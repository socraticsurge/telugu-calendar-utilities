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

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.engines.base import VAARAM_NAMES
from telugu_panchangam.personal.lagna_hora import get_horas
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

GOOD_CHOGHADIYA = {'Amrit': 3, 'Shubh': 2, 'Labh': 2, 'Char': 1}
MIN_SLOT_MINUTES = 24  # one ghati

CHANDRA_MODES = ('stars', 'puja_ok', 'strict')

# Tier thresholds — score → human-anchor label.
# Tuned for typical Drik scoring with a 1-4 person family:
#   ≥ +7: Excellent — rare alignment, multiple positive signals
#   +4..+6: Good — solid recommendation
#   +1..+3: Fair — workable, often with compromises (notes explain)
#   ≤ 0: Avoid — significant negatives outweigh the slot
TIER_NAMES = ('Avoid', 'Fair', 'Good', 'Excellent')


def score_tier(score: int) -> str:
    """Map raw slot score to a tier label using fixed absolute bands."""
    if score >= 7:
        return 'Excellent'
    if score >= 4:
        return 'Good'
    if score >= 1:
        return 'Fair'
    return 'Avoid'


# Relative tier buckets — fraction of the way from this batch's lowest
# to its highest score. score_tier()'s fixed bands assume a 1-person,
# no-Abhijit, no-Amrita baseline and a slot that could plausibly stack
# every bonus at once — neither holds across group sizes or activities.
# Bucketing by position within the scores actually found keeps
# "Excellent" meaning "the best of what turned up for this search".
_RELATIVE_BANDS = (0.75, 0.5, 0.25)


def relative_tier(score: int, ceiling: int, floor: int) -> str:
    """Map raw score to a tier relative to a [floor, ceiling] range."""
    spread = ceiling - floor
    if spread <= 0:
        return score_tier(score)
    rel = (score - floor) / spread
    if rel >= _RELATIVE_BANDS[0]:
        return 'Excellent'
    if rel >= _RELATIVE_BANDS[1]:
        return 'Good'
    if rel >= _RELATIVE_BANDS[2]:
        return 'Fair'
    return 'Avoid'


def assign_tiers(slots: list[dict]) -> None:
    """Tier each slot relative to the min/max score within this batch.

    Mutates each slot's 'tier' in place. The personal chandra-dosha cap
    (Excellent -> Good) is re-applied here so it holds regardless of
    which batch — a single day's slots or a whole search's — supplied
    the ceiling/floor.
    """
    if not slots:
        return
    scores = [s['score'] for s in slots]
    ceiling, floor = max(scores), min(scores)
    for s in slots:
        tier = relative_tier(s['score'], ceiling, floor)
        if tier == 'Excellent' and (s['personal_dosha'] is not None
                                     or s['day_dosha'] is not None):
            tier = 'Good'
        s['tier'] = tier

