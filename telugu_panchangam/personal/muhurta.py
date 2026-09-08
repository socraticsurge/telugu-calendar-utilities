# Muhurta finder — public API.
#
# Orchestrates the atomic scorers in slot_scorers.py and the activity
# configuration in activity_rules.py into a ranked list of auspicious
# slots for a given day. Scoring is universal (same astrological judgement
# regardless of chandra_mode); chandra_mode controls only which slots
# survive the filter pass.
from datetime import timedelta

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.muhurtas import named_muhurtas
from telugu_panchangam.panchaka import evaluate_panchaka
from telugu_panchangam.personal.activity_rules import (
    ACTIVITIES,
    ACTIVITY_RULES,
    canonical_activity_nakshatras,
    get_activity_rules,
)
from telugu_panchangam.personal.election_assessors.karnavedha import (
    KARNAVEDHA_DAYLIGHT_POLICY_ID,
    evaluate_karnavedha_daylight,
    karnavedha_daylight_drop_reason,
)
from telugu_panchangam.personal.lagna_hora import get_horas, get_lagna_transitions
from telugu_panchangam.personal.lagna_position import lagna_class_of, lagnas_in_class
from telugu_panchangam.personal.nitya_yoga import NITYA_HARD_AVOID
from telugu_panchangam.personal.slot_scorers import (
    YOGA_PENALTY,
    _DayContext,
    anandadi_day_modifier,
    doctrinal_notes,
    score_chandra,
    score_lagna,
    score_lagna_activity,
    score_nitya_yoga,
    score_special_yogas,
    score_tara,
    score_tithi_class,
    slot_lagna_name,
)
from telugu_panchangam.personal.tithi_class import tithi_number

_ADHIKA_PREFIX = 'Adhika '

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


def _overlaps(a0, a1, b0, b1) -> bool:
    return a0 < b1 and b0 < a1


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
# Shared day-skip gate — used by both day_slots() and diagnose_day()
# ---------------------------------------------------------------------------


def _calendar_profile_skip_reason(day, rules) -> str | None:
    allowed_maasams = rules.get('allowed_maasams')
    allowed_pairs = {tuple(pair) for pair in rules.get('allowed_maasa_solar_pairs', ())}
    maasam = day.maasam.removeprefix('Nija ').removeprefix(_ADHIKA_PREFIX)
    if (
        (allowed_maasams or allowed_pairs)
        and maasam not in (allowed_maasams or ())
        and (maasam, day.solar_sign) not in allowed_pairs
    ):
        return (
            f'{day.maasam} Maasa · {rules["label"]} source profile '
            'does not admit this lunar month'
        )
    allowed_varas = rules.get('allowed_varas')
    if allowed_varas and day.vaaram not in allowed_varas:
        return (
            f'{day.vaaram} · {rules["label"]} source profile '
            'does not admit this weekday'
        )
    allowed_pakshams = rules.get('allowed_pakshams')
    if allowed_pakshams and day.paksham not in allowed_pakshams:
        return (
            f'{day.paksham} Paksha · {rules["label"]} source profile '
            'does not admit this lunar fortnight'
        )
    avoided = map(tuple, rules.get('avoid_vara_paksha', ()))
    if (day.vaaram, day.paksham) in avoided:
        return (
            f'{day.vaaram} during {day.paksham} Paksha · '
            f'{rules["label"]} source profile rejects this combination'
        )
    return _solar_profile_skip_reason(day, rules)


def _solar_profile_skip_reason(day, rules) -> str | None:
    allowed_classes = rules.get('allowed_solar_classes')
    solar_class = lagna_class_of(day.solar_sign)
    if allowed_classes and solar_class not in allowed_classes:
        return (
            f'Surya in {day.solar_sign} ({solar_class}) · '
            f'{rules["label"]} source profile does not admit this Rasi class'
        )
    allowed_signs = rules.get('allowed_solar_signs')
    if allowed_signs and day.solar_sign not in allowed_signs:
        return (
            f'Surya in {day.solar_sign} · {rules["label"]} source profile '
            'does not admit this solar Rasi'
        )
    return None


def _chandra_skip_reason(day, janma_rasis, chandra_mode) -> str | None:
    if janma_rasis is None or chandra_mode == 'stars':
        return None
    from telugu_panchangam.personal.chandrabalam import (
        CHANDRA_GOOD,
        CHANDRA_PUJA,
        chandra_position,
    )

    positions = [
        chandra_position(rashi, day.lunar_sign)
        for rashi in janma_rasis
        if rashi is not None
    ]
    has_avoid = any(
        position not in CHANDRA_GOOD and position not in CHANDRA_PUJA
        for position in positions
    )
    has_remedial = any(position in CHANDRA_PUJA for position in positions)
    if chandra_mode == 'strict' and (has_avoid or has_remedial):
        return 'chandra_mode=strict · Moon at sunrise fails for at least one person'
    if chandra_mode == 'puja_ok' and has_avoid:
        return 'chandra_mode=puja_ok · someone has Moon-avoid (4/8/12)'
    return None


