# Muhurta finder — public API.
#
# Orchestrates the atomic scorers in slot_scorers.py and the activity
# configuration in activity_rules.py into a ranked list of auspicious
# slots for a given day. Scoring is universal (same astrological judgement
# regardless of chandra_mode); chandra_mode controls only which slots
# survive the filter pass.
from datetime import datetime, timedelta

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES, ACTIVITIES
from telugu_panchangam.personal.lagna_hora import get_horas, get_lagna_transitions
from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
from telugu_panchangam.personal.slot_scorers import (
    _DayContext,
    YOGA_PENALTY,
    score_tara, score_chandra, score_lagna, score_lagna_activity,
    score_tithi_class, score_special_yogas, score_nitya_yoga,
    anandadi_day_modifier, doctrinal_notes, slot_lagna_name,
)
from telugu_panchangam.panchaka import evaluate_panchaka

GOOD_CHOGHADIYA = {'Amrit': 3, 'Shubh': 2, 'Labh': 2, 'Char': 1}
MIN_SLOT_MINUTES = 24   # one ghati — minimum piece after bad-window subtraction
MUHURTA_MINUTES = 48    # one classical muhurta (2 ghati) — the slot window size

# Night choghadiya sequence (8 blocks sunset→next sunrise), weekday 0=Sunday.
# Matches _NIGHT_CHOGHADIYA in generators/ics.py — both must stay in sync.
_NIGHT_CHOGHADIYA = {
    0: ['Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh'],
    1: ['Char',  'Rog',   'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char'],
    2: ['Kaal',  'Labh',  'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog',  'Kaal'],
    3: ['Udveg', 'Shubh', 'Amrit', 'Char', 'Rog',   'Kaal', 'Labh', 'Udveg'],
    4: ['Amrit', 'Char',  'Rog',  'Kaal', 'Labh',  'Udveg', 'Shubh', 'Amrit'],
    5: ['Rog',   'Kaal',  'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog'],
    6: ['Labh',  'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog',   'Kaal', 'Labh'],
}

CHANDRA_MODES = ('stars', 'puja_ok', 'strict')

TIER_NAMES = ('Avoid', 'Fair', 'Good', 'Excellent')

# Tier thresholds — score → human-anchor label.
#   ≥ +7: Excellent   rare alignment, multiple positive signals
#   +4..+6: Good      solid recommendation
#   +1..+3: Fair      workable, often with compromises
#   ≤ 0:   Avoid      significant negatives outweigh the slot
_RELATIVE_BANDS = (0.75, 0.5, 0.25)


def score_tier(score: int) -> str:
    if score >= 7:
        return 'Excellent'
    if score >= 4:
        return 'Good'
    if score >= 1:
        return 'Fair'
    return 'Avoid'


def relative_tier(score: int, ceiling: int, floor: int) -> str:
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
    which batch supplied the ceiling/floor.
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


# ---------------------------------------------------------------------------
# Day-level utilities
# ---------------------------------------------------------------------------

_MUHURTA_DUR = timedelta(minutes=MUHURTA_MINUTES)


def _chog_at_time(t: datetime, choghadiya: list) -> 'Window | None':
    """Return the choghadiya block active at time t, or None if t is outside all blocks."""
    for block in choghadiya:
        if block.start <= t < block.end:
            return block
    return None


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


def _get_bad_windows(day, avoid_karana_names):
    bad = [(w.start, w.end) for w in
           [day.rahu_kalam, day.gulika_kalam, day.yamagandam]
           + list(day.varjyam) + list(day.durmuhurtham)
           + list(day.vishaghati)]
    if day.bhadra_mukha is not None:
        bad.append((day.bhadra_mukha.start, day.bhadra_mukha.end))
    if avoid_karana_names:
        bad += [(k.start, k.end) for k in day.karana if k.name in avoid_karana_names]
    return bad


def _get_bad_windows_night(day, avoid_karana_names):
    """Bad windows for night scoring — same as day but without Rahu/Gulika/Yamagandam.

    Rahu Kalam, Gulika Kalam, and Yamagandam are daytime-only; Varjyam and
    Durmuhurtham are nakshatra/muhurta-based and can fall at night.
    """
    bad = [(w.start, w.end) for w in
           list(day.varjyam) + list(day.durmuhurtham)
           + list(day.vishaghati)]
    if day.bhadra_mukha is not None:
        bad.append((day.bhadra_mukha.start, day.bhadra_mukha.end))
    if avoid_karana_names:
        bad += [(k.start, k.end) for k in day.karana if k.name in avoid_karana_names]
    return bad


