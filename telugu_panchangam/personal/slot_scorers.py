# Atomic scoring components for the muhurta finder.
#
# Each function measures one signal and returns a (bonus, reasons, ...)
# tuple — never mutates state, never makes final decisions. The
# orchestrator in muhurta.py combines them into a ranked slot list.
#
# Also defines _DayContext: the day-constant inputs bundled so that
# _evaluate_slot() takes (s, e, block, base, facts, ctx) instead of 20+
# positional arguments.
from __future__ import annotations

from dataclasses import dataclass

from telugu_panchangam.personal.lagna_position import (
    lagna_position, lagna_verdict, is_favourable_lagna, is_ashtama_lagna,
    lagnas_in_class,
)
from telugu_panchangam.personal.tarabalam import (
    AUSPICIOUS_TARAS, tara_number, tara_name,
)
from telugu_panchangam.personal.chandrabalam import (
    CHANDRA_GOOD, CHANDRA_PUJA, chandra_position,
)
from telugu_panchangam.personal.tithi_class import tithi_family
from telugu_panchangam.personal.nitya_yoga import (
    NITYA_HARD_AVOID, NITYA_HARD_PENALTY,
    NITYA_PARTIAL_DOSHA_WINDOW, NITYA_PARTIAL_PENALTY,
    NITYA_AUSPICIOUS, NITYA_AUSPICIOUS_BONUS,
)
from telugu_panchangam.special_yogas import ANANDADI_AUSPICIOUS, ANANDADI_INAUSPICIOUS

_YOGA_BONUS = {'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
               'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1,
               'Siddha Yoga': 1}
_YOGA_PENALTY = {'Visha Yoga': -2, 'Dagdha Yoga': -2}


# ---------------------------------------------------------------------------
# Day-constant context — built once per day_slots() call, passed to every
# _evaluate_slot() invocation so the function signature stays manageable.
# ---------------------------------------------------------------------------

@dataclass
class _DayContext:
    day: object                             # PanchangamDay (avoid circular import)
    skip_yogas: frozenset
    janma_nakshatras: list[str] | None
    janma_rasis: list[str | None] | None
    janma_lagnas: list[str | None] | None
    chandra_mode: str
    prefer_tithi_class: str | None
    avoid_tithi_class: list
    label: str
    vara_bonus: int
    vara_reason: str | None
    abhijit: object | None                  # Window | None
    amrita: list                            # list[Window]
    prefer_chog: tuple | None               # ('BlockName', bonus) | None
    avoid_karana_names: frozenset
    horas: list | None
    prefer_varas: frozenset
    lagnas: list | None
    prefer_lagna_class: str | None
    required_lagna_class: str | None
    prefer_bhadra_puchha: int
    simha_stha_shukra_penalty: int
    prefer_nakshatra_mukha: tuple | None    # ([classes], bonus) | None
    allowed_nakshatras: frozenset
    avoid_nakshatras: frozenset
    prefer_nakshatras: frozenset
    allowed_tithi_numbers: frozenset
    prefer_tithi_numbers: frozenset
    allowed_tithi_names: frozenset
    avoid_tithi_numbers: frozenset
    allowed_lagnas: frozenset
    prefer_lagnas: frozenset
    caution_lagna_solar: bool
    manual_checks: tuple[str, ...]
    manual_prerequisites: bool


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _label(janma: str, idx: int) -> str:
    return f'#{idx + 1} ({janma})'


# ---------------------------------------------------------------------------
# Personal-fit scorers  (tara, chandra, lagna)
# ---------------------------------------------------------------------------

def score_tara(janma_nakshatras, day_nakshatra_name):
    """Per-person tarabalam against a specific nakshatra.

    Returns (bonus, reasons, unfav_names).
    unfav_names feeds doctrinal_notes to surface Sarvartha-rectification.
    """
    if not janma_nakshatras:
        return 0, [], []
    bonus, fav, unfav, unfav_names = 0, [], [], []
    for i, janma in enumerate(janma_nakshatras):
        t = tara_number(janma, day_nakshatra_name)
        label = _label(janma, i)
        if t in AUSPICIOUS_TARAS:
            fav.append(label); bonus += 1
        else:
            unfav.append(f'{label} {tara_name(t)}')
            unfav_names.append(label)
            bonus -= 1
    reasons = []
    if fav:
        reasons.append(f"tarabalam favourable for {', '.join(fav)} (+{len(fav)})")
    if unfav:
        reasons.append(f"tarabalam avoid for {', '.join(unfav)} (-{len(unfav)})")
    return bonus, reasons, unfav_names