def _traditional_skip_reason(day, rules) -> str | None:
    if rules.get('skip_on_panchaka_nakshatra') and day.in_panchaka_nakshatra:
        return (
            f'Panchaka Nakshatra ({day.nakshatra.name}) · '
            f'{rules["label"]} traditionally avoided'
        )
    if rules.get('skip_on_khar_maasa') and day.is_khar_maasa:
        return (
            f'Khar-Maasa ({day.khar_maasa_name} Maasa) · '
            f'{rules["label"]} traditionally avoided'
        )
    if rules.get('skip_on_adhika') and day.maasam.startswith(_ADHIKA_PREFIX):
        return f'Adhika Maasa · {rules["label"]} traditionally avoided'
    if rules.get('skip_on_pitru_paksha') and day.is_pitru_paksha:
        return (
            'Pitru Paksha (Bhadrapada Krishna paksha) · '
            f'{rules["label"]} traditionally avoided'
        )
    if rules.get('skip_on_simha_stha_guru') and day.simha_stha_guru:
        return (
            'Simha-Stha Guru · '
            f'{rules["label"]} traditionally avoided while Jupiter is in Simha'
        )
    if reason := _combustion_skip_reason(day, rules):
        return reason
    return _yoga_skip_reason(day, rules)


def _combustion_skip_reason(day, rules) -> str | None:
    for graha in rules.get('skip_on_combust', []):
        info = getattr(day, f'{graha.lower()}_maudhya', None)
        if info is not None and info.combust:
            return (
                f'{graha} Maudhya ({info.elongation_deg:.1f}° < '
                f'{info.threshold_deg}°) · {rules["label"]} '
                f'traditionally avoided when {graha} is combust'
            )
    return None


def _yoga_skip_reason(day, rules) -> str | None:
    skip_yogas = set(rules.get('skip_on_yoga', ()))
    if not skip_yogas:
        return None
    for yoga in day.special_yogas:
        if yoga in skip_yogas:
            return f'{yoga} · {rules["label"]} traditionally avoids this day'
    if day.yoga.name in NITYA_HARD_AVOID:
        return f'{day.yoga.name} yoga · samskaras traditionally defer'
    return None


def _day_skip_reason(
    day,
    rules,
    activity,
    travel_direction,
    janma_rasis,
    chandra_mode,
    daylight_assessment=None,
) -> str | None:
    """Return a reason string if the day should be skipped, else None.

    Covers eclipse, disha shoola, all rule-driven skips (khar maasa,
    adhika, pitru paksha, simha-stha guru, combustion, skip-on-yoga),
    and chandra_mode day-level filtering.
    """
    if day.eclipse is not None:
        kind = f'{day.eclipse.kind} eclipse'
        return f'{kind} · auspicious activities deferred'

    if daylight_assessment is not None and not daylight_assessment['admissible']:
        return karnavedha_daylight_drop_reason(daylight_assessment)

    if reason := _calendar_profile_skip_reason(day, rules):
        return reason

    if activity == 'travel' and travel_direction is not None:
        blocked = getattr(day, 'disha_shoola_direction', None)
        if blocked is not None and travel_direction == blocked:
            return (
                f'Disha Shoola ({day.vaaram}) · travel toward {blocked} '
                f'is inauspicious on this weekday'
            )

    if reason := _traditional_skip_reason(day, rules):
        return reason

    return _chandra_skip_reason(day, janma_rasis, chandra_mode)


# ---------------------------------------------------------------------------
# diagnose_day — explains why day_slots() would return []
# ---------------------------------------------------------------------------


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
    if (
        janma_nakshatras is not None
        and janma_rasis is not None
        and len(janma_nakshatras) != len(janma_rasis)
    ):
        raise ValueError(
            'janma_rasis must align with janma_nakshatras '
            '(use None for people whose rashi is unknown).'
        )
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
        activity,
        travel_direction,
        janma_rasis,
        chandra_mode,
        _daylight_assessment,
    )


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


# ---------------------------------------------------------------------------
# Slot evaluation — orchestrates all scorers for one candidate slot
# ---------------------------------------------------------------------------

_DISALLOWED_TITHI = object()


def _allowed_tithi_number(day, facts, ctx: _DayContext):
    janma_nakshatras = canonical_activity_nakshatras(ctx.janma_nakshatras or [])
    if (
        ctx.avoid_janma_nakshatra
        and ctx.janma_nakshatras
        and facts.nakshatra in janma_nakshatras
    ):
        return _DISALLOWED_TITHI
    if ctx.allowed_nakshatras and facts.nakshatra not in ctx.allowed_nakshatras:
        return _DISALLOWED_TITHI
    if facts.nakshatra in ctx.avoid_nakshatras:
        return _DISALLOWED_TITHI
    try:
        number = tithi_number(facts.tithi)
    except ValueError:
        number = None
    if ctx.allowed_tithi_numbers and number not in ctx.allowed_tithi_numbers:
        return _DISALLOWED_TITHI
    if ctx.allowed_tithi_names and facts.tithi not in ctx.allowed_tithi_names:
        return _DISALLOWED_TITHI
    if number in ctx.avoid_tithi_numbers:
        return _DISALLOWED_TITHI
    if (day.vaaram, facts.tithi) in ctx.avoid_vara_tithi_names:
        return _DISALLOWED_TITHI
    if facts.yoga in ctx.avoid_nitya_yogas:
        return _DISALLOWED_TITHI
    return number