def _day_snapshot_facts(day):
    """Sunrise-snapshot SlotFacts when no engine is supplied."""
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


# ---------------------------------------------------------------------------
# Shared day-skip gate — used by both day_slots() and diagnose_day()
# ---------------------------------------------------------------------------

def _day_skip_reason(day, rules, activity, travel_direction,
                     janma_rasis, chandra_mode) -> str | None:
    """Return a reason string if the day should be skipped, else None.

    Covers eclipse, disha shoola, all rule-driven skips (khar maasa,
    adhika, pitru paksha, simha-stha guru, combustion, skip-on-yoga),
    and chandra_mode day-level filtering.
    """
    if day.eclipse is not None:
        kind = f'{day.eclipse.kind} eclipse'
        return f'{kind} — auspicious activities deferred'

    if activity == 'travel' and travel_direction is not None:
        blocked = getattr(day, 'disha_shoola_direction', None)
        if blocked is not None and travel_direction == blocked:
            return (f'Disha Shoola ({day.vaaram}) — travel toward {blocked} '
                    f'is inauspicious on this weekday')

    if rules.get('skip_on_panchaka_nakshatra') and day.in_panchaka_nakshatra:
        return (f'Panchaka Nakshatra ({day.nakshatra.name}) — '
                f'{rules["label"]} traditionally avoided')

    if rules.get('skip_on_khar_maasa') and day.is_khar_maasa:
        return (f'Khar-Maasa ({day.khar_maasa_name} Maasa) — '
                f'{rules["label"]} traditionally avoided')

    if rules.get('skip_on_adhika') and day.maasam.startswith('Adhika '):
        return f'Adhika Maasa — {rules["label"]} traditionally avoided'

    if rules.get('skip_on_pitru_paksha') and day.is_pitru_paksha:
        return f'Pitru Paksha (Bhadrapada Krishna paksha) — {rules["label"]} traditionally avoided'

    if rules.get('skip_on_simha_stha_guru') and day.simha_stha_guru:
        return (f'Simha-Stha Guru — '
                f'{rules["label"]} traditionally avoided while Jupiter is in Simha')

    for g in rules.get('skip_on_combust', []):
        info = getattr(day, f'{g.lower()}_maudhya', None)
        if info is not None and info.combust:
            return (f'{g} Maudhya ({info.elongation_deg:.1f}° < {info.threshold_deg}°) — '
                    f'{rules["label"]} traditionally avoided when {g} is combust')

    skip_yogas = set(rules.get('skip_on_yoga', ()))
    if skip_yogas:
        for y in day.special_yogas:
            if y in skip_yogas:
                return f'{y} — {rules["label"]} traditionally avoids this day'
        if day.yoga.name in NITYA_HARD_AVOID:
            return f'{day.yoga.name} yoga — samskaras traditionally defer'

    if janma_rasis is not None and chandra_mode != 'stars':
        has_avoid = False
        has_remedial = False
        from telugu_panchangam.personal.chandrabalam import (
            CHANDRA_GOOD, CHANDRA_PUJA, chandra_position,
        )
        for r in janma_rasis:
            if r is None:
                continue
            pos = chandra_position(r, day.lunar_sign)
            if pos not in CHANDRA_GOOD and pos not in CHANDRA_PUJA:
                has_avoid = True
            elif pos in CHANDRA_PUJA:
                has_remedial = True
        if chandra_mode == 'strict' and (has_avoid or has_remedial):
            return 'chandra_mode=strict — Moon at sunrise fails for at least one person'
        if chandra_mode == 'puja_ok' and has_avoid:
            return 'chandra_mode=puja_ok — someone has Moon-avoid (4/8/12)'

    return None


# ---------------------------------------------------------------------------
# diagnose_day — explains why day_slots() would return []
# ---------------------------------------------------------------------------