def score_chandra(janma_nakshatras, janma_rasis, lunar_sign, chandra_mode):
    """Per-person chandrabalam against a specific moon rashi.

    Returns (bonus, reasons, dropped, avoid_names, puja_names).
    avoid_names feeds doctrinal_notes; puja_names feeds personal_dosha flag.
    """
    if janma_rasis is None or not any(r is not None for r in janma_rasis):
        return 0, [], False, [], []
    bonus = 0
    good, puja, avoid, avoid_names, puja_names = [], [], [], [], []
    for i, rasi in enumerate(janma_rasis):
        if rasi is None:
            continue
        janma_label = janma_nakshatras[i] if janma_nakshatras else rasi
        label = _label(janma_label, i)
        pos = chandra_position(rasi, lunar_sign)
        if pos in CHANDRA_GOOD:
            good.append(label); bonus += 1
        elif pos in CHANDRA_PUJA:
            puja.append(f'{label} Moon@{pos}')
            puja_names.append(label)
        else:
            ashtama = ' Ashtama' if pos == 8 else ''
            avoid.append(f'{label}{ashtama} Moon@{pos}')
            avoid_names.append(f'{label}{ashtama}')
            bonus -= 1
    reasons = []
    if good:
        reasons.append(f"chandrabalam favourable for {', '.join(good)} (+{len(good)})")
    if puja:
        reasons.append(f"chandrabalam remedial for {', '.join(puja)} (puja recommended)")
    if avoid:
        reasons.append(f"chandrabalam avoid for {', '.join(avoid)} (-{len(avoid)})")
    dropped = (chandra_mode == 'strict' and (puja or avoid)) \
              or (chandra_mode == 'puja_ok' and avoid)
    return bonus, reasons, bool(dropped), avoid_names, puja_names


def slot_lagna_name(lagnas, slot_start):
    """Rising sign name at slot_start; None if lagnas list is empty."""
    if not lagnas:
        return None
    for w in lagnas:
        if w.start <= slot_start < w.end:
            return w.name.replace(' Lagna', '')
    return None


def score_lagna_activity(prefer_lagna_class, slot_lagna, activity_label):
    """Activity-class lagna preference (Muhurta Chintamani).

    Returns (bonus, reason_text | None).
    Independent of the personal kendra/trikona check.
    """
    if not prefer_lagna_class or not slot_lagna:
        return 0, None
    favoured = lagnas_in_class(prefer_lagna_class)
    if slot_lagna in favoured:
        return 1, (f'{slot_lagna} lagna ({prefer_lagna_class}) '
                   f'favoured for {activity_label} (+1)')
    return 0, None


