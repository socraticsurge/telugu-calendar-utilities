"""Compose atomic scorer contributions for one candidate window."""

from dataclasses import dataclass
from datetime import datetime

from telugu_panchangam.models.panchangam_day import SlotFacts, Window
from telugu_panchangam.panchaka import evaluate_panchaka
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.lagna_position import lagnas_in_class
from telugu_panchangam.personal.muhurta_eligibility import (
    _DISALLOWED_TITHI,
    _allowed_tithi_number,
    _overlaps,
)
from telugu_panchangam.personal.muhurta_explanations import (
    _append_manual_notes,
    _CalendarReasons,
    _day_dosha,
    _initial_reason_buckets,
    _personal_dosha,
    _slot_quality_reasons,
)
from telugu_panchangam.personal.search_contract import (
    LagnaContribution,
    ScoreContribution,
)
from telugu_panchangam.personal.slot_scorers import (
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

_DISALLOWED_LAGNA = object()


@dataclass(frozen=True)
class _SlotCandidate:
    start: datetime
    end: datetime
    block: Window
    base: int
    facts: SlotFacts
    muhurta: dict


@dataclass
class _CalendarScore:
    score: int
    day_quality: list[str]
    activity_match: list[str]
    group_fit: list[str]
    tara_unfav_names: list[str]
    chandra_avoid_names: list[str]
    chandra_puja_names: list[str]
    tithi_fam: str | None


def _panchaka_conflicts(avoid_key, activity_label):
    profile = ACTIVITY_RULES.get(avoid_key)
    configured_label = profile['label'].lower() if profile is not None else None
    return configured_label == activity_label or avoid_key in activity_label.replace(
        ' ', '_'
    )


def _panchaka_penalty(facts, cur_lagna, ctx: _DayContext) -> tuple[int, str | None]:
    if cur_lagna is None:
        return 0, None
    panchaka = _panchaka_at(facts, cur_lagna)
    if panchaka is None:
        return 0, None
    if panchaka.name == 'Mrityu':
        return -3, 'Mrityu Panchaka · universal samskara avoidance (-3)'
    if panchaka.name == 'Rahita':
        return 0, None
    activity_label = ctx.label.lower()
    for avoid_key in panchaka.avoid_for:
        if _panchaka_conflicts(avoid_key, activity_label):
            return -2, (f'{panchaka.name} Panchaka conflicts with {ctx.label} (-2)')
    return 0, None


def _panchaka_at(facts, cur_lagna):
    try:
        return evaluate_panchaka(
            tithi_name=facts.tithi,
            vaaram_name=facts.vaaram,
            nakshatra_name=facts.nakshatra,
            lagna_name=cur_lagna,
        )
    except (ValueError, KeyError):
        return None


def _muhurta_nature_bonus(mu) -> int:
    if mu['is_abhijit'] or mu['is_brahma']:
        return 2
    return 1 if mu['nature'] == 'auspicious' else -2


def _bhadra_overlap_bonus(s, e, ctx):
    window = ctx.day.bhadra_puchha
    if not ctx.prefer_bhadra_puchha or window is None:
        return ScoreContribution()
    if not _overlaps(s, e, window.start, window.end):
        return ScoreContribution()
    return ScoreContribution(
        ctx.prefer_bhadra_puchha,
        activity_match=(f'Bhadra Puchha overlap (+{ctx.prefer_bhadra_puchha})',),
    )


def _nakshatra_mukha_bonus(ctx):
    if ctx.prefer_nakshatra_mukha is None:
        return ScoreContribution()
    preferred_classes, bonus = ctx.prefer_nakshatra_mukha
    mukha = getattr(ctx.day, 'nakshatra_mukha', None)
    if mukha is None or mukha not in preferred_classes:
        return ScoreContribution()
    return ScoreContribution(
        bonus, activity_match=(f'Nakshatra Mukha {mukha} (+{bonus})',)
    )


def _nakshatra_preference(nakshatra, ctx):
    if nakshatra in ctx.prefer_nakshatras:
        return ScoreContribution(
            1,
            activity_match=(f'{nakshatra} specifically favoured for {ctx.label} (+1)',),
        )
    return ScoreContribution()


def _amrita_overlap_bonus(s, e, ctx):
    if any(_overlaps(s, e, a.start, a.end) for a in ctx.amrita):
        return ScoreContribution(2, slot_quality=('overlaps Amrita Kalam (+2)',))
    return ScoreContribution()


def _choghadiya_preference(block, ctx):
    if ctx.prefer_chog and block.name == ctx.prefer_chog[0]:
        return ScoreContribution(
            ctx.prefer_chog[1],
            activity_match=(
                f'{block.name} favoured for {ctx.label} (+{ctx.prefer_chog[1]})',
            ),
        )
    return ScoreContribution()


def _activity_overlap_bonus(candidate, ctx: _DayContext) -> ScoreContribution:
    s, e = candidate.start, candidate.end
    contributions = (
        _nakshatra_preference(candidate.facts.nakshatra, ctx),
        _amrita_overlap_bonus(s, e, ctx),
        _bhadra_overlap_bonus(s, e, ctx),
        _nakshatra_mukha_bonus(ctx),
        _choghadiya_preference(candidate.block, ctx),
    )
    slot_quality, activity_match = [], []
    bonus = 0
    for contribution in contributions:
        bonus += contribution.score
        slot_quality.extend(contribution.slot_quality)
        activity_match.extend(contribution.activity_match)
    for karana_name in ctx.avoid_karana_names:
        activity_match.append(f'{karana_name} karana avoided')
    return ScoreContribution(bonus, tuple(slot_quality), tuple(activity_match))


def _hora_bonus(s, ctx: _DayContext) -> ScoreContribution:
    if not ctx.horas or not ctx.prefer_varas:
        return ScoreContribution()
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
                return ScoreContribution(
                    1, activity_match=(f'{hora.name} favoured for {ctx.label} (+1)',)
                )
            return ScoreContribution()
    return ScoreContribution()


def _lagna_admitted(cur_lagna, ctx):
    if ctx.allowed_lagnas and cur_lagna not in ctx.allowed_lagnas:
        return False
    if ctx.required_lagna_class:
        return cur_lagna in lagnas_in_class(ctx.required_lagna_class)
    return True


def _lagna_score(s, ctx: _DayContext):
    activity_match, group_fit = [], []
    cur_lagna = slot_lagna_name(ctx.lagnas, s)
    if not _lagna_admitted(cur_lagna, ctx):
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
    return LagnaContribution(
        ScoreContribution(
            bonus, activity_match=tuple(activity_match), group_fit=tuple(group_fit)
        ),
        cur_lagna,
        tuple(ashtama_names),
    )


def _preferred_tithi(number, name, ctx):
    if number in ctx.prefer_tithi_numbers:
        return 1, f'{name} specifically favoured for {ctx.label} (+1)'
    return 0, None


def _calendar_score(s, facts, ctx: _DayContext, election_reasons):
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
    preference_bonus, preferred_number_tithi_reason = _preferred_tithi(
        active_tithi_number, facts.tithi, ctx
    )
    tithi_bonus += preference_bonus

    # Nitya yoga
    skip_on_nitya_hard = bool(ctx.skip_yogas)
    nitya_bonus, nitya_reasons, defer_nitya = score_nitya_yoga(
        facts.yoga, s, day, skip_on_nitya_hard
    )
    if defer_nitya:
        return None

    # Anandadi
    anandadi_bonus, anandadi_reason = anandadi_day_modifier(day)

    day_quality, activity_match = _initial_reason_buckets(
        ctx,
        _CalendarReasons(
            yoga_reasons,
            nitya_reasons,
            anandadi_reason,
            tithi_day_reason,
            election_reasons,
            tithi_activity_reason,
            preferred_number_tithi_reason,
        ),
    )
    return _CalendarScore(
        ctx.vara_bonus
        + tara_bonus
        + chandra_bonus
        + tithi_bonus
        + yoga_bonus
        + nitya_bonus
        + ctx.simha_stha_shukra_penalty
        + anandadi_bonus,
        day_quality,
        activity_match,
        list(tara_reasons) + list(chandra_reasons),
        tara_unfav_names,
        chandra_avoid_names,
        chandra_puja_names,
        tithi_fam,
    )


def _evaluate_slot(
    candidate: _SlotCandidate, ctx: _DayContext, election_reasons=()
) -> dict | None:
    day = ctx.day
    s, e, facts = candidate.start, candidate.end, candidate.facts
    mu, block, base = candidate.muhurta, candidate.block, candidate.base
    calendar = _calendar_score(s, facts, ctx, election_reasons)
    if calendar is None:
        return None
    nature_bonus = _muhurta_nature_bonus(mu)
    score = base + nature_bonus + calendar.score
    slot_quality = _slot_quality_reasons(mu, block, base, nature_bonus)
    group_fit = calendar.group_fit
    day_quality, activity_match = calendar.day_quality, calendar.activity_match
    overlap = _activity_overlap_bonus(candidate, ctx)
    hora = _hora_bonus(s, ctx)
    score += overlap.score + hora.score
    slot_quality.extend(overlap.slot_quality)
    activity_match.extend(overlap.activity_match + hora.activity_match)

    lagna_result = _lagna_score(s, ctx)
    if lagna_result is _DISALLOWED_LAGNA:
        return None
    cur_lagna, lagna_ashtama_names = lagna_result.lagna, lagna_result.ashtama_names
    score += lagna_result.contribution.score
    activity_match.extend(lagna_result.contribution.activity_match)
    group_fit.extend(lagna_result.contribution.group_fit)

    panchaka_penalty, panchaka_reason = _panchaka_penalty(facts, cur_lagna, ctx)
    score += panchaka_penalty
    if panchaka_reason:
        day_quality.append(panchaka_reason)

    notes = doctrinal_notes(
        special_yogas=facts.special_yogas,
        tara_unfav_names=calendar.tara_unfav_names,
        chandra_avoid_names=calendar.chandra_avoid_names,
        tithi_fam=calendar.tithi_fam,
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
        (calendar.chandra_avoid_names, calendar.chandra_puja_names),
        lagna_ashtama_names,
        calendar.tara_unfav_names,
        facts.special_yogas,
    )
    day_dosha = _day_dosha(facts, calendar.tithi_fam, ctx.manual_prerequisites)

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