def diagnose_day(day, activity='any', janma_nakshatras=None,
                 janma_rasis=None, chandra_mode='stars',
                 travel_direction: str | None = None):
    """If day_slots() would return [] for these inputs, explain why.

    Returns a string (the reason) or None when the day is not filtered.
    Used by MCP find_muhurta to populate dropped_days[].
    """
    rules = ACTIVITY_RULES.get(activity, ACTIVITY_RULES['any'])
    return _day_skip_reason(day, rules, activity, travel_direction,
                            janma_rasis, chandra_mode)


# ---------------------------------------------------------------------------
# Slot evaluation — orchestrates all scorers for one candidate slot
# ---------------------------------------------------------------------------

def _evaluate_slot(s, e, block, base, facts, ctx: _DayContext) -> dict | None:
    day = ctx.day

    # Special yogas
    yoga_bonus, yoga_reasons, defer = score_special_yogas(
        facts.special_yogas, ctx.skip_yogas)
    if defer:
        return None

    # Tarabalam
    tara_bonus, tara_reasons, tara_unfav_names = score_tara(
        ctx.janma_nakshatras, facts.nakshatra)

    # Chandrabalam
    chandra_bonus, chandra_reasons, dropped, chandra_avoid_names, chandra_puja_names = \
        score_chandra(ctx.janma_nakshatras, ctx.janma_rasis,
                      facts.lunar_sign, ctx.chandra_mode)
    if dropped:
        return None

    # Tithi class (nakshatra + special_yogas enable dosha neutralization)
    tithi_bonus, tithi_day_reason, tithi_activity_reason, tithi_fam = \
        score_tithi_class(facts.tithi, ctx.prefer_tithi_class, ctx.label,
                          nakshatra=facts.nakshatra,
                          special_yogas=facts.special_yogas)

    # Nitya yoga
    skip_on_nitya_hard = bool(ctx.skip_yogas)
    nitya_bonus, nitya_reasons, defer_nitya = score_nitya_yoga(
        facts.yoga, s, day, skip_on_nitya_hard)
    if defer_nitya:
        return None

    # Anandadi
    anandadi_bonus, anandadi_reason = anandadi_day_modifier(day)

    score = (base + ctx.vara_bonus + tara_bonus + chandra_bonus
             + tithi_bonus + yoga_bonus + nitya_bonus
             + ctx.simha_stha_shukra_penalty + anandadi_bonus)

    # Assemble reason buckets
    slot_quality = [
        f'{block.name} choghadiya (+{base})',
        'clear of all inauspicious windows',
    ]
    day_quality = list(yoga_reasons) + list(nitya_reasons)
    if ctx.simha_stha_shukra_penalty:
        day_quality.append(
            f'Simha-Stha Shukra (Venus in Simha) ({ctx.simha_stha_shukra_penalty})'
        )
    if anandadi_reason:
        day_quality.append(anandadi_reason)
    if tithi_day_reason:
        day_quality.append(tithi_day_reason)
    group_fit = list(tara_reasons) + list(chandra_reasons)
    activity_match: list[str] = []
    if tithi_activity_reason:
        activity_match.append(tithi_activity_reason)
    if ctx.vara_reason:
        activity_match.append(ctx.vara_reason)

    # Overlap bonuses
    if ctx.abhijit and _overlaps(s, e, ctx.abhijit.start, ctx.abhijit.end):
        score += 2
        slot_quality.append('overlaps Abhijit Muhurta (+2)')
    if any(_overlaps(s, e, a.start, a.end) for a in ctx.amrita):
        score += 2
        slot_quality.append('overlaps Amrita Kalam (+2)')
    if ctx.prefer_bhadra_puchha and day.bhadra_puchha is not None \
            and _overlaps(s, e, day.bhadra_puchha.start, day.bhadra_puchha.end):
        score += ctx.prefer_bhadra_puchha
        activity_match.append(f'Bhadra Puchha overlap (+{ctx.prefer_bhadra_puchha})')
    if ctx.prefer_nakshatra_mukha is not None:
        preferred_classes, mukha_bonus = ctx.prefer_nakshatra_mukha
        day_mukha = getattr(day, 'nakshatra_mukha', None)
        if day_mukha is not None and day_mukha in preferred_classes:
            score += mukha_bonus
            activity_match.append(f'Nakshatra Mukha {day_mukha} (+{mukha_bonus})')
    if ctx.prefer_chog and block.name == ctx.prefer_chog[0]:
        score += ctx.prefer_chog[1]
        activity_match.append(
            f'{block.name} favoured for {ctx.label} (+{ctx.prefer_chog[1]})')
    for kname in ctx.avoid_karana_names:
        activity_match.append(f'{kname} karana avoided')

    # Hora Vara bonus
    if ctx.horas and ctx.prefer_varas:
        from telugu_panchangam.panchangam_names import VAARAM_NAMES
        for h in ctx.horas:
            if h.start <= s < h.end:
                ruler_name = h.name.split(' ')[0]
                ruler_idx = {'Sun': 0, 'Moon': 1, 'Mars': 2, 'Mercury': 3,
                             'Jupiter': 4, 'Venus': 5, 'Saturn': 6}.get(ruler_name)
                if ruler_idx is not None:
                    from telugu_panchangam.panchangam_names import VAARAM_NAMES
                    mapped_vaaram = VAARAM_NAMES[ruler_idx]
                    if mapped_vaaram in ctx.prefer_varas:
                        score += 1
                        activity_match.append(
                            f'{h.name} favoured for {ctx.label} (+1)')
                break

    # Lagna scoring
    cur_lagna = slot_lagna_name(ctx.lagnas, s)
    lagna_bonus, lagna_reasons, lagna_ashtama_names = score_lagna(
        ctx.janma_nakshatras, ctx.janma_rasis, cur_lagna,
        janma_lagnas=ctx.janma_lagnas)
    score += lagna_bonus
    group_fit.extend(lagna_reasons)

    lagna_act_bonus, lagna_act_reason = score_lagna_activity(
        ctx.prefer_lagna_class, cur_lagna, ctx.label)
    if lagna_act_reason:
        score += lagna_act_bonus
        activity_match.append(lagna_act_reason)

    # Panchaka Rahita
    if cur_lagna is not None:
        try:
            _panchaka = evaluate_panchaka(
                tithi_name=facts.tithi,
                vaaram_name=facts.vaaram,
                nakshatra_name=facts.nakshatra,
                lagna_name=cur_lagna,
            )
            if _panchaka.name == 'Mrityu':
                day_quality.append('Mrityu Panchaka — universal samskara avoidance (-3)')
                score -= 3
            elif _panchaka.name != 'Rahita':
                _matched_avoid = None
                for _avoid_key in _panchaka.avoid_for:
                    if (_avoid_key in ACTIVITY_RULES and
                            ACTIVITY_RULES[_avoid_key]['label'].lower() == ctx.label.lower()):
                        _matched_avoid = _avoid_key
                        break
                    if _avoid_key in ctx.label.lower().replace(' ', '_'):
                        _matched_avoid = _avoid_key
                        break
                if _matched_avoid is not None:
                    day_quality.append(
                        f'{_panchaka.name} Panchaka conflicts with {ctx.label} (-2)')
                    score -= 2
        except (ValueError, KeyError):
            pass

    notes = doctrinal_notes(
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
    reasons = slot_quality + group_fit + day_quality + activity_match

    # Personal dosha flag
    if chandra_avoid_names:
        personal_dosha = 'ashtama_chandra' if any(
            'Ashtama' in n for n in chandra_avoid_names) else 'chandra_avoid'
    elif lagna_ashtama_names:
        personal_dosha = 'ashtama_lagna'
    elif chandra_puja_names:
        personal_dosha = 'chandra_remedial'
    elif tara_unfav_names and not any(
            y in ('Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga')
            for y in facts.special_yogas):
        personal_dosha = 'tara_dosha'
    else:
        personal_dosha = None

    # Day-level dosha flag
    if tithi_fam == 'Rikta':
        day_dosha = 'rikta_tithi'
    elif 'Amavasya' in facts.tithi:
        day_dosha = 'amavasya'
    elif any(y in YOGA_PENALTY for y in facts.special_yogas):
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def day_slots(day: PanchangamDay, activity: str = 'any',
              janma_nakshatras: list[str] | None = None,
              janma_rasis: list[str | None] | None = None,
              janma_lagnas: list[str | None] | None = None,
              chandra_mode: str = 'stars',
              travel_direction: str | None = None,
              *, engine=None) -> list[dict]:
    """Ranked auspicious slots for one day (daytime, sunrise to sunset).

    When `engine` is supplied, every Moon-driven scoring component is
    recomputed at the slot's start time via engine.facts_at(). When None,
    the day's sunrise snapshot is used (backward-compatible default).

    Scoring components (all mode-independent):
      Tarabalam      ±1 per person, slot-time nakshatra
      Chandrabalam   +1/0/-1 per person, slot-time moon rashi
      Tithi class    -2 for Rikta, +1 for activity match
      Vara           +1 for activity-preferred weekday (day-level)
      Special yogas  Sarvartha/Amrita +2, Dvi/Tripushkara +1, Visha/Dagdha -2
      Choghadiya     1..3 base, ±1 activity preference
      Abhijit/Amrita +2 each on slot overlap

    chandra_mode controls which slots survive the filter; it does not
    change scores.
    """
    if activity not in ACTIVITIES:
        raise ValueError(f'activity must be one of {ACTIVITIES}')
    if chandra_mode not in CHANDRA_MODES:
        raise ValueError(f'chandra_mode must be one of {CHANDRA_MODES}')
    if janma_rasis is not None and janma_nakshatras is not None:
        if len(janma_rasis) != len(janma_nakshatras):
            raise ValueError('janma_rasis must align with janma_nakshatras '
                             '(use None for people whose rashi is unknown).')

    rules = ACTIVITY_RULES[activity]
    reason = _day_skip_reason(day, rules, activity, travel_direction,
                              janma_rasis, chandra_mode)
    if reason is not None:
        return []

    skip_yogas = frozenset(rules.get('skip_on_yoga', ()))
    prefer_chog = rules.get('prefer_choghadiya')
    avoid_karana_names = frozenset(rules.get('avoid_karana', ()))
    prefer_tithi_class = rules.get('prefer_tithi_class')
    prefer_varas = frozenset(rules.get('prefer_vara', ()))
    prefer_lagna_class = rules.get('prefer_lagna_class')
    prefer_bhadra_puchha = rules.get('prefer_bhadra_puchha', 0)
    prefer_nakshatra_mukha = rules.get('prefer_nakshatra_mukha')
    label = rules['label']

    _shukra_penalty = rules.get('penalty_on_simha_stha_shukra', 0) \
        if day.simha_stha_shukra else 0

    vara_bonus = 1 if day.vaaram in prefer_varas else 0
    vara_reason = (f'{day.vaaram} favoured for {label} (+1)'
                   if vara_bonus else None)

    bad = _get_bad_windows(day, avoid_karana_names)
    if rules.get('skip_on_sankramana') and day.sankramana_avoidance is not None:
        bad.append((day.sankramana_avoidance.start, day.sankramana_avoidance.end))

    ctx = _DayContext(
        day=day,
        skip_yogas=skip_yogas,
        janma_nakshatras=janma_nakshatras,
        janma_rasis=janma_rasis,
        janma_lagnas=janma_lagnas,
        chandra_mode=chandra_mode,
        prefer_tithi_class=prefer_tithi_class,
        label=label,
        vara_bonus=vara_bonus,
        vara_reason=vara_reason,
        abhijit=day.abhijit_muhurta,
        amrita=list(day.amrita_kalam),
        prefer_chog=prefer_chog,
        avoid_karana_names=avoid_karana_names,
        horas=get_horas(day),
        prefer_varas=prefer_varas,
        lagnas=get_lagna_transitions(day),
        prefer_lagna_class=prefer_lagna_class,
        prefer_bhadra_puchha=prefer_bhadra_puchha,
        simha_stha_shukra_penalty=_shukra_penalty,
        prefer_nakshatra_mukha=prefer_nakshatra_mukha,
    )

    use_engine = engine is not None and hasattr(engine, 'facts_at')
    snapshot = _day_snapshot_facts(day) if not use_engine else None

    slots = []
    t = day.sunrise
    while t < day.sunset:
        win_end = min(t + _MUHURTA_DUR, day.sunset)
        block = _chog_at_time(t, day.choghadiya)
        if block is not None:
            base = GOOD_CHOGHADIYA.get(block.name)
            if base is not None:
                for s, e in _subtract(t, win_end, bad):
                    if (e - s) < timedelta(minutes=MIN_SLOT_MINUTES):
                        continue
                    facts = engine.facts_at(s, day.location, vaaram=day.vaaram) \
                            if use_engine else snapshot
                    slot_dict = _evaluate_slot(s, e, block, base, facts, ctx)
                    if slot_dict is not None:
                        slots.append(slot_dict)
        t += _MUHURTA_DUR

    assign_tiers(slots)
    slots.sort(key=lambda x: (-TIER_NAMES.index(x['tier']), -x['score'],
                              x['personal_dosha'] is not None, x['start']))
    return slots


def night_slots(day: PanchangamDay, next_day: PanchangamDay,
                activity: str = 'any',
                janma_nakshatras: list[str] | None = None,
                janma_rasis: list[str | None] | None = None,
                janma_lagnas: list[str | None] | None = None,
                chandra_mode: str = 'stars',
                travel_direction: str | None = None,
                *, engine=None) -> list[dict]:
    """Ranked auspicious slots for one night (today's sunset to tomorrow's sunrise).

    Mirrors day_slots() with the following night-specific differences:
    - Uses night choghadiya blocks (8 equal parts of sunset→next sunrise)
    - Omits Rahu Kalam / Gulika Kalam / Yamagandam (daytime-only in standard practice)
    - Omits Abhijit Muhurta bonus (anchored to solar noon; no night equivalent)
    - Adds Brahma Muhurta bonus (+2) from next_day.brahma_muhurta
    - Adds Nishita Kala bonus (+2) at the midpoint of the night (±1 ghati)

    `next_day` must be the PanchangamDay for the calendar day after `day`.
    Its sunrise time defines the end of the night, and its brahma_muhurta
    gives the pre-dawn auspicious window.
    """
    if activity not in ACTIVITIES:
        raise ValueError(f'activity must be one of {ACTIVITIES}')
    if chandra_mode not in CHANDRA_MODES:
        raise ValueError(f'chandra_mode must be one of {CHANDRA_MODES}')
    if janma_rasis is not None and janma_nakshatras is not None:
        if len(janma_rasis) != len(janma_nakshatras):
            raise ValueError('janma_rasis must align with janma_nakshatras '
                             '(use None for people whose rashi is unknown).')

    # Same day-level hard skips as day_slots().
    if day.eclipse is not None:
        return []
    if activity == 'travel' and travel_direction is not None:
        blocked = getattr(day, 'disha_shoola_direction', None)
        if blocked is not None and travel_direction == blocked:
            return []

    rules = ACTIVITY_RULES[activity]

    if rules.get('skip_on_panchaka_nakshatra') and day.in_panchaka_nakshatra:
        return []
    if rules.get('skip_on_khar_maasa') and day.is_khar_maasa:
        return []
    if rules.get('skip_on_adhika') and day.maasam.startswith('Adhika '):
        return []
    if rules.get('skip_on_pitru_paksha') and day.is_pitru_paksha:
        return []
    if rules.get('skip_on_simha_stha_guru') and day.simha_stha_guru:
        return []
    for g in rules.get('skip_on_combust', []):
        info = getattr(day, f'{g.lower()}_maudhya', None)
        if info is not None and info.combust:
            return []

    skip_yogas = set(rules.get('skip_on_yoga', ()))
    prefer_chog = rules.get('prefer_choghadiya')
    avoid_karana_names = set(rules.get('avoid_karana', ()))
    prefer_tithi_class = rules.get('prefer_tithi_class')
    prefer_varas = set(rules.get('prefer_vara', ()))
    prefer_lagna_class = rules.get('prefer_lagna_class')
    prefer_bhadra_puchha = rules.get('prefer_bhadra_puchha', 0)
    prefer_nakshatra_mukha = rules.get('prefer_nakshatra_mukha')
    label = rules['label']

    _shukra_penalty = rules.get('penalty_on_simha_stha_shukra', 0) \
        if day.simha_stha_shukra else 0

    # Vara is sunrise-anchored — carries through the night following that sunrise.
    vara_bonus = 1 if day.vaaram in prefer_varas else 0
    vara_reason = (f'{day.vaaram} favoured for {label} (+1)' if vara_bonus else None)

    bad = _get_bad_windows_night(day, avoid_karana_names)
    if rules.get('skip_on_sankramana') and day.sankramana_avoidance is not None:
        bad.append((day.sankramana_avoidance.start, day.sankramana_avoidance.end))

    amrita = list(day.amrita_kalam)  # absolute datetimes; night-spanning ones included

    # Brahma Muhurta: from next_day (the 48-min window before tomorrow's sunrise).
    brahma = next_day.brahma_muhurta

    # Nishita Kala: midpoint of night ± 1 ghati (24 min).
    _ONE_GHATI = timedelta(minutes=24)
    nishita_mid = day.sunset + (next_day.sunrise - day.sunset) / 2
    nishita_start = nishita_mid - _ONE_GHATI
    nishita_end = nishita_mid + _ONE_GHATI

    # Night choghadiya blocks (engine convention: Sunday=0).
    weekday = (day.date.weekday() + 1) % 7
    _block_dur = (next_day.sunrise - day.sunset) / 8
    night_blocks = [
        Window(name=_NIGHT_CHOGHADIYA[weekday][i],
               start=day.sunset + i * _block_dur,
               end=day.sunset + (i + 1) * _block_dur)
        for i in range(8)
    ]

    # get_horas() returns 24 horas covering the full day+night from today's sunrise.
    # get_lagna_transitions() covers sunrise to next sunrise.
    # Both are already night-aware — no special handling needed.
    horas = get_horas(day)
    lagnas = get_lagna_transitions(day)

    ctx = _DayContext(
        day=day,
        skip_yogas=frozenset(skip_yogas),
        janma_nakshatras=janma_nakshatras,
        janma_rasis=janma_rasis,
        janma_lagnas=janma_lagnas,
        chandra_mode=chandra_mode,
        prefer_tithi_class=prefer_tithi_class,
        label=label,
        vara_bonus=vara_bonus,
        vara_reason=vara_reason,
        abhijit=None,   # no Abhijit at night
        amrita=amrita,
        prefer_chog=prefer_chog,
        avoid_karana_names=frozenset(avoid_karana_names),
        horas=horas,
        prefer_varas=frozenset(prefer_varas),
        lagnas=lagnas,
        prefer_lagna_class=prefer_lagna_class,
        prefer_bhadra_puchha=prefer_bhadra_puchha,
        simha_stha_shukra_penalty=_shukra_penalty,
        prefer_nakshatra_mukha=prefer_nakshatra_mukha,
    )

    use_engine = engine is not None and hasattr(engine, 'facts_at')
    snapshot = _day_snapshot_facts(day) if not use_engine else None

    slots = []
    t = day.sunset
    while t < next_day.sunrise:
        win_end = min(t + _MUHURTA_DUR, next_day.sunrise)
        block = _chog_at_time(t, night_blocks)
        if block is not None:
            base = GOOD_CHOGHADIYA.get(block.name)
            if base is not None:
                for s, e in _subtract(t, win_end, bad):
                    if (e - s) < timedelta(minutes=MIN_SLOT_MINUTES):
                        continue
                    facts = engine.facts_at(s, day.location, vaaram=day.vaaram) \
                            if use_engine else snapshot
                    slot_dict = _evaluate_slot(s, e, block, base, facts, ctx)
                    if slot_dict is None:
                        continue

                    # Night-specific bonuses applied after _evaluate_slot().
                    night_bonuses: list[str] = []
                    if brahma is not None and _overlaps(s, e, brahma.start, brahma.end):
                        slot_dict['score'] += 2
                        night_bonuses.append('overlaps Brahma Muhurta (+2)')
                    if _overlaps(s, e, nishita_start, nishita_end):
                        slot_dict['score'] += 2
                        night_bonuses.append('overlaps Nishita Kala (+2)')
                    if night_bonuses:
                        slot_dict['reason_groups']['slot_quality'].extend(night_bonuses)
                        slot_dict['reasons'].extend(night_bonuses)

                    slots.append(slot_dict)
        t += _MUHURTA_DUR

    assign_tiers(slots)
    slots.sort(key=lambda x: (-TIER_NAMES.index(x['tier']), -x['score'],
                              x['personal_dosha'] is not None, x['start']))
    return slots