def score_lagna(janma_nakshatras, janma_rasis, slot_lagna, janma_lagnas=None):
    """Per-person lagna position against the slot's rising sign.

    Checks kendra/trikona (favourable) and Ashtama (personal dosha)
    from both janma rashi and janma lagna when supplied.

    Returns (bonus, reasons, ashtama_names).
    """
    if not janma_rasis or not slot_lagna:
        return 0, [], []
    bonus = 0
    fav_rashi, ash_rashi, neut_rashi = [], [], []
    fav_lagna, ash_lagna, neut_lagna = [], [], []
    ashtama_names: list[str] = []

    def _record_ashtama(label):
        if label not in ashtama_names:
            ashtama_names.append(label)

    _ord_suffix = {1: 'st', 2: 'nd', 3: 'rd'}
    def _ord(n):
        return f'{n}{_ord_suffix.get(n, "th")}'

    for i, rasi in enumerate(janma_rasis):
        if rasi is None:
            continue
        janma_label = janma_nakshatras[i] if janma_nakshatras else rasi
        label = _label(janma_label, i)
        has_lagna = bool(janma_lagnas and i < len(janma_lagnas)
                         and janma_lagnas[i])
        pos_r = lagna_position(rasi, slot_lagna)
        if is_ashtama_lagna(pos_r):
            ash_rashi.append(f'{label} lagna@{pos_r} from {rasi}')
            _record_ashtama(label)
            bonus -= 1
        elif is_favourable_lagna(pos_r):
            fav_rashi.append(
                f'{label} {lagna_verdict(pos_r)}@{pos_r} from {rasi}'
            )
            bonus += 1
        elif has_lagna:
            neut_rashi.append(f'{label} {_ord(pos_r)} from {rasi}')
        if has_lagna:
            jl = janma_lagnas[i]
            pos_l = lagna_position(jl, slot_lagna)
            if is_ashtama_lagna(pos_l):
                ash_lagna.append(f'{label} lagna@{pos_l} from {jl} lagna')
                _record_ashtama(label)
                bonus -= 1
            elif is_favourable_lagna(pos_l):
                fav_lagna.append(
                    f'{label} {lagna_verdict(pos_l)}@{pos_l} from {jl} lagna'
                )
                bonus += 1
            else:
                neut_lagna.append(f'{label} {_ord(pos_l)} from {jl} lagna')

    reasons = []
    if fav_rashi:
        reasons.append(
            f"{slot_lagna} lagna favourable for {', '.join(fav_rashi)} "
            f"(+{len(fav_rashi)})"
        )
    if fav_lagna:
        reasons.append(
            f"{slot_lagna} lagna favourable for {', '.join(fav_lagna)} "
            f"(+{len(fav_lagna)})"
        )
    if ash_rashi:
        reasons.append(
            f"{slot_lagna} lagna Ashtama for {', '.join(ash_rashi)} "
            f"(-{len(ash_rashi)})"
        )
    if ash_lagna:
        reasons.append(
            f"{slot_lagna} lagna Ashtama for {', '.join(ash_lagna)} "
            f"(-{len(ash_lagna)})"
        )
    if neut_rashi:
        reasons.append(
            f"{slot_lagna} lagna neutral for {', '.join(neut_rashi)} "
            f"(no effect)"
        )
    if neut_lagna:
        reasons.append(
            f"{slot_lagna} lagna neutral for {', '.join(neut_lagna)} "
            f"(no effect)"
        )
    return bonus, reasons, ashtama_names


# ---------------------------------------------------------------------------
# Calendar-quality scorers  (tithi, yoga, nitya yoga, anandadi)
# ---------------------------------------------------------------------------

def score_tithi_class(tithi_name, prefer_tithi_class, activity_label,
                      nakshatra=None, special_yogas=(), avoid_tithi_class=()):
    """Tithi-family scoring: Rikta -2; activity-preferred +1; activity-avoided -1.

    Classical neutralization (Muhurta Chintamani / B.V. Raman Muhurtha):
      - Pushya nakshatra: cancels Rikta dosha entirely (0 instead of -2).
      - Sarvartha/Amrita Siddhi Yoga: partially offsets Rikta (-1 instead of -2).
    Both conditions surface a reason note so the user sees why the penalty
    is reduced. When both apply, Pushya takes precedence (full cancellation).

    Returns (bonus, day_reason, activity_reason, family).
    """
    try:
        fam = tithi_family(tithi_name)
    except ValueError:
        return 0, None, None, None

    if fam == 'Rikta':
        if nakshatra == 'Pushya':
            return 0, (f'{tithi_name} (Rikta tithi) neutralised by Pushya '
                       f'nakshatra (0)'), None, fam
        siddhi = [y for y in special_yogas
                  if y in ('Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga')]
        if siddhi:
            label = ' + '.join(siddhi)
            return -1, (f'{tithi_name} (Rikta tithi) partially offset by '
                        f'{label} (-1)'), None, fam
        return -2, f'{tithi_name} (Rikta tithi) (-2)', None, fam

    if 'Amavasya' in tithi_name:
        return -2, f'{tithi_name} (-2)', None, 'Amavasya'
    if prefer_tithi_class and fam == prefer_tithi_class:
        return 1, None, (f'{tithi_name} ({prefer_tithi_class} tithi) '
                         f'favoured for {activity_label} (+1)'), fam
    if fam in avoid_tithi_class:
        return -1, None, (f'{tithi_name} ({fam} tithi) '
                          f'inauspicious for {activity_label} (-1)'), fam
    return 0, None, None, fam