def _personal_dosha(
    chandra_avoid_names,
    lagna_ashtama_names,
    chandra_puja_names,
    tara_unfav_names,
    special_yogas,
) -> str | None:
    if chandra_avoid_names:
        return (
            'ashtama_chandra'
            if any('Ashtama' in name for name in chandra_avoid_names)
            else 'chandra_avoid'
        )
    if lagna_ashtama_names:
        return 'ashtama_lagna'
    if chandra_puja_names:
        return 'chandra_remedial'
    rectified = any(
        yoga in ('Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga')
        for yoga in special_yogas
    )
    if tara_unfav_names and not rectified:
        return 'tara_dosha'
    return None


def _day_dosha(facts, tithi_fam, manual_prerequisites) -> str | None:
    if tithi_fam == 'Rikta':
        return 'rikta_tithi'
    if 'Amavasya' in facts.tithi:
        return 'amavasya'
    if any(yoga in YOGA_PENALTY for yoga in facts.special_yogas):
        return 'visha_dagdha_yoga'
    if facts.yoga in NITYA_HARD_AVOID:
        return 'vyatipata_vaidhriti'
    return 'practitioner_review' if manual_prerequisites else None


def _append_manual_notes(notes, day, ctx: _DayContext, cur_lagna) -> None:
    english_weekdays = {
        'Adivaram': 'Sunday',
        'Somavaram': 'Monday',
        'Mangalavaram': 'Tuesday',
        'Budhavaram': 'Wednesday',
        'Guruvaram': 'Thursday',
        'Shukravaram': 'Friday',
        'Shanivaram': 'Saturday',
    }
    current_weekday = english_weekdays.get(day.vaaram)
    for item in ctx.manual_checks:
        named_weekdays = [name for name in english_weekdays.values() if name in item]
        if not named_weekdays or current_weekday in named_weekdays:
            notes.append(f'Manual check required · {item}')
    if ctx.caution_lagna_solar and cur_lagna == day.solar_sign:
        notes.append(
            f'Source caution · {cur_lagna} Lagna is occupied by Surya; '
            'Raman associates this with delay from hard rock.'
        )


def _panchaka_penalty(facts, cur_lagna, ctx: _DayContext) -> tuple[int, str | None]:
    if cur_lagna is None:
        return 0, None
    try:
        panchaka = evaluate_panchaka(
            tithi_name=facts.tithi,
            vaaram_name=facts.vaaram,
            nakshatra_name=facts.nakshatra,
            lagna_name=cur_lagna,
        )
    except (ValueError, KeyError):
        return 0, None
    if panchaka.name == 'Mrityu':
        return -3, 'Mrityu Panchaka · universal samskara avoidance (-3)'
    if panchaka.name == 'Rahita':
        return 0, None
    activity_label = ctx.label.lower()
    for avoid_key in panchaka.avoid_for:
        configured = (
            avoid_key in ACTIVITY_RULES
            and ACTIVITY_RULES[avoid_key]['label'].lower() == activity_label
        )
        if configured or avoid_key in activity_label.replace(' ', '_'):
            return -2, (f'{panchaka.name} Panchaka conflicts with {ctx.label} (-2)')
    return 0, None


def _muhurta_nature_bonus(mu) -> int:
    if mu['is_abhijit'] or mu['is_brahma']:
        return 2
    return 1 if mu['nature'] == 'auspicious' else -2


def _activity_overlap_bonus(
    s, e, block, facts, ctx: _DayContext, slot_quality, activity_match
) -> int:
    bonus = 0
    if facts.nakshatra in ctx.prefer_nakshatras:
        bonus += 1
        activity_match.append(
            f'{facts.nakshatra} specifically favoured for {ctx.label} (+1)'
        )
    if any(_overlaps(s, e, a.start, a.end) for a in ctx.amrita):
        bonus += 2
        slot_quality.append('overlaps Amrita Kalam (+2)')
    if (
        ctx.prefer_bhadra_puchha
        and ctx.day.bhadra_puchha is not None
        and _overlaps(s, e, ctx.day.bhadra_puchha.start, ctx.day.bhadra_puchha.end)
    ):
        bonus += ctx.prefer_bhadra_puchha
        activity_match.append(f'Bhadra Puchha overlap (+{ctx.prefer_bhadra_puchha})')
    if ctx.prefer_nakshatra_mukha is not None:
        preferred_classes, mukha_bonus = ctx.prefer_nakshatra_mukha
        day_mukha = getattr(ctx.day, 'nakshatra_mukha', None)
        if day_mukha is not None and day_mukha in preferred_classes:
            bonus += mukha_bonus
            activity_match.append(f'Nakshatra Mukha {day_mukha} (+{mukha_bonus})')
    if ctx.prefer_chog and block.name == ctx.prefer_chog[0]:
        bonus += ctx.prefer_chog[1]
        activity_match.append(
            f'{block.name} favoured for {ctx.label} (+{ctx.prefer_chog[1]})'
        )
    for karana_name in ctx.avoid_karana_names:
        activity_match.append(f'{karana_name} karana avoided')
    return bonus