_YOGA_BONUS = {'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
               'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1}
_YOGA_PENALTY = {'Visha Yoga': -2, 'Dagdha Yoga': -2}

_SAMSKARA_SKIP = ('Visha Yoga', 'Dagdha Yoga')

# Activity rules — declarative, one row per activity. Fields:
#   label              human-readable name (used in MCP errors, UI dropdown)
#   skip_on_yoga       day is omitted if any of these yogas are active
#                      (classical samskaras avoid Visha / Dagdha days)
#   prefer_choghadiya  (block_name, bonus) — adds bonus when slot's block matches
#   avoid_karana       slot pieces overlapping these karana windows are cut
#   (Batch B will add: prefer_tithi_class, prefer_vara)
ACTIVITY_RULES: dict[str, dict] = {
    # — Generic (existing — backward-compatible MCP keys) —
    'any':           {'label': 'Anything auspicious'},
    'travel':        {'label': 'Travel / journey',
                      'avoid_karana': ['Vishti']},
    'purchase':      {'label': 'Purchase (general)',
                      'prefer_choghadiya': ('Labh', 1)},
    'ceremony':      {'label': 'Ceremony / puja (general)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_vara': ['Somavaram', 'Guruvaram']},
    'beginning':     {'label': 'New beginning (general)',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram', 'Guruvaram']},
    # — Samskaras —
    'wedding':       {'label': 'Wedding (Vivaha)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Purna',
                      'prefer_vara': ['Guruvaram', 'Somavaram']},
    'engagement':    {'label': 'Engagement (Nischayam)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Purna',
                      'prefer_vara': ['Guruvaram', 'Somavaram']},
    'naming':        {'label': 'Naming (Namakaranam)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_choghadiya': ('Shubh', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram', 'Guruvaram']},
    'annaprasana':   {'label': 'Annaprasana (First feeding)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_choghadiya': ('Shubh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Somavaram', 'Guruvaram']},
    'karnavedha':    {'label': 'Karnavedha (Ear-piercing)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Budhavaram', 'Shukravaram']},
    'mundana':       {'label': 'Mundana / Chaula (First head-shave)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram', 'Guruvaram']},
    'upanayana':     {'label': 'Upanayana (Sacred thread)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram', 'Guruvaram']},
    'vidyarambha':   {'label': 'Education start (Vidyarambha)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Budhavaram']},
    'gruhapravesha': {'label': 'Gruhapravesha (Home entry)',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Guruvaram', 'Somavaram']},
    # — Acquisitions —
    'vehicle':       {'label': 'Vehicle purchase',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Shukravaram']},
    'property':      {'label': 'Property / Land purchase',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Guruvaram', 'Shukravaram']},
    'gold':          {'label': 'Gold / Jewelry purchase',
                      'prefer_choghadiya': ('Labh', 1),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Shukravaram', 'Guruvaram']},
    # — Construction & Ventures —
    'bhumi_puja':    {'label': 'Bhumi Puja / Foundation laying',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Bhadra',
                      'prefer_vara': ['Guruvaram', 'Somavaram']},
    'business':      {'label': 'Business launch',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Guruvaram', 'Budhavaram']},
    'job':           {'label': 'Job start / Contract signing',
                      'prefer_choghadiya': ('Amrit', 1),
                      'prefer_tithi_class': 'Nanda',
                      'prefer_vara': ['Guruvaram', 'Budhavaram']},
    # — Spiritual —
    'yajna':         {'label': 'Yajna / Homam',
                      'skip_on_yoga': list(_SAMSKARA_SKIP),
                      'prefer_tithi_class': 'Purna',
                      'prefer_vara': ['Guruvaram', 'Somavaram']},
    'pilgrimage':    {'label': 'Pilgrimage (Tirtha Yatra)',
                      'avoid_karana': ['Vishti']},
    # — Civil & Medical —
    'court':         {'label': 'Court / legal matter',
                      'prefer_tithi_class': 'Jaya',
                      'prefer_vara': ['Mangalavaram']},
    'surgery':       {'label': 'Surgery / medical procedure',
                      'avoid_karana': ['Vishti'],
                      'prefer_vara': ['Mangalavaram']},
}

ACTIVITIES = tuple(ACTIVITY_RULES.keys())


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


def _score_tara(janma_nakshatras, day_nakshatra_name):
    """Per-person tarabalam contribution against a specific nakshatra.

    Returns (bonus, reasons, unfav_names). The unfav_names list (people
    whose tara is in Janma/Vipat/Pratyak/Naidhana) is used by the
    doctrinal-notes engine to surface Sarvartha-rectification messages.
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


def _score_chandra(janma_nakshatras, janma_rasis, lunar_sign, chandra_mode):
    """Per-person chandrabalam against a specific moon rashi.

    Returns (bonus, reasons, dropped_by_mode, avoid_names, puja_names).
    avoid_names lists people whose Moon is at 4/8/12 (used by
    doctrinal-notes engine to surface the 'chandra dosha is not
    rectified' caution). puja_names lists people whose Moon is in a
    remedial (puja) position — both lists feed the personal-dosha flag
    that caps a slot's tier (chandra dosha is never fully rectified by
    group-level yogas).
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


def _score_tithi_class(tithi_name, prefer_tithi_class, activity_label):
    """Universal Rikta -2; activity-preferred class +1.

    Returns (bonus, day_reason, activity_reason, family). The Rikta
    penalty is a day-quality concern; the class-match is activity-match.
    """
    try:
        fam = tithi_family(tithi_name)
    except ValueError:
        return 0, None, None, None
    if fam == 'Rikta':
        return -2, f'{tithi_name} (Rikta tithi) (-2)', None, fam
    if prefer_tithi_class and fam == prefer_tithi_class:
        return 1, None, f'{tithi_name} ({prefer_tithi_class}) favoured for {activity_label} (+1)', fam
    return 0, None, None, fam


def _doctrinal_notes(*, special_yogas, tara_unfav_names, chandra_avoid_names,
                     tithi_fam):
    """Generate classical-doctrine notes from the day's flags.

    These are explanatory only — they do NOT change the score. They surface
    the *relationships* the score's reasons can't communicate on their own:
    e.g. why a Sarvartha day still ranks high despite one person's tara
    dosha (the yoga rectifies it), and why Sarvartha doesn't help with
    Ashtama Chandra (chandra dosha isn't rectifiable by group-level yogas).

    Sources: Muhurta Chintamani, Muhurta Martanda; modern panchangam
    commentaries (Drik Panchang, TTD Panchanga Nirnayam).
    """
    notes: list[str] = []
    siddhi_yogas = [y for y in special_yogas
                    if y in ('Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga')]
    has_pushkara = any(y in ('Dvipushkara Yoga', 'Tripushkara Yoga')
                       for y in special_yogas)

    # 1. Sarvartha/Amrita Siddhi rectifies tara dosha
    if siddhi_yogas and tara_unfav_names:
        siddhi_label = ' + '.join(siddhi_yogas)
        names = ', '.join(tara_unfav_names)
        notes.append(
            f'{siddhi_label} traditionally rectifies tara dosha '
            f'(Muhurta Chintamani) — {names} mitigated.'
        )

    # 2. Chandra dosha is NOT rectified by Siddhi yogas
    if siddhi_yogas and chandra_avoid_names:
        names = ', '.join(chandra_avoid_names)
        notes.append(
            'Chandra dosha is not rectified by Siddhi yogas — '
            f'{names} remains a personal caution.'
        )

    # 3. Pushkara amplifier + Rikta tithi caveat
    if has_pushkara and tithi_fam == 'Rikta':
        notes.append(
            'Pushkara amplifies the day\'s nature; combined with Rikta '
            'tithi, even small inauspicious factors magnify.'
        )

    return notes


def _score_special_yogas(special_yogas, skip_yogas):
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


def _score_nitya_yoga(yoga_name, slot_start, day, skip_on_hard_avoid):
    """Score the slot's Nitya yoga (the 27 sun-moon longitudinal yogas).

    Returns (bonus, reasons, defer_on_hard_avoid).

    - Hard-avoid (Vyatipata, Vaidhriti): -2 day_bonus + reason. Also
      defers the slot when `skip_on_hard_avoid` is True (samskaras).
    - Partial-avoid (Vishkambha/Atiganda/Shoola/Ganda/Vyaghata/Parigha):
      -1 only if the slot is inside the yoga's dosha-window measured
      from when the yoga began. We use `day.yoga.start` when the slot's
      yoga matches the sunrise yoga; otherwise we treat `day.yoga.end`
      as the start of the new yoga (a 1-transition heuristic that
      covers the common case).
    - Auspicious yogas (Siddhi, Shubha, Brahma, etc): +1.
    - Neutral yogas: 0.
    """
    if yoga_name in NITYA_HARD_AVOID:
        if skip_on_hard_avoid:
            return 0, [], True
        return NITYA_HARD_PENALTY, [f'{yoga_name} yoga ({NITYA_HARD_PENALTY})'], False
    if yoga_name in NITYA_PARTIAL_DOSHA_WINDOW:
        window = NITYA_PARTIAL_DOSHA_WINDOW[yoga_name]
        # Best-effort yoga-start: sunrise yoga if it matches, else the
        # boundary at day.yoga.end (where the next yoga began).
        if day.yoga.name == yoga_name:
            yoga_start = day.yoga.start
        else:
            yoga_start = day.yoga.end
        if slot_start - yoga_start <= window:
            return NITYA_PARTIAL_PENALTY, \
                [f'{yoga_name} yoga dosha-window ({NITYA_PARTIAL_PENALTY})'], False
        # Outside the dosha-window — neutral
        return 0, [], False
    if yoga_name in NITYA_AUSPICIOUS:
        return NITYA_AUSPICIOUS_BONUS, \
               [f'{yoga_name} yoga (+{NITYA_AUSPICIOUS_BONUS})'], False
    return 0, [], False


def diagnose_day(day, activity='any', janma_nakshatras=None,
                 janma_rasis=None, chandra_mode='stars'):
    """If day_slots() would return [] for these inputs, explain why.

    Returns a string (the reason) or None when the day is not filtered.
    Used by MCP find_muhurta to populate dropped_days[] so devotees see
    why days were excluded from the result set.

    This is a lightweight pre-check — it does NOT run the full scoring
    loop. It catches the day-level skip conditions:
      - Eclipse
      - Activity-skip yoga (samskara on Visha/Dagdha/Vyatipata/Vaidhriti)
      - chandra_mode strict/puja_ok filtering out the day's sunrise rashi
    """
    if day.eclipse is not None:
        kind = f'{day.eclipse.kind} eclipse'
        return f'{kind} — auspicious activities deferred'

    rules = ACTIVITY_RULES.get(activity, ACTIVITY_RULES['any'])
    skip_yogas = set(rules.get('skip_on_yoga', ()))
    if skip_yogas:
        for y in day.special_yogas:
            if y in skip_yogas:
                return f'{y} — {rules["label"]} traditionally avoids this day'
        # Vyatipata/Vaidhriti also defer samskaras even though they're
        # Nitya yogas not in skip_on_yoga
        if day.yoga.name in NITYA_HARD_AVOID:
            return f'{day.yoga.name} yoga — samskaras traditionally defer'

    # chandra_mode day-level filter (matches the sunrise rashi snapshot;
    # for slot-time precision, individual slots may still pass, but if
    # the sunrise reading already fails, the whole day usually fails)
    if janma_rasis is not None and chandra_mode != 'stars':
        has_avoid = False
        has_remedial = False
        for r in janma_rasis:
            if r is None:
                continue
            pos = chandra_position(r, day.lunar_sign)
            if pos not in CHANDRA_GOOD and pos not in CHANDRA_PUJA:
                has_avoid = True
            elif pos in CHANDRA_PUJA:
                has_remedial = True
        if chandra_mode == 'strict' and (has_avoid or has_remedial):
            return f'chandra_mode=strict — Moon at sunrise fails for at least one person'
        if chandra_mode == 'puja_ok' and has_avoid:
            return f'chandra_mode=puja_ok — someone has Moon-avoid (4/8/12)'

    return None


def _day_snapshot_facts(day):
    """Fallback when no engine is provided — wrap the day's sunrise spans
    as a SlotFacts so the per-slot scoring path can use the same code."""
    from telugu_panchangam.models.panchangam_day import SlotFacts
    return SlotFacts(
        nakshatra=day.nakshatra.name,
        tithi=day.tithi.name,
        yoga=day.yoga.name,
        karana=day.karana[0].name if day.karana else '',
        lunar_sign=day.lunar_sign,
        vaaram=day.vaaram,
        special_yogas=list(day.special_yogas),
    )



def _get_bad_windows(day, avoid_karana_names):
    bad = [(w.start, w.end) for w in
           [day.rahu_kalam, day.gulika_kalam, day.yamagandam]
           + list(day.varjyam) + list(day.durmuhurtham)]
    if avoid_karana_names:
        bad += [(k.start, k.end) for k in day.karana if k.name in avoid_karana_names]
    return bad


def _evaluate_slot(s, e, day, block, base, facts, skip_yogas, janma_nakshatras,
                   janma_rasis, chandra_mode, prefer_tithi_class, label,
                   vara_bonus, vara_reason, abhijit, amrita, prefer_chog,
                   avoid_karana_names, horas: list[Window] | None = None,
                   prefer_varas: set[str] | None = None):
    # Special yogas (slot-time when engine given)
    yoga_bonus, yoga_reasons, defer = _score_special_yogas(
        facts.special_yogas, skip_yogas)
    if defer:
        return None

    # Tarabalam (slot-time nakshatra)
    tara_bonus, tara_reasons, tara_unfav_names = _score_tara(
        janma_nakshatras, facts.nakshatra)

    # Chandrabalam (slot-time moon rashi + mode filter)
    chandra_bonus, chandra_reasons, dropped, chandra_avoid_names, chandra_puja_names = \
        _score_chandra(janma_nakshatras, janma_rasis, facts.lunar_sign, chandra_mode)
    if dropped:
        return None

    # Tithi class (slot-time tithi)
    tithi_bonus, tithi_day_reason, tithi_activity_reason, tithi_fam = \
        _score_tithi_class(facts.tithi, prefer_tithi_class, label)

    # Nitya yoga (slot-time yoga). Samskara activities defer on
    # Vyatipata/Vaidhriti the same way they defer on Visha/Dagdha.
    skip_on_nitya_hard = bool(skip_yogas)
    nitya_bonus, nitya_reasons, defer_nitya = _score_nitya_yoga(
        facts.yoga, s, day, skip_on_nitya_hard)
    if defer_nitya:
        return None

    score = base + vara_bonus + tara_bonus + chandra_bonus \
            + tithi_bonus + yoga_bonus + nitya_bonus

    # Reason groups — assemble each category as we go.
    slot_quality = [
        f'{block.name} choghadiya (+{base})',
        'clear of all inauspicious windows',
    ]
    day_quality = list(yoga_reasons) + list(nitya_reasons)
    if tithi_day_reason:
        day_quality.append(tithi_day_reason)
    group_fit = list(tara_reasons) + list(chandra_reasons)
    activity_match: list[str] = []
    if tithi_activity_reason:
        activity_match.append(tithi_activity_reason)
    if vara_reason:
        activity_match.append(vara_reason)

    if abhijit and _overlaps(s, e, abhijit.start, abhijit.end):
        score += 2
        slot_quality.append('overlaps Abhijit Muhurta (+2)')
    if any(_overlaps(s, e, a.start, a.end) for a in amrita):
        score += 2
        slot_quality.append('overlaps Amrita Kalam (+2)')
    if prefer_chog and block.name == prefer_chog[0]:
        score += prefer_chog[1]
        activity_match.append(f'{block.name} favoured for {label} (+{prefer_chog[1]})')
    for kname in avoid_karana_names:
        activity_match.append(f'{kname} karana avoided')

    if horas and prefer_varas:
        # Find which hora this slot starts in
        for h in horas:
            if h.start <= s < h.end:
                ruler_name = h.name.split(' ')[0]
                # Map ruler to Vaaram (Sunday=0, Monday=1, ..., Saturday=6)
                ruler_idx = {'Sun': 0, 'Moon': 1, 'Mars': 2, 'Mercury': 3,
                             'Jupiter': 4, 'Venus': 5, 'Saturn': 6}.get(ruler_name)
                if ruler_idx is not None:
                    mapped_vaaram = VAARAM_NAMES[ruler_idx]
                    if mapped_vaaram in prefer_varas:
                        score += 1
                        activity_match.append(f'{h.name} favoured for {label} (+1)')
                break

    notes = _doctrinal_notes(
        special_yogas=facts.special_yogas,
        tara_unfav_names=tara_unfav_names,
        chandra_avoid_names=chandra_avoid_names,
        tithi_fam=tithi_fam,
    )

    reason_groups = {
        'slot_quality': slot_quality,
        'day_quality': day_quality,
        'group_fit': group_fit,
        'activity_match': activity_match,
        'notes': notes,
    }
    # Backward-compat flat list (existing callers / tests use this)
    reasons = slot_quality + group_fit + day_quality + activity_match

    # Personal (chandra) dosha is never fully rectified by
    # group-level yogas — flag it so a slot can't be "Excellent"
    # while carrying an unresolved personal caution, and so
    # equally-scored slots prefer the personally-clean one.
    if chandra_avoid_names:
        personal_dosha = 'ashtama_chandra' if any(
            'Ashtama' in n for n in chandra_avoid_names) else 'chandra_avoid'
    elif chandra_puja_names:
        personal_dosha = 'chandra_remedial'
    else:
        personal_dosha = None

    # Day-level dosha (Rikta tithi, Visha/Dagdha yoga, Vyatipata/
    # Vaidhriti) — same "can't be Excellent" treatment as a
    # personal chandra dosha: these are traditionally avoided
    # regardless of how high other yogas push the score.
    if tithi_fam == 'Rikta':
        day_dosha = 'rikta_tithi'
    elif any(y in _YOGA_PENALTY for y in facts.special_yogas):
        day_dosha = 'visha_dagdha_yoga'
    elif facts.yoga in NITYA_HARD_AVOID:
        day_dosha = 'vyatipata_vaidhriti'
    else:
        day_dosha = None

    return {'date': day.date.isoformat(), 'vaaram': day.vaaram,
            'start': s, 'end': e, 'score': score,
            'personal_dosha': personal_dosha,
            'day_dosha': day_dosha,
            'reasons': reasons, 'reason_groups': reason_groups}

def day_slots(day: PanchangamDay, activity: str = 'any',

              janma_nakshatras: list[str] | None = None,
              janma_rasis: list[str | None] | None = None,
              chandra_mode: str = 'stars',
              *, engine=None) -> list[dict]:
    """Ranked auspicious slots for one day (daytime, sunrise to sunset).

    When `engine` is supplied, every Moon-driven scoring component
    (tarabalam, chandrabalam, tithi class, special yogas) is recomputed
    at the slot's start time using `engine.facts_at(slot.start, day.location)`
    — so late-day slots are scored against the panchangam facts active
    THEN, not at sunrise. Vara remains day-level (sunrise-anchored by
    classical convention).

    When `engine` is None (default), every component falls back to the
    day's sunrise snapshot — the pre-B1-Heavy behaviour. This keeps
    every existing caller working unchanged.

    Scoring components (all mode-independent):
      Tarabalam      ±1 per person, slot-time nakshatra
      Chandrabalam   +1/0/-1 per person, slot-time moon rashi
      Tithi class    -2 universal for Rikta, +1 for activity match
      Vara           +1 for activity-preferred weekday (day-level)
      Special yogas  Sarvartha/Amrita +2, Dvi/Tripushkara +1,
                     Visha/Dagdha -2 — recomputed at slot time when
                     `engine` is given
      Choghadiya     1..3 base, ±1 activity preference
      Abhijit/Amrita +2 each on slot overlap

    Hard skips (slot excluded):
      Eclipse day            — entire day
      Slot inside avoid_karana — slot only (Vishti for travel, etc.)
      skip_on_yoga match     — slot only (when engine), day (when not)
      chandra_mode filter    — slot or day depending on engine presence

    Mode filtering ('chandra_mode') only changes which slots survive;
    scoring itself is universal.
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

    rules = ACTIVITY_RULES[activity]
    skip_yogas = set(rules.get('skip_on_yoga', ()))
    prefer_chog = rules.get('prefer_choghadiya')   # ('Block', bonus) or None
    avoid_karana_names = set(rules.get('avoid_karana', ()))
    prefer_tithi_class = rules.get('prefer_tithi_class')
    prefer_varas = set(rules.get('prefer_vara', ()))
    label = rules['label']

    # Vara is sunrise-anchored (one constant per panchangam day).
    vara_bonus = 1 if day.vaaram in prefer_varas else 0
    vara_reason = (f'{day.vaaram} favoured for {label} (+1)'
                   if vara_bonus else None)

    bad = _get_bad_windows(day, avoid_karana_names)
    abhijit = day.abhijit_muhurta
    amrita = list(day.amrita_kalam)

    horas = get_horas(day)

    # Engine-precise mode: per-slot facts via engine.facts_at(start).
    # Snapshot mode: every slot sees the day's sunrise facts.
    use_engine = engine is not None and hasattr(engine, 'facts_at')
    snapshot = _day_snapshot_facts(day) if not use_engine else None

    slots = []
    for block in day.choghadiya:
        base = GOOD_CHOGHADIYA.get(block.name)
        if base is None:
            continue
        for s, e in _subtract(block.start, block.end, bad):
            if (e - s) < timedelta(minutes=MIN_SLOT_MINUTES):
                continue
            facts = engine.facts_at(s, day.location, vaaram=day.vaaram) \
                    if use_engine else snapshot

            slot_dict = _evaluate_slot(
                s=s, e=e, day=day, block=block, base=base, facts=facts,
                skip_yogas=skip_yogas, janma_nakshatras=janma_nakshatras,
                janma_rasis=janma_rasis, chandra_mode=chandra_mode,
                prefer_tithi_class=prefer_tithi_class, label=label,
                vara_bonus=vara_bonus, vara_reason=vara_reason,
                abhijit=abhijit, amrita=amrita, prefer_chog=prefer_chog,
                avoid_karana_names=avoid_karana_names,
                horas=horas, prefer_varas=prefer_varas
            )
            if slot_dict is not None:
                slots.append(slot_dict)

    # Tier each slot relative to the scores found on this day, then sort
    # tier-first (Excellent > Good > Fair > Avoid), then by score, then
    # the personal-dosha tiebreaker, then chronological. This keeps the
    # visible tier pill consistent with rank order — a "Good" slot never
    # sits above an "Excellent" one just because its raw score is higher.
    assign_tiers(slots)
    slots.sort(key=lambda x: (-TIER_NAMES.index(x['tier']), -x['score'],
                              x['personal_dosha'] is not None, x['start']))
    return slots