def doctrinal_notes(*, special_yogas, tara_unfav_names, chandra_avoid_names,
                    tithi_fam):
    """Explanatory notes from classical doctrine — do not change the score.

    Surfaces relationships the numeric reasons can't communicate on their own.
    Sources: Muhurta Chintamani, Muhurta Martanda, TTD Panchanga Nirnayam.
    """
    notes: list[str] = []
    siddhi_yogas = [y for y in special_yogas
                    if y in ('Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga')]
    has_pushkara = any(y in ('Dvipushkara Yoga', 'Tripushkara Yoga')
                       for y in special_yogas)

    if siddhi_yogas and tara_unfav_names:
        siddhi_label = ' + '.join(siddhi_yogas)
        names = ', '.join(tara_unfav_names)
        notes.append(
            f'{siddhi_label} traditionally rectifies tara dosha '
            f'(Muhurta Chintamani) · {names} mitigated.'
        )
    if siddhi_yogas and chandra_avoid_names:
        names = ', '.join(chandra_avoid_names)
        notes.append(
            'Chandra dosha is not rectified by Siddhi yogas · '
            f'{names} remains a personal caution.'
        )
    if has_pushkara and tithi_fam == 'Rikta':
        notes.append(
            "Pushkara amplifies the day's nature; combined with Rikta "
            'tithi, even small inauspicious factors magnify.'
        )
    return notes


def score_special_yogas(special_yogas, skip_yogas):
    """Yoga bonuses/penalties. Returns (bonus, reasons, defer_due_to_yoga)."""
    bonus, reasons = 0, []
    for y in special_yogas:
        if y in _YOGA_BONUS:
            bonus += _YOGA_BONUS[y]
            reasons.append(f'{y} day (+{_YOGA_BONUS[y]})')
        if y in _YOGA_PENALTY:
            if y in skip_yogas:
                return 0, [], True
            bonus += _YOGA_PENALTY[y]
            reasons.append(f'{y} day ({_YOGA_PENALTY[y]})')
    return bonus, reasons, False


def score_nitya_yoga(yoga_name, slot_start, day, skip_on_hard_avoid):
    """Score the slot's Nitya yoga (the 27 sun-moon longitudinal yogas).

    Returns (bonus, reasons, defer_on_hard_avoid).
    """
    if yoga_name in NITYA_HARD_AVOID:
        if skip_on_hard_avoid:
            return 0, [], True
        return NITYA_HARD_PENALTY, [f'{yoga_name} yoga ({NITYA_HARD_PENALTY})'], False
    if yoga_name in NITYA_PARTIAL_DOSHA_WINDOW:
        window = NITYA_PARTIAL_DOSHA_WINDOW[yoga_name]
        if day.yoga.name == yoga_name:
            yoga_start = day.yoga.start
        else:
            yoga_start = day.yoga.end
        if slot_start - yoga_start <= window:
            return NITYA_PARTIAL_PENALTY, \
                [f'{yoga_name} yoga dosha-window ({NITYA_PARTIAL_PENALTY})'], False
        return 0, [], False
    if yoga_name in NITYA_AUSPICIOUS:
        return NITYA_AUSPICIOUS_BONUS, \
               [f'{yoga_name} yoga (+{NITYA_AUSPICIOUS_BONUS})'], False
    return 0, [], False


def anandadi_day_modifier(day) -> tuple[int, str | None]:
    """Return (score_delta, reason_chip) for the day's Anandadi yoga."""
    yoga = getattr(day, 'anandadi_yoga', None)
    if yoga is None:
        return 0, None
    if yoga in ANANDADI_AUSPICIOUS:
        return 1, f'Anandadi: {yoga} (+1)'
    if yoga in ANANDADI_INAUSPICIOUS:
        return -1, f'Anandadi: {yoga} (-1)'
    return 0, None


# Re-export so muhurta.py can reach the yoga penalty table for day_dosha check.
YOGA_PENALTY = _YOGA_PENALTY