def _hora_bonus(s, ctx: _DayContext, activity_match) -> int:
    if not ctx.horas or not ctx.prefer_varas:
        return 0
    from telugu_panchangam.panchangam_names import VAARAM_NAMES

    ruler_indexes = {
        'Sun': 0,
        'Moon': 1,
        'Mars': 2,
        'Mercury': 3,
        'Jupiter': 4,
        'Venus': 5,
        'Saturn': 6,
    }
    for hora in ctx.horas:
        if hora.start <= s < hora.end:
            ruler_index = ruler_indexes.get(hora.name.split(' ')[0])
            if (
                ruler_index is not None
                and VAARAM_NAMES[ruler_index] in ctx.prefer_varas
            ):
                activity_match.append(f'{hora.name} favoured for {ctx.label} (+1)')
                return 1
            return 0
    return 0


_DISALLOWED_LAGNA = object()


def _lagna_score(s, ctx: _DayContext, activity_match, group_fit):
    cur_lagna = slot_lagna_name(ctx.lagnas, s)
    if ctx.allowed_lagnas and cur_lagna not in ctx.allowed_lagnas:
        return _DISALLOWED_LAGNA
    if ctx.required_lagna_class and cur_lagna not in lagnas_in_class(
        ctx.required_lagna_class
    ):
        return _DISALLOWED_LAGNA
    if ctx.required_lagna_class:
        activity_match.append(
            f'{cur_lagna} lagna satisfies required {ctx.required_lagna_class} class'
        )
    if ctx.allowed_lagnas:
        activity_match.append(f'{cur_lagna} lagna is admitted for {ctx.label}')
    bonus = 0
    if cur_lagna in ctx.prefer_lagnas:
        bonus += 1
        activity_match.append(
            f'{cur_lagna} lagna specifically favoured for {ctx.label} (+1)'
        )
    lagna_bonus, reasons, ashtama_names = score_lagna(
        ctx.janma_nakshatras,
        ctx.janma_rasis,
        cur_lagna,
        janma_lagnas=ctx.janma_lagnas,
    )
    bonus += lagna_bonus
    group_fit.extend(reasons)
    activity_bonus, activity_reason = score_lagna_activity(
        ctx.prefer_lagna_class, cur_lagna, ctx.label
    )
    if activity_reason:
        bonus += activity_bonus
        activity_match.append(activity_reason)
    return bonus, cur_lagna, ashtama_names


def _slot_quality_reasons(mu, block, base, nature_bonus) -> list[str]:
    mu_label = mu['name']
    if mu['is_abhijit']:
        mu_label += ' (Abhijit)'
    mu_deity = f' · {mu["deity"]}' if mu['deity'] else ''
    chog_desc = f'{block.name} choghadiya'
    if mu.get('chog_straddle'):
        chog_desc += f' (spans {mu["chog_straddle"]})'
    chog_line = f'{chog_desc} (+{base})' if base else chog_desc
    return [
        f'{mu_label} muhurta{mu_deity} · {mu["nature"]} ({nature_bonus:+d})',
        chog_line,
    ]


def _initial_reason_buckets(
    yoga_reasons,
    nitya_reasons,
    ctx: _DayContext,
    anandadi_reason,
    tithi_day_reason,
    election_reasons,
    tithi_activity_reason,
    preferred_number_tithi_reason,
) -> tuple[list[str], list[str]]:
    day_quality = list(yoga_reasons) + list(nitya_reasons)
    if ctx.simha_stha_shukra_penalty:
        day_quality.append(
            f'Simha-Stha Shukra (Venus in Simha) ({ctx.simha_stha_shukra_penalty})'
        )
    if anandadi_reason:
        day_quality.append(anandadi_reason)
    if tithi_day_reason:
        day_quality.append(tithi_day_reason)
    activity_match = list(election_reasons)
    if tithi_activity_reason:
        activity_match.append(tithi_activity_reason)
    if preferred_number_tithi_reason:
        activity_match.append(preferred_number_tithi_reason)
    if ctx.vara_reason:
        activity_match.append(ctx.vara_reason)
    return day_quality, activity_match


