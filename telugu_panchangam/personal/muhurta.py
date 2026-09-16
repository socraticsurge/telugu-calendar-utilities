# Muhurta finder — public API.
#
# Orchestrates the atomic scorers in slot_scorers.py and the activity
# configuration in activity_rules.py into a ranked list of auspicious
# slots for a given day. Scoring is universal (same astrological judgement
# regardless of chandra_mode); chandra_mode controls only which slots
# survive the filter pass.
from dataclasses import dataclass
from datetime import timedelta

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.muhurtas import named_muhurtas
from telugu_panchangam.personal.activity_rules import (
    ACTIVITIES,
    ACTIVITY_RULES,
    canonical_activity_nakshatras,
    get_activity_rules,
)
from telugu_panchangam.personal.election_assessors.karnavedha import (
    KARNAVEDHA_DAYLIGHT_POLICY_ID,
    evaluate_karnavedha_daylight,
)
from telugu_panchangam.personal.lagna_hora import get_horas, get_lagna_transitions
from telugu_panchangam.personal.muhurta_eligibility import (
    _day_skip_reason,
    _night_unavailable,
    _overlaps,
)
from telugu_panchangam.personal.muhurta_slot_scoring import (
    _evaluate_slot,
    _SlotCandidate,
)
from telugu_panchangam.personal.search_contract import SearchOptions
from telugu_panchangam.personal.slot_scorers import _DayContext

GOOD_CHOGHADIYA = {'Amrit': 3, 'Shubh': 2, 'Labh': 2, 'Char': 1}
MUHURTA_MINUTES = 48  # one classical muhurta (2 ghati) · the slot window size

