# Muhurta finder: ranks daytime slots by intersecting what the engines
# already compute — good choghadiya blocks minus every inauspicious
# window, with bonuses for Abhijit/Amrita overlap and the day's special
# yogas, light activity rules, and per-person tarabalam + chandrabalam
# group fit. Deterministic and explainable: each slot carries its reasons.
#
# Scoring is universal — the same astrological judgement regardless of
# what 'chandra_mode' the caller selects. `chandra_mode` controls only
# which days appear in the returned list; it does not change scores.
from datetime import datetime, timedelta

from telugu_panchangam.models.panchangam_day import PanchangamDay
from telugu_panchangam.personal.tarabalam import (
    AUSPICIOUS_TARAS, tara_number, tara_name,
)
from telugu_panchangam.personal.chandrabalam import (
    CHANDRA_GOOD, CHANDRA_PUJA, chandra_position,
)

GOOD_CHOGHADIYA = {'Amrit': 3, 'Shubh': 2, 'Labh': 2, 'Char': 1}
MIN_SLOT_MINUTES = 24  # one ghati

ACTIVITIES = ('any', 'travel', 'purchase', 'ceremony', 'beginning')
CHANDRA_MODES = ('stars', 'puja_ok', 'strict')

_YOGA_BONUS = {'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
               'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1}
_YOGA_PENALTY = {'Visha Yoga': -2, 'Dagdha Yoga': -2}


def _subtract(start: datetime, end: datetime, blocks: list[tuple[datetime, datetime]]):
    """Pieces of [start, end) not covered by any block."""
    pieces = [(start, end)]
    for b0, b1 in blocks:
        nxt = []
        for p0, p1 in pieces:
            if b1 <= p0 or b0 >= p1:
                nxt.append((p0, p1))
                continue
            if p0 < b0:
                nxt.append((p0, b0))
            if b1 < p1:
                nxt.append((b1, p1))
        pieces = nxt
    return pieces


def _overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


def _label(janma: str, idx: int) -> str:
    """Person label for reasons — uses '#N' when names aren't supplied."""
    return f'#{idx + 1} ({janma})'


def day_slots(day: PanchangamDay, activity: str = 'any',
              janma_nakshatras: list[str] | None = None,
              janma_rasis: list[str | None] | None = None,
              chandra_mode: str = 'stars') -> list[dict]:
    """Ranked auspicious slots for one day (daytime, sunrise to sunset).

    Scoring (always applied, regardless of chandra_mode):
      - Tarabalam: per person, +1 if tara in {2,4,6,8,9}; -1 otherwise.
        Reasons name each person; net contribution is the sum.
      - Chandrabalam (when rashis given): per person, +1 for {1,3,6,7,10,11},
        0 for {2,5,9} (annotation only), -1 for {4,8,12}.
      - Yoga: Sarvartha Siddhi / Amrita Siddhi +2, Dvi/Tripushkara +1,
        Visha / Dagdha -2 (ceremony skips Visha/Dagdha days outright).
      - Choghadiya base 1-3, Abhijit/Amrita Kalam overlap +2 each,
        activity bias +1 (purchase favours Labh, beginning favours Amrit).

    Day-level hard skips (return []):
      - Eclipse day (engine-provided): auspicious activities deferred.
      - Ceremony activity on Visha/Dagdha day.

    Mode filtering (only affects which days are in the output):
      - 'stars': no chandrabalam filter.
      - 'puja_ok': day omitted if any person hits {4,8,12}.
      - 'strict': day omitted unless every person is in {1,3,6,7,10,11}.
    """
    if activity not in ACTIVITIES:
        raise ValueError(f'activity must be one of {ACTIVITIES}')
    if chandra_mode not in CHANDRA_MODES:
        raise ValueError(f'chandra_mode must be one of {CHANDRA_MODES}')
    if janma_rasis is not None and janma_nakshatras is not None:
        if len(janma_rasis) != len(janma_nakshatras):
            raise ValueError('janma_rasis must align with janma_nakshatras '
                             '(use None for people whose rashi is unknown).')

    # Eclipse: auspicious activities are deferred outright.
    if day.eclipse is not None:
        return []

    day_bonus = 0
    day_reasons: list[str] = []

    # Tarabalam — per-person additive (graded). +1 favourable, -1 otherwise.
    if janma_nakshatras:
        fav_names, unfav_names = [], []
        for i, janma in enumerate(janma_nakshatras):
            t = tara_number(janma, day.nakshatra.name)
            label = _label(janma, i)
            if t in AUSPICIOUS_TARAS:
                fav_names.append(label)
                day_bonus += 1
            else:
                unfav_names.append(f'{label} {tara_name(t)}')
                day_bonus -= 1
        if fav_names:
            day_reasons.append(f"tarabalam favourable for {', '.join(fav_names)} (+{len(fav_names)})")
        if unfav_names:
            day_reasons.append(f"tarabalam avoid for {', '.join(unfav_names)} (-{len(unfav_names)})")

    # Chandrabalam — per-person additive (graded), only when rashis are given.
    if janma_rasis is not None and any(r is not None for r in janma_rasis):
        good_names, puja_names, avoid_names = [], [], []
        for i, rasi in enumerate(janma_rasis):
            if rasi is None:
                continue
            janma_label = janma_nakshatras[i] if janma_nakshatras else rasi
            label = _label(janma_label, i)
            pos = chandra_position(rasi, day.lunar_sign)
            if pos in CHANDRA_GOOD:
                good_names.append(label)
                day_bonus += 1
            elif pos in CHANDRA_PUJA:
                puja_names.append(f'{label} Moon@{pos}')
            else:  # in {4, 8, 12}
                ashtama = ' Ashtama' if pos == 8 else ''
                avoid_names.append(f'{label}{ashtama} Moon@{pos}')
                day_bonus -= 1
        if good_names:
            day_reasons.append(f"chandrabalam favourable for {', '.join(good_names)} (+{len(good_names)})")
        if puja_names:
            day_reasons.append(f"chandrabalam remedial for {', '.join(puja_names)} (puja recommended)")
        if avoid_names:
            day_reasons.append(f"chandrabalam avoid for {', '.join(avoid_names)} (-{len(avoid_names)})")

        # Mode filtering — applied AFTER scoring is fixed, so it only changes
        # which days appear in the result, never the scores themselves.
        if chandra_mode == 'strict' and (puja_names or avoid_names):
            return []
        if chandra_mode == 'puja_ok' and avoid_names:
            return []

    for y in day.special_yogas:
        if y in _YOGA_BONUS:
            day_bonus += _YOGA_BONUS[y]
            day_reasons.append(f'{y} day (+{_YOGA_BONUS[y]})')
        if y in _YOGA_PENALTY:
            if activity == 'ceremony':
                return []  # ceremonies avoid Visha/Dagdha days outright
            day_bonus += _YOGA_PENALTY[y]
            day_reasons.append(f'{y} day ({_YOGA_PENALTY[y]})')

    bad = [(w.start, w.end) for w in
           [day.rahu_kalam, day.gulika_kalam, day.yamagandam]
           + list(day.varjyam) + list(day.durmuhurtham)]

    if activity == 'travel':
        bad += [(k.start, k.end) for k in day.karana if k.name == 'Vishti']

    abhijit = day.abhijit_muhurta
    amrita = list(day.amrita_kalam)

    slots = []
    for block in day.choghadiya:
        base = GOOD_CHOGHADIYA.get(block.name)
        if base is None:
            continue
        for s, e in _subtract(block.start, block.end, bad):
            if (e - s) < timedelta(minutes=MIN_SLOT_MINUTES):
                continue
            score = base + day_bonus
            reasons = [f'{block.name} choghadiya (+{base})', 'clear of all inauspicious windows'] + day_reasons
            if abhijit and _overlaps(s, e, abhijit.start, abhijit.end):
                score += 2
                reasons.append('overlaps Abhijit Muhurta (+2)')
            if any(_overlaps(s, e, a.start, a.end) for a in amrita):
                score += 2
                reasons.append('overlaps Amrita Kalam (+2)')
            if activity == 'purchase' and block.name == 'Labh':
                score += 1
                reasons.append('Labh favoured for purchases (+1)')
            if activity == 'beginning' and block.name == 'Amrit':
                score += 1
                reasons.append('Amrit favoured for beginnings (+1)')
            if activity == 'travel':
                reasons.append('Vishti karana avoided')
            slots.append({'date': day.date.isoformat(), 'vaaram': day.vaaram,
                          'start': s, 'end': e, 'score': score, 'reasons': reasons})
    slots.sort(key=lambda x: (-x['score'], x['start']))
    return slots