def _evaluate_slot(
    s, e, block, base, facts, ctx: _DayContext, mu, election_reasons=()
) -> dict | None:
    day = ctx.day

    active_tithi_number = _allowed_tithi_number(day, facts, ctx)
    if active_tithi_number is _DISALLOWED_TITHI:
        return None

    # Special yogas
    yoga_bonus, yoga_reasons, defer = score_special_yogas(
        facts.special_yogas, ctx.skip_yogas
    )
    if defer:
        return None

    # Tarabalam
    tara_bonus, tara_reasons, tara_unfav_names = score_tara(
        ctx.janma_nakshatras, facts.nakshatra
    )

    # Chandrabalam
    chandra_bonus, chandra_reasons, dropped, chandra_avoid_names, chandra_puja_names = (
        score_chandra(
            ctx.janma_nakshatras, ctx.janma_rasis, facts.lunar_sign, ctx.chandra_mode
        )
    )
    if dropped:
        return None

    # Tithi class (nakshatra + special_yogas enable dosha neutralization)
    tithi_bonus, tithi_day_reason, tithi_activity_reason, tithi_fam = score_tithi_class(
        facts.tithi,
        ctx.prefer_tithi_class,
        ctx.label,
        nakshatra=facts.nakshatra,
        special_yogas=facts.special_yogas,
        avoid_tithi_class=ctx.avoid_tithi_class,
    )
    preferred_number_tithi_reason = None
    if active_tithi_number in ctx.prefer_tithi_numbers:
        tithi_bonus += 1
        preferred_number_tithi_reason = (
            f'{facts.tithi} specifically favoured for {ctx.label} (+1)'
        )

    # Nitya yoga
    skip_on_nitya_hard = bool(ctx.skip_yogas)
    nitya_bonus, nitya_reasons, defer_nitya = score_nitya_yoga(
        facts.yoga, s, day, skip_on_nitya_hard
    )
    if defer_nitya:
        return None

    # Anandadi
    anandadi_bonus, anandadi_reason = anandadi_day_modifier(day)

    # Muhurta intrinsic nature (additive, disclosed): Abhijit/Brahma +2,
    # other auspicious +1, inauspicious -2.
    nature_bonus = _muhurta_nature_bonus(mu)

    score = (
        base
        + nature_bonus
        + ctx.vara_bonus
        + tara_bonus
        + chandra_bonus
        + tithi_bonus
        + yoga_bonus
        + nitya_bonus
        + ctx.simha_stha_shukra_penalty
        + anandadi_bonus
    )

    slot_quality = _slot_quality_reasons(mu, block, base, nature_bonus)
    group_fit = list(tara_reasons) + list(chandra_reasons)
    day_quality, activity_match = _initial_reason_buckets(
        yoga_reasons,
        nitya_reasons,
        ctx,
        anandadi_reason,
        tithi_day_reason,
        election_reasons,
        tithi_activity_reason,
        preferred_number_tithi_reason,
    )
    score += _activity_overlap_bonus(
        s, e, block, facts, ctx, slot_quality, activity_match
    )

    score += _hora_bonus(s, ctx, activity_match)

    lagna_result = _lagna_score(s, ctx, activity_match, group_fit)
    if lagna_result is _DISALLOWED_LAGNA:
        return None
    lagna_bonus, cur_lagna, lagna_ashtama_names = lagna_result
    score += lagna_bonus

    panchaka_penalty, panchaka_reason = _panchaka_penalty(facts, cur_lagna, ctx)
    score += panchaka_penalty
    if panchaka_reason:
        day_quality.append(panchaka_reason)

    notes = doctrinal_notes(
        special_yogas=facts.special_yogas,
        tara_unfav_names=tara_unfav_names,
        chandra_avoid_names=chandra_avoid_names,
        tithi_fam=tithi_fam,
    )
    _append_manual_notes(notes, day, ctx, cur_lagna)

    reason_groups = {
        'slot_quality': slot_quality,
        'day_quality': day_quality,
        'group_fit': group_fit,
        'activity_match': activity_match,
        'notes': notes,
    }
    reasons = slot_quality + group_fit + day_quality + activity_match

    personal_dosha = _personal_dosha(
        chandra_avoid_names,
        lagna_ashtama_names,
        chandra_puja_names,
        tara_unfav_names,
        facts.special_yogas,
    )
    day_dosha = _day_dosha(facts, tithi_fam, ctx.manual_prerequisites)

    return {
        'date': day.date.isoformat(),
        'vaaram': day.vaaram,
        'start': s,
        'end': e,
        'score': score,
        'personal_dosha': personal_dosha,
        'day_dosha': day_dosha,
        'reasons': reasons,
        'reason_groups': reason_groups,
    }


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
    if (
        janma_rasis is not None
        and janma_nakshatras is not None
        and len(janma_rasis) != len(janma_nakshatras)
    ):
        raise ValueError(
            'janma_rasis must align with janma_nakshatras '
            '(use None for people whose rashi is unknown).'
        )


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
        activity,
        travel_direction,
        janma_rasis,
        chandra_mode,
        daylight_assessment,
    )
    return daylight_assessment, reason