# Night choghadiya sequence (8 blocks sunset→next sunrise), weekday 0=Sunday.
# Matches _NIGHT_CHOGHADIYA in generators/ics.py — both must stay in sync.
_NIGHT_CHOGHADIYA = {
    0: ['Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh'],
    1: ['Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char'],
    2: ['Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog', 'Kaal'],
    3: ['Udveg', 'Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg'],
    4: ['Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit'],
    5: ['Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog'],
    6: ['Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh'],
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
        if tier == 'Excellent' and (
            s['personal_dosha'] is not None or s['day_dosha'] is not None
        ):
            tier = 'Good'
        s['tier'] = tier


# ---------------------------------------------------------------------------
# Day-level utilities
# ---------------------------------------------------------------------------


def _dominant_choghadiya(s, e, choghadiya):
    """The choghadiya block covering most of [s, e], and (when the
    muhurta straddles a boundary) the name of the secondary block it
    also touches (else None). Choghadiya is a scoring attribute, not a
    gate, so a straddling muhurta is scored by its dominant block and the
    straddle is disclosed."""
    best, best_overlap, touched = None, timedelta(0), []
    for blk in choghadiya:
        lo, hi = max(s, blk.start), min(e, blk.end)
        ov = hi - lo
        if ov > timedelta(0):
            touched.append(blk.name)
            if ov > best_overlap:
                best, best_overlap = blk, ov
    other = next((n for n in touched if n != best.name), None) if best else None
    return best, other


def _get_bad_windows(day, avoid_karana_names):
    bad = [
        (w.start, w.end)
        for w in [day.rahu_kalam, day.gulika_kalam, day.yamagandam]
        + list(day.varjyam)
        + list(day.durmuhurtham)
        + list(day.vishaghati)
    ]
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
    bad = [
        (w.start, w.end)
        for w in list(day.varjyam) + list(day.durmuhurtham) + list(day.vishaghati)
    ]
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
# diagnose_day — explains why day_slots() would return []
# ---------------------------------------------------------------------------


def _validate_participants(janma_nakshatras, janma_rasis) -> None:
    if janma_nakshatras is None or janma_rasis is None:
        return
    if len(janma_nakshatras) != len(janma_rasis):
        raise ValueError(
            'janma_rasis must align with janma_nakshatras '
            '(use None for people whose rashi is unknown).'
        )


def diagnose_day(
    day,
    activity='any',
    janma_nakshatras=None,
    janma_rasis=None,
    chandra_mode='stars',
    travel_direction: str | None = None,
    *,
    _daylight_assessment=None,
):
    """If day_slots() would return [] for these inputs, explain why.

    Returns a string (the reason) or None when the day is not filtered.
    Used by MCP find_muhurta to populate dropped_days[].
    """
    _validate_participants(janma_nakshatras, janma_rasis)
    rules = (
        get_activity_rules(activity)
        if activity in ACTIVITIES
        else ACTIVITY_RULES['any']
    )
    if _daylight_assessment is None:
        _daylight_assessment = karnavedha_daylight_assessment(day, rules, activity)
    return _day_skip_reason(
        day,
        rules,
        SearchOptions(
            activity=activity,
            travel_direction=travel_direction,
            janma_rasis=janma_rasis,
            chandra_mode=chandra_mode,
        ),
        _daylight_assessment,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _validate_slot_request(
    activity, chandra_mode, janma_nakshatras, janma_rasis
) -> None:
    if activity not in ACTIVITIES:
        raise ValueError(f'activity must be one of {ACTIVITIES}')
    if chandra_mode not in CHANDRA_MODES:
        raise ValueError(f'chandra_mode must be one of {CHANDRA_MODES}')
    _validate_participants(janma_nakshatras, janma_rasis)


def _slot_engine(day, rules, engine):
    use_engine = engine is not None and hasattr(engine, 'facts_at')
    if not rules.get('require_homa_election') or use_engine:
        return engine, use_engine
    from telugu_panchangam.engines.drik import DrikGanitaEngine
    from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
    from telugu_panchangam.engines.vakya import VakyaEngine

    engine_type = {
        'drik': DrikGanitaEngine,
        'surya_siddhanta': SuryaSiddhantaEngine,
        'vakya': VakyaEngine,
    }[day.system]
    return engine_type(), True


def karnavedha_daylight_assessment(day, rules, activity):
    """Return the one-per-day Karnavedha assessment when configured."""
    configured = (
        rules.get('require_single_daylight_tithi'),
        rules.get('require_single_daylight_nakshatra'),
    )
    if activity != 'karnavedha':
        return None
    if configured != (
        KARNAVEDHA_DAYLIGHT_POLICY_ID,
        KARNAVEDHA_DAYLIGHT_POLICY_ID,
    ):
        # Configuration drift is temporal uncertainty, never an admission.
        assessment = evaluate_karnavedha_daylight(day)
        for outcome in assessment['outcomes']:
            outcome['status'] = 'unknown'
            outcome['evidence'] = [
                'The configured Karnavedha daylight policy is unsupported.'
            ]
        assessment.update(
            {
                'rejected': False,
                'needs_review': True,
                'admissible': False,
            }
        )
        return assessment
    return evaluate_karnavedha_daylight(day)


def _daylight_gate(
    day,
    rules,
    activity,
    travel_direction,
    janma_rasis,
    chandra_mode,
    daylight_assessment,
):
    if daylight_assessment is None:
        daylight_assessment = karnavedha_daylight_assessment(day, rules, activity)
    reason = _day_skip_reason(
        day,
        rules,
        SearchOptions(
            activity=activity,
            travel_direction=travel_direction,
            janma_rasis=janma_rasis,
            chandra_mode=chandra_mode,
        ),
        daylight_assessment,
    )
    return daylight_assessment, reason


def _day_bad_windows(day, rules, avoid_karana_names):
    bad = _get_bad_windows(day, avoid_karana_names)
    if rules.get('skip_on_sankramana') and day.sankramana_avoidance is not None:
        bad.append((day.sankramana_avoidance.start, day.sankramana_avoidance.end))
    return bad


def _slot_context(
    day,
    rules,
    janma_nakshatras,
    janma_rasis,
    janma_lagnas,
    chandra_mode,
    *,
    abhijit,
    amrita,
    horas,
    lagnas,
) -> _DayContext:
    prefer_varas = frozenset(rules.get('prefer_vara', ()))
    vara_bonus = 1 if day.vaaram in prefer_varas else 0
    label = rules['label']
    vara_reason = f'{day.vaaram} favoured for {label} (+1)' if vara_bonus else None
    shukra_penalty = (
        rules.get('penalty_on_simha_stha_shukra', 0) if day.simha_stha_shukra else 0
    )
    return _DayContext(
        day=day,
        skip_yogas=frozenset(rules.get('skip_on_yoga', ())),
        janma_nakshatras=janma_nakshatras,
        janma_rasis=janma_rasis,
        janma_lagnas=janma_lagnas,
        chandra_mode=chandra_mode,
        prefer_tithi_class=rules.get('prefer_tithi_class'),
        avoid_tithi_class=list(rules.get('avoid_tithi_class', [])),
        label=label,
        vara_bonus=vara_bonus,
        vara_reason=vara_reason,
        abhijit=abhijit,
        amrita=amrita,
        prefer_chog=rules.get('prefer_choghadiya'),
        avoid_karana_names=frozenset(rules.get('avoid_karana', ())),
        horas=horas,
        prefer_varas=prefer_varas,
        lagnas=lagnas,
        prefer_lagna_class=rules.get('prefer_lagna_class'),
        required_lagna_class=rules.get('required_lagna_class'),
        prefer_bhadra_puchha=rules.get('prefer_bhadra_puchha', 0),
        simha_stha_shukra_penalty=shukra_penalty,
        prefer_nakshatra_mukha=rules.get('prefer_nakshatra_mukha'),
        allowed_nakshatras=canonical_activity_nakshatras(
            rules.get('allowed_nakshatras', ())
        ),
        avoid_nakshatras=canonical_activity_nakshatras(
            rules.get('avoid_nakshatras', ())
        ),
        prefer_nakshatras=canonical_activity_nakshatras(
            rules.get('prefer_nakshatras', ())
        ),
        allowed_tithi_numbers=frozenset(rules.get('allowed_tithi_numbers', ())),
        prefer_tithi_numbers=frozenset(rules.get('prefer_tithi_numbers', ())),
        allowed_tithi_names=frozenset(rules.get('allowed_tithi_names', ())),
        avoid_tithi_numbers=frozenset(rules.get('avoid_tithi_numbers', ())),
        avoid_vara_tithi_names=frozenset(
            tuple(pair) for pair in rules.get('avoid_vara_tithi_names', ())
        ),
        avoid_nitya_yogas=frozenset(rules.get('avoid_nitya_yogas', ())),
        allowed_lagnas=frozenset(rules.get('allowed_lagnas', ())),
        prefer_lagnas=frozenset(rules.get('prefer_lagnas', ())),
        caution_lagna_solar=bool(rules.get('caution_lagna_solar')),
        manual_checks=tuple(rules.get('manual_checks', ())),
        manual_prerequisites=bool(rules.get('manual_prerequisites')),
        avoid_janma_nakshatra=bool(rules.get('avoid_janma_nakshatra')),
    )


@dataclass
class _SlotEvaluation:
    day: PanchangamDay
    rules: dict
    bad: list
    ctx: _DayContext
    engine: object
    use_engine: bool
    snapshot: object

    def facts_at(self, start):
        if self.use_engine:
            return self.engine.facts_at(
                start, self.day.location, vaaram=self.day.vaaram
            )
        return self.snapshot


def _slot_evaluation(day, rules, bad, ctx, engine):
    engine, use_engine = _slot_engine(day, rules, engine)
    snapshot = _day_snapshot_facts(day) if not use_engine else None
    return _SlotEvaluation(day, rules, bad, ctx, engine, use_engine, snapshot)


def _homa_election_result(rules, facts, start, engine):
    if not rules.get('require_homa_election'):
        return True, ()
    from telugu_panchangam.personal.homa import homa_election, solar_nakshatra_at

    return homa_election(
        facts.tithi,
        facts.vaaram,
        facts.nakshatra,
        solar_nakshatra_at(start, engine),
    )


def _evaluate_candidate(mu, run: _SlotEvaluation, blocks):
    start, end = mu['start'], mu['end']
    if any(_overlaps(start, end, a, b) for a, b in run.bad):
        return None
    block, straddle = _dominant_choghadiya(start, end, blocks)
    if block is None:
        return None
    facts = run.facts_at(start)
    admitted, election_reasons = _homa_election_result(
        run.rules, facts, start, run.engine
    )
    if not admitted:
        return None
    return _evaluate_slot(
        _SlotCandidate(
            start,
            end,
            block,
            GOOD_CHOGHADIYA.get(block.name, 0),
            facts,
            {**mu, 'chog_straddle': straddle},
        ),
        run.ctx,
        election_reasons,
    )


def _evaluated_day_slot(mu, run: _SlotEvaluation, solar_noon, daylight_assessment):
    if run.rules.get('forenoon_only') and mu['end'] > solar_noon:
        return None
    slot = _evaluate_candidate(mu, run, run.day.choghadiya)
    if slot is not None and daylight_assessment is not None:
        slot['reason_groups']['day_source_outcomes'] = daylight_assessment['outcomes']
    return slot


def _rank_slots(slots):
    assign_tiers(slots)
    slots.sort(
        key=lambda item: (
            -TIER_NAMES.index(item['tier']),
            -item['score'],
            item['personal_dosha'] is not None,
            item['start'],
        )
    )
    return slots


def day_slots(
    day: PanchangamDay,
    activity: str = 'any',
    janma_nakshatras: list[str] | None = None,
    janma_rasis: list[str | None] | None = None,
    janma_lagnas: list[str | None] | None = None,
    chandra_mode: str = 'stars',
    travel_direction: str | None = None,
    *,
    engine=None,
    _daylight_assessment=None,
) -> list[dict]:
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
      Muhurta nature +2 Abhijit, +1 auspicious, -2 inauspicious
      Choghadiya     0..3 base, ±1 activity preference
      Amrita Kalam   +2 on overlap

    chandra_mode controls which slots survive the filter; it does not
    change scores.
    """
    _validate_slot_request(activity, chandra_mode, janma_nakshatras, janma_rasis)

    rules = get_activity_rules(activity)
    _daylight_assessment, reason = _daylight_gate(
        day,
        rules,
        activity,
        travel_direction,
        janma_rasis,
        chandra_mode,
        _daylight_assessment,
    )
    if reason is not None:
        return []

    ctx = _slot_context(
        day,
        rules,
        janma_nakshatras,
        janma_rasis,
        janma_lagnas,
        chandra_mode,
        abhijit=day.abhijit_muhurta,
        amrita=list(day.amrita_kalam),
        horas=get_horas(day),
        lagnas=get_lagna_transitions(day),
    )
    bad = _day_bad_windows(day, rules, ctx.avoid_karana_names)
    run = _slot_evaluation(day, rules, bad, ctx, engine)

    # Iterate the 15 named daytime muhurtas (sunrise->sunset /15). Each is
    # an indivisible slot: excluded if it overlaps any inauspicious window
    # (decision 1), otherwise scored — with its intrinsic nature, its
    # dominant choghadiya (a scoring attribute, straddle disclosed), and
    # all the per-slot factors. The muhurta grid coincides with the
    # engine's Abhijit/Durmuhurtham (see telugu_panchangam/muhurtas.py).
    slots = []
    solar_noon = day.sunrise + (day.sunset - day.sunrise) / 2
    for mu in named_muhurtas(day):
        slot_dict = _evaluated_day_slot(mu, run, solar_noon, _daylight_assessment)
        if slot_dict is not None:
            slots.append(slot_dict)
    return _rank_slots(slots)


def _night_bad_windows(day, rules, avoid_karana_names):
    bad = _get_bad_windows_night(day, avoid_karana_names)
    if rules.get('skip_on_sankramana') and day.sankramana_avoidance is not None:
        bad.append((day.sankramana_avoidance.start, day.sankramana_avoidance.end))
    return bad


def _night_choghadiya_blocks(day, next_day):
    weekday = (day.date.weekday() + 1) % 7
    block_duration = (next_day.sunrise - day.sunset) / 8
    return [
        Window(
            name=_NIGHT_CHOGHADIYA[weekday][index],
            start=day.sunset + index * block_duration,
            end=day.sunset + (index + 1) * block_duration,
        )
        for index in range(8)
    ]


def _nishita_window(day, next_day):
    one_ghati = timedelta(minutes=24)
    midpoint = day.sunset + (next_day.sunrise - day.sunset) / 2
    return midpoint - one_ghati, midpoint + one_ghati


def _evaluated_night_slot(mu, run: _SlotEvaluation, night_blocks, nishita):
    slot = _evaluate_candidate(mu, run, night_blocks)
    if slot is None:
        return None
    if _overlaps(mu['start'], mu['end'], *nishita):
        slot['score'] += 2
        slot['reason_groups']['slot_quality'].append('overlaps Nishita Kala (+2)')
        slot['reasons'].append('overlaps Nishita Kala (+2)')
    return slot


def night_slots(
    day: PanchangamDay,
    next_day: PanchangamDay,
    activity: str = 'any',
    janma_nakshatras: list[str] | None = None,
    janma_rasis: list[str | None] | None = None,
    janma_lagnas: list[str | None] | None = None,
    chandra_mode: str = 'stars',
    travel_direction: str | None = None,
    *,
    engine=None,
) -> list[dict]:
    """Ranked auspicious slots for one night (today's sunset to tomorrow's sunrise).

    Mirrors day_slots() with the following night-specific differences:
    - Uses night choghadiya blocks (8 equal parts of sunset→next sunrise)
    - Omits Rahu Kalam / Gulika Kalam / Yamagandam (daytime-only in standard practice)
    - Uses the 14th named night Muhurta, Brahma, as the +2 counterpart to Abhijit
    - Adds Nishita Kala bonus (+2) at the midpoint of the night (±1 ghati)

    `next_day` must be the PanchangamDay for the calendar day after `day`.
    Its sunrise time defines the end of the night.
    """
    _validate_slot_request(activity, chandra_mode, janma_nakshatras, janma_rasis)
    rules = get_activity_rules(activity)
    if _night_unavailable(day, rules, activity, travel_direction):
        return []

    ctx = _slot_context(
        day,
        rules,
        janma_nakshatras,
        janma_rasis,
        janma_lagnas,
        chandra_mode,
        abhijit=None,  # no Abhijit at night
        amrita=list(day.amrita_kalam),
        horas=get_horas(day),
        lagnas=get_lagna_transitions(day),
    )
    bad = _night_bad_windows(day, rules, ctx.avoid_karana_names)
    night_blocks = _night_choghadiya_blocks(day, next_day)
    nishita = _nishita_window(day, next_day)
    run = _slot_evaluation(day, rules, bad, ctx, engine)

    # The 15 named night muhurtas (sunset->next sunrise /15). Same model as
    # day_slots: hard-window exclude, dominant night-choghadiya, muhurta
    # nature. Brahma is now scored as the 14th night muhurta's nature; only
    # the Nishita Kala overlap remains a night-specific bonus.
    slots = []
    for mu in (m for m in named_muhurtas(day, next_day) if m['period'] == 'night'):
        slot_dict = _evaluated_night_slot(mu, run, night_blocks, nishita)
        if slot_dict is not None:
            slots.append(slot_dict)
    return _rank_slots(slots)