def _day_bad_windows(day, rules, avoid_karana_names):
    bad = _get_bad_windows(day, avoid_karana_names)
    if rules.get('skip_on_sankramana') and day.sankramana_avoidance is not None:
        bad.append((day.sankramana_avoidance.start, day.sankramana_avoidance.end))
    return bad


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

    skip_yogas = frozenset(rules.get('skip_on_yoga', ()))
    prefer_chog = rules.get('prefer_choghadiya')
    avoid_karana_names = frozenset(rules.get('avoid_karana', ()))
    prefer_tithi_class = rules.get('prefer_tithi_class')
    avoid_tithi_class = list(rules.get('avoid_tithi_class', []))
    prefer_varas = frozenset(rules.get('prefer_vara', ()))
    prefer_lagna_class = rules.get('prefer_lagna_class')
    required_lagna_class = rules.get('required_lagna_class')
    prefer_bhadra_puchha = rules.get('prefer_bhadra_puchha', 0)
    prefer_nakshatra_mukha = rules.get('prefer_nakshatra_mukha')
    allowed_nakshatras = canonical_activity_nakshatras(
        rules.get('allowed_nakshatras', ())
    )
    avoid_nakshatras = canonical_activity_nakshatras(rules.get('avoid_nakshatras', ()))
    prefer_nakshatras = canonical_activity_nakshatras(
        rules.get('prefer_nakshatras', ())
    )
    allowed_tithi_numbers = frozenset(rules.get('allowed_tithi_numbers', ()))
    prefer_tithi_numbers = frozenset(rules.get('prefer_tithi_numbers', ()))
    allowed_tithi_names = frozenset(rules.get('allowed_tithi_names', ()))
    avoid_tithi_numbers = frozenset(rules.get('avoid_tithi_numbers', ()))
    avoid_vara_tithi_names = frozenset(
        tuple(pair) for pair in rules.get('avoid_vara_tithi_names', ())
    )
    avoid_nitya_yogas = frozenset(rules.get('avoid_nitya_yogas', ()))
    allowed_lagnas = frozenset(rules.get('allowed_lagnas', ()))
    prefer_lagnas = frozenset(rules.get('prefer_lagnas', ()))
    caution_lagna_solar = bool(rules.get('caution_lagna_solar'))
    manual_checks = tuple(rules.get('manual_checks', ()))
    label = rules['label']

    _shukra_penalty = (
        rules.get('penalty_on_simha_stha_shukra', 0) if day.simha_stha_shukra else 0
    )

    vara_bonus = 1 if day.vaaram in prefer_varas else 0
    vara_reason = f'{day.vaaram} favoured for {label} (+1)' if vara_bonus else None

    bad = _day_bad_windows(day, rules, avoid_karana_names)

    ctx = _DayContext(
        day=day,
        skip_yogas=skip_yogas,
        janma_nakshatras=janma_nakshatras,
        janma_rasis=janma_rasis,
        janma_lagnas=janma_lagnas,
        chandra_mode=chandra_mode,
        prefer_tithi_class=prefer_tithi_class,
        avoid_tithi_class=avoid_tithi_class,
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
        required_lagna_class=required_lagna_class,
        prefer_bhadra_puchha=prefer_bhadra_puchha,
        simha_stha_shukra_penalty=_shukra_penalty,
        prefer_nakshatra_mukha=prefer_nakshatra_mukha,
        allowed_nakshatras=allowed_nakshatras,
        avoid_nakshatras=avoid_nakshatras,
        prefer_nakshatras=prefer_nakshatras,
        allowed_tithi_numbers=allowed_tithi_numbers,
        prefer_tithi_numbers=prefer_tithi_numbers,
        allowed_tithi_names=allowed_tithi_names,
        avoid_tithi_numbers=avoid_tithi_numbers,
        avoid_vara_tithi_names=avoid_vara_tithi_names,
        avoid_nitya_yogas=avoid_nitya_yogas,
        allowed_lagnas=allowed_lagnas,
        prefer_lagnas=prefer_lagnas,
        caution_lagna_solar=caution_lagna_solar,
        manual_checks=manual_checks,
        manual_prerequisites=bool(rules.get('manual_prerequisites')),
        avoid_janma_nakshatra=bool(rules.get('avoid_janma_nakshatra')),
    )

    engine, use_engine = _slot_engine(day, rules, engine)
    snapshot = _day_snapshot_facts(day) if not use_engine else None

    # Iterate the 15 named daytime muhurtas (sunrise->sunset /15). Each is
    # an indivisible slot: excluded if it overlaps any inauspicious window
    # (decision 1), otherwise scored — with its intrinsic nature, its
    # dominant choghadiya (a scoring attribute, straddle disclosed), and
    # all the per-slot factors. The muhurta grid coincides with the
    # engine's Abhijit/Durmuhurtham (see telugu_panchangam/muhurtas.py).
    slots = []
    solar_noon = day.sunrise + (day.sunset - day.sunrise) / 2
    for mu in named_muhurtas(day):
        s, e = mu['start'], mu['end']
        if rules.get('forenoon_only') and e > solar_noon:
            continue
        if any(_overlaps(s, e, b0, b1) for b0, b1 in bad):
            continue  # decision 1: hard-window exclude
        block, straddle = _dominant_choghadiya(s, e, day.choghadiya)
        if block is None:
            continue
        mu = {**mu, 'chog_straddle': straddle}
        base = GOOD_CHOGHADIYA.get(block.name, 0)  # bad choghadiya scores 0, not gated
        facts = (
            engine.facts_at(s, day.location, vaaram=day.vaaram)
            if use_engine
            else snapshot
        )
        election_reasons = ()
        if rules.get('require_homa_election'):
            from telugu_panchangam.personal.homa import (
                homa_election,
                solar_nakshatra_at,
            )

            admitted, election_reasons = homa_election(
                facts.tithi,
                facts.vaaram,
                facts.nakshatra,
                solar_nakshatra_at(s, engine),
            )
            if not admitted:
                continue
        slot_dict = _evaluate_slot(s, e, block, base, facts, ctx, mu, election_reasons)
        if slot_dict is not None:
            if _daylight_assessment is not None:
                slot_dict['reason_groups']['day_source_outcomes'] = (
                    _daylight_assessment['outcomes']
                )
            slots.append(slot_dict)

    assign_tiers(slots)
    slots.sort(
        key=lambda x: (
            -TIER_NAMES.index(x['tier']),
            -x['score'],
            x['personal_dosha'] is not None,
            x['start'],
        )
    )
    return slots


def _night_traditional_skip(day, rules) -> bool:
    if rules.get('skip_on_panchaka_nakshatra') and day.in_panchaka_nakshatra:
        return True
    if rules.get('skip_on_khar_maasa') and day.is_khar_maasa:
        return True
    if rules.get('skip_on_adhika') and day.maasam.startswith(_ADHIKA_PREFIX):
        return True
    if rules.get('skip_on_pitru_paksha') and day.is_pitru_paksha:
        return True
    if rules.get('skip_on_simha_stha_guru') and day.simha_stha_guru:
        return True
    return _combustion_skip_reason(day, rules) is not None


def _night_unavailable(day, rules, activity, travel_direction) -> bool:
    if day.eclipse is not None:
        return True
    if activity == 'travel' and travel_direction is not None:
        blocked = getattr(day, 'disha_shoola_direction', None)
        if blocked is not None and travel_direction == blocked:
            return True
    if rules.get('daytime_only') or rules.get('forenoon_only'):
        return True
    if _calendar_profile_skip_reason(day, rules) is not None:
        return True
    return _night_traditional_skip(day, rules)


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

    skip_yogas = set(rules.get('skip_on_yoga', ()))
    prefer_chog = rules.get('prefer_choghadiya')
    avoid_karana_names = set(rules.get('avoid_karana', ()))
    prefer_tithi_class = rules.get('prefer_tithi_class')
    avoid_tithi_class = list(rules.get('avoid_tithi_class', []))
    prefer_varas = set(rules.get('prefer_vara', ()))
    prefer_lagna_class = rules.get('prefer_lagna_class')
    required_lagna_class = rules.get('required_lagna_class')
    prefer_bhadra_puchha = rules.get('prefer_bhadra_puchha', 0)
    prefer_nakshatra_mukha = rules.get('prefer_nakshatra_mukha')
    allowed_nakshatras = canonical_activity_nakshatras(
        rules.get('allowed_nakshatras', ())
    )
    avoid_nakshatras = canonical_activity_nakshatras(rules.get('avoid_nakshatras', ()))
    prefer_nakshatras = canonical_activity_nakshatras(
        rules.get('prefer_nakshatras', ())
    )
    allowed_tithi_numbers = frozenset(rules.get('allowed_tithi_numbers', ()))
    prefer_tithi_numbers = frozenset(rules.get('prefer_tithi_numbers', ()))
    allowed_tithi_names = frozenset(rules.get('allowed_tithi_names', ()))
    avoid_tithi_numbers = frozenset(rules.get('avoid_tithi_numbers', ()))
    avoid_vara_tithi_names = frozenset(
        tuple(pair) for pair in rules.get('avoid_vara_tithi_names', ())
    )
    avoid_nitya_yogas = frozenset(rules.get('avoid_nitya_yogas', ()))
    allowed_lagnas = frozenset(rules.get('allowed_lagnas', ()))
    prefer_lagnas = frozenset(rules.get('prefer_lagnas', ()))
    caution_lagna_solar = bool(rules.get('caution_lagna_solar'))
    manual_checks = tuple(rules.get('manual_checks', ()))
    label = rules['label']

    _shukra_penalty = (
        rules.get('penalty_on_simha_stha_shukra', 0) if day.simha_stha_shukra else 0
    )

    # Vara is sunrise-anchored — carries through the night following that sunrise.
    vara_bonus = 1 if day.vaaram in prefer_varas else 0
    vara_reason = f'{day.vaaram} favoured for {label} (+1)' if vara_bonus else None

    bad = _get_bad_windows_night(day, avoid_karana_names)
    if rules.get('skip_on_sankramana') and day.sankramana_avoidance is not None:
        bad.append((day.sankramana_avoidance.start, day.sankramana_avoidance.end))

    amrita = list(day.amrita_kalam)  # absolute datetimes; night-spanning ones included

    # Nishita Kala: midpoint of night ± 1 ghati (24 min).
    _ONE_GHATI = timedelta(minutes=24)
    nishita_mid = day.sunset + (next_day.sunrise - day.sunset) / 2
    nishita_start = nishita_mid - _ONE_GHATI
    nishita_end = nishita_mid + _ONE_GHATI

    # Night choghadiya blocks (engine convention: Sunday=0).
    weekday = (day.date.weekday() + 1) % 7
    _block_dur = (next_day.sunrise - day.sunset) / 8
    night_blocks = [
        Window(
            name=_NIGHT_CHOGHADIYA[weekday][i],
            start=day.sunset + i * _block_dur,
            end=day.sunset + (i + 1) * _block_dur,
        )
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
        abhijit=None,  # no Abhijit at night
        amrita=amrita,
        prefer_chog=prefer_chog,
        avoid_karana_names=frozenset(avoid_karana_names),
        horas=horas,
        prefer_varas=frozenset(prefer_varas),
        lagnas=lagnas,
        prefer_lagna_class=prefer_lagna_class,
        required_lagna_class=required_lagna_class,
        prefer_bhadra_puchha=prefer_bhadra_puchha,
        simha_stha_shukra_penalty=_shukra_penalty,
        prefer_nakshatra_mukha=prefer_nakshatra_mukha,
        allowed_nakshatras=allowed_nakshatras,
        avoid_nakshatras=avoid_nakshatras,
        prefer_nakshatras=prefer_nakshatras,
        allowed_tithi_numbers=allowed_tithi_numbers,
        prefer_tithi_numbers=prefer_tithi_numbers,
        allowed_tithi_names=allowed_tithi_names,
        avoid_tithi_numbers=avoid_tithi_numbers,
        avoid_vara_tithi_names=avoid_vara_tithi_names,
        avoid_nitya_yogas=avoid_nitya_yogas,
        allowed_lagnas=allowed_lagnas,
        prefer_lagnas=prefer_lagnas,
        caution_lagna_solar=caution_lagna_solar,
        manual_checks=manual_checks,
        manual_prerequisites=bool(rules.get('manual_prerequisites')),
        avoid_janma_nakshatra=bool(rules.get('avoid_janma_nakshatra')),
        avoid_tithi_class=avoid_tithi_class,
    )

    engine, use_engine = _slot_engine(day, rules, engine)
    snapshot = _day_snapshot_facts(day) if not use_engine else None

    # The 15 named night muhurtas (sunset->next sunrise /15). Same model as
    # day_slots: hard-window exclude, dominant night-choghadiya, muhurta
    # nature. Brahma is now scored as the 14th night muhurta's nature; only
    # the Nishita Kala overlap remains a night-specific bonus.
    slots = []
    for mu in (m for m in named_muhurtas(day, next_day) if m['period'] == 'night'):
        s, e = mu['start'], mu['end']
        if any(_overlaps(s, e, b0, b1) for b0, b1 in bad):
            continue
        block, straddle = _dominant_choghadiya(s, e, night_blocks)
        if block is None:
            continue
        mu = {**mu, 'chog_straddle': straddle}
        base = GOOD_CHOGHADIYA.get(block.name, 0)
        facts = (
            engine.facts_at(s, day.location, vaaram=day.vaaram)
            if use_engine
            else snapshot
        )
        election_reasons = ()
        if rules.get('require_homa_election'):
            from telugu_panchangam.personal.homa import (
                homa_election,
                solar_nakshatra_at,
            )

            admitted, election_reasons = homa_election(
                facts.tithi,
                facts.vaaram,
                facts.nakshatra,
                solar_nakshatra_at(s, engine),
            )
            if not admitted:
                continue
        slot_dict = _evaluate_slot(s, e, block, base, facts, ctx, mu, election_reasons)
        if slot_dict is None:
            continue
        if _overlaps(s, e, nishita_start, nishita_end):
            slot_dict['score'] += 2
            slot_dict['reason_groups']['slot_quality'].append(
                'overlaps Nishita Kala (+2)'
            )
            slot_dict['reasons'].append('overlaps Nishita Kala (+2)')
        slots.append(slot_dict)

    assign_tiers(slots)
    slots.sort(
        key=lambda x: (
            -TIER_NAMES.index(x['tier']),
            -x['score'],
            x['personal_dosha'] is not None,
            x['start'],
        )
    )
    return slots
