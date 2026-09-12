"""Pure evaluation of structured Muhurtam election-chart predicates."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from itertools import pairwise
from typing import Any

from .activity_rules import resolve_activity
from .election_assessors.chart_geometry import (
    aggregate_court_guru_trikona_window,
    evaluate_court_guru_trikona,
)
from .election_assessors.court import (
    aggregate_court_lagna_sixth_lord_separation_window,
    aggregate_court_mesha_d1_d9_window,
    aggregate_court_peace_pattern_window,
    aggregate_court_sixth_house_natural_malefic_window,
    evaluate_court_lagna_sixth_lord_separation,
    evaluate_court_mesha_d1_d9,
    evaluate_court_peace_pattern,
    evaluate_court_sixth_house_natural_malefic,
)
from .election_assessors.conjunction import (
    aggregate_same_rasi_conjunction_window,
    evaluate_same_rasi_chandra_conjunction,
)
from .election_assessors.event_admission import planet_houses, planet_positions
from .election_assessors.primitives import (
    GOLD_MAX_SAMPLE_GAP_MINUTES,
    PrimitiveOutcome,
    evaluate_all_planets_in_houses,
    evaluate_full_aspect,
    evaluate_house_free_of_natural_malefics,
    evaluate_well_situated,
    gold_transition_uncertainty,
)
from .election_chart_rules import ELECTION_CHART_RULES


def _primitive_result(
    rule: Mapping[str, Any],
    houses: Mapping[str, int] | None,
    positions: Mapping[str, Any] | None,
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome | None:
    kind = rule['kind']
    if kind == 'planet_well_situated':
        return evaluate_well_situated(
            rule, positions, house_frame_uncertain=house_frame_uncertain
        )
    if kind == 'planet_receives_full_aspect':
        return evaluate_full_aspect(rule, positions)
    if kind == 'house_free_of_natural_malefics':
        return evaluate_house_free_of_natural_malefics(
            rule, positions, house_frame_uncertain=house_frame_uncertain
        )
    if kind == 'all_planets_in_houses':
        return evaluate_all_planets_in_houses(
            rule, houses, house_frame_uncertain=house_frame_uncertain
        )
    if kind == 'same_rasi_chandra_conjunction':
        return evaluate_same_rasi_chandra_conjunction(positions)
    return None


def _house_empty_result(
    rule: Mapping[str, Any], houses: Mapping[str, int]
) -> PrimitiveOutcome:
    occupants = [name for name, house in houses.items() if house == rule['house']]
    evidence = (
        (
            f'House {rule["house"]} occupants: '
            f'{", ".join(occupants) if occupants else "none"}.'
        ),
    )
    return PrimitiveOutcome('fail' if occupants else 'pass', evidence)


def _planet_not_house_result(
    rule: Mapping[str, Any],
    houses: Mapping[str, int],
) -> PrimitiveOutcome:
    observed = houses[rule['planet']]
    passed = observed != rule['house']
    evidence = (
        f'{rule["planet"]} occupies house {observed}'
        + (f', outside house {rule["house"]}.' if passed else ', which is prohibited.'),
    )
    return PrimitiveOutcome('pass' if passed else 'fail', evidence)


def _planet_in_houses_result(
    rule: Mapping[str, Any],
    houses: Mapping[str, int],
) -> PrimitiveOutcome:
    observed = houses[rule['planet']]
    passed = observed in rule['houses']
    evidence = (
        (
            f'{rule["planet"]} occupies house {observed}; target houses: '
            f'{", ".join(str(house) for house in rule["houses"])}.'
        ),
    )
    return PrimitiveOutcome('pass' if passed else 'fail', evidence)


def _any_planet_in_houses_result(
    rule: Mapping[str, Any],
    houses: Mapping[str, int],
) -> PrimitiveOutcome:
    matching = [
        planet for planet in rule['planets'] if houses[planet] in rule['houses']
    ]
    if rule['houses'] == [1]:
        named = f'{", ".join(rule["planets"][:-1])} and {rule["planets"][-1]}'
        evidence = (
            (
                f'Lagna occupants among {named}: '
                f'{", ".join(matching) if matching else "none"}.'
            ),
        )
    else:
        evidence = (
            (
                f'Matching grahas: {", ".join(matching) if matching else "none"}; '
                f'target houses: {", ".join(str(house) for house in rule["houses"])}.'
            ),
        )
    return PrimitiveOutcome('pass' if matching else 'fail', evidence)


def _evaluate_house_rule(
    rule: Mapping[str, Any],
    houses: Mapping[str, int],
) -> PrimitiveOutcome:
    evaluators = {
        'house_empty': _house_empty_result,
        'planet_not_house': _planet_not_house_result,
        'planet_in_houses': _planet_in_houses_result,
        'any_planet_in_houses': _any_planet_in_houses_result,
    }
    evaluator = evaluators.get(rule['kind'])
    if evaluator is None:
        return PrimitiveOutcome(
            'unknown',
            (f'Unsupported election-chart rule kind: {rule["kind"]}.',),
        )
    return evaluator(rule, houses)


def _evaluate_rule(
    rule: Mapping[str, Any],
    houses: Mapping[str, int] | None,
    positions: Mapping[str, Any] | None,
    *,
    chart: Mapping[str, Any] | None = None,
    house_frame_uncertain: bool = False,
    authoritative_lagna_rashi: str | None = None,
    lagna_authority_uncertain: bool = False,
    supported_system: bool = True,
) -> PrimitiveOutcome:
    chart = chart or {}
    if not supported_system and rule.get('kind') == 'same_rasi_chandra_conjunction':
        return PrimitiveOutcome(
            'unknown',
            ('Borrowing chart screening is available only for Drik/Lahiri; systems are not blended.',),
        )
    court_evaluators = {
        'court_mesha_d1_d9': lambda: evaluate_court_mesha_d1_d9(
            chart,
            authoritative_d1_rashi=authoritative_lagna_rashi,
            lagna_authority_uncertain=lagna_authority_uncertain,
            supported_system=supported_system,
        ),
        'court_guru_trikona': lambda: evaluate_court_guru_trikona(
            chart, house_frame_uncertain=house_frame_uncertain
        ),
        'court_no_natural_malefic_h6': lambda: (
            evaluate_court_sixth_house_natural_malefic(
                chart, house_frame_uncertain=house_frame_uncertain
            )
        ),
        'court_lagna_sixth_lord_separation': lambda: (
            evaluate_court_lagna_sixth_lord_separation(
                chart,
                authoritative_lagna_rashi=authoritative_lagna_rashi or '',
                lagna_authority_uncertain=lagna_authority_uncertain,
            )
        ),
        'court_peace_pattern': lambda: evaluate_court_peace_pattern(
            chart, house_frame_uncertain=house_frame_uncertain
        ),
    }
    if evaluator := court_evaluators.get(rule['kind']):
        return evaluator()
    primitive = _primitive_result(
        rule,
        houses,
        positions,
        house_frame_uncertain=house_frame_uncertain,
    )
    if primitive is not None:
        return primitive
    if houses is None or house_frame_uncertain:
        return PrimitiveOutcome(
            'unknown', ('Complete Whole Sign house facts are unavailable.',)
        )
    return _evaluate_house_rule(rule, houses)


def _outcome(rule: Mapping[str, Any], result: PrimitiveOutcome) -> dict:
    outcome = {
        'rule_id': rule['id'],
        'label': rule['label'],
        'effect': rule['effect'],
        'source_claim': rule['source_claim'],
        'source_locator': rule['source_locator'],
        'status': result.status,
        'evidence': list(result.evidence),
    }
    for key in (
        'convention_id',
        'convention_label',
        'formula',
        'method_claims',
        'decision_policy_claim',
    ):
        if key in rule:
            outcome[key] = rule[key]
    return outcome


def _summary(outcomes: list[dict], *, stable: bool = True) -> dict:
    rejected = any(
        outcome['effect'] == 'reject' and outcome['status'] == 'fail'
        for outcome in outcomes
    )
    needs_review = any(outcome['status'] == 'unknown' for outcome in outcomes)
    return {
        'outcomes': outcomes,
        'rejected': rejected,
        'needs_review': needs_review,
        'preference_passes': sum(
            outcome['effect'] == 'prefer' and outcome['status'] == 'pass'
            for outcome in outcomes
        ),
        'qualification_failed': any(
            outcome['effect'] == 'qualify' and outcome['status'] == 'fail'
            for outcome in outcomes
        ),
        'stable': stable,
    }


def _instant_minutes_between(
    start_chart: Mapping[str, Any],
    end_chart: Mapping[str, Any],
) -> float | None:
    values = []
    for chart in (start_chart, end_chart):
        raw = chart.get('instant')
        if not isinstance(raw, str):
            return None
        try:
            parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        values.append(parsed)
    return (values[1] - values[0]).total_seconds() / 60


def _gold_pair_uncertainty(
    rules: tuple[Mapping[str, Any], ...],
    start_chart: Mapping[str, Any],
    end_chart: Mapping[str, Any],
) -> dict[str, str]:
    start_positions = planet_positions(start_chart)
    end_positions = planet_positions(end_chart)
    if start_positions is None or end_positions is None:
        return {}
    gap_minutes = _instant_minutes_between(start_chart, end_chart)
    if (
        gap_minutes is None
        or gap_minutes <= 0
        or gap_minutes > GOLD_MAX_SAMPLE_GAP_MINUTES
    ):
        detail = (
            'The chart instants do not prove the required '
            'ten-minute transition coverage.'
        )
        return {rule['id']: detail for rule in rules}
    return {
        rule['id']: detail
        for rule in rules
        if (
            detail := gold_transition_uncertainty(
                rule, start_positions, end_positions, gap_minutes
            )
        )
    }


def _gold_transition_evidence(
    charts: list[Mapping[str, Any]],
) -> dict[str, list[str]]:
    rules = ELECTION_CHART_RULES.get('gold', ())
    evidence: dict[str, list[str]] = {}
    for start_chart, end_chart in pairwise(charts):
        for rule_id, detail in _gold_pair_uncertainty(
            rules, start_chart, end_chart
        ).items():
            if detail and detail not in evidence.setdefault(rule_id, []):
                evidence[rule_id].append(detail)
    return evidence


def evaluate_election_chart(
    activity: str,
    chart: Mapping[str, Any],
    *,
    house_frame_uncertain: bool = False,
    authoritative_lagna_rashi: str | None = None,
    lagna_authority_uncertain: bool = False,
    supported_system: bool = True,
) -> dict:
    """Evaluate all deterministic rules for one exact chart snapshot."""
    activity = resolve_activity(activity)
    houses = planet_houses(chart)
    positions = planet_positions(chart)
    outcomes = [
        _outcome(
            rule,
            _evaluate_rule(
                rule,
                houses,
                positions,
                chart=chart,
                house_frame_uncertain=house_frame_uncertain,
                authoritative_lagna_rashi=authoritative_lagna_rashi,
                lagna_authority_uncertain=lagna_authority_uncertain,
                supported_system=supported_system,
            ),
        )
        for rule in ELECTION_CHART_RULES.get(activity, ())
    ]
    return _summary(outcomes)


def evaluate_election_window(
    activity: str,
    start_chart: Mapping[str, Any],
    end_chart: Mapping[str, Any],
) -> dict:
    """Compatibility wrapper for a two-snapshot offered window."""
    return evaluate_election_snapshots(activity, [start_chart, end_chart])


def _unknown_summary(activity: str) -> dict:
    activity = resolve_activity(activity)
    outcomes = []
    for rule in ELECTION_CHART_RULES.get(activity, ()):
        outcome = {
            'rule_id': rule['id'],
            'label': rule['label'],
            'effect': rule['effect'],
            'source_claim': rule['source_claim'],
            'source_locator': rule['source_locator'],
            'status': 'unknown',
            'evidence': [],
        }
        for key in (
            'convention_id',
            'convention_label',
            'formula',
            'method_claims',
            'decision_policy_claim',
        ):
            if key in rule:
                outcome[key] = rule[key]
        outcomes.append(outcome)
    return _summary(outcomes, stable=False)


def _matching_outcomes(start_item: dict, evaluations: list[dict]) -> list[dict | None]:
    return [
        next(
            (
                item
                for item in result['outcomes']
                if item['rule_id'] == start_item['rule_id']
            ),
            None,
        )
        for result in evaluations
    ]


def _combined_election_status(effect: str, statuses: list[str]) -> str:
    if effect in {'reject', 'qualify'} and 'fail' in statuses:
        return 'fail'
    if 'unknown' in statuses:
        return 'unknown'
    if effect == 'reject':
        return 'pass'
    if all(value == 'pass' for value in statuses):
        return 'pass'
    if all(value == 'fail' for value in statuses):
        return 'fail'
    return 'unknown'


def _observed_evidence(
    matching: list[dict | None],
    status: str,
) -> list[str]:
    evidence = []
    for item in matching:
        if item and item['status'] == status:
            for detail in item.get('evidence', ()):
                if detail not in evidence:
                    evidence.append(detail)
                if len(evidence) == 3:
                    return evidence
    return evidence


def _with_transition_evidence(
    evidence: list[str],
    extra_evidence: list[str] | tuple[str, ...],
    transition_applied: bool,
) -> list[str]:
    if not transition_applied:
        return evidence
    for detail in extra_evidence:
        if detail not in evidence:
            evidence.append(detail)
        if len(evidence) == 3:
            break
    return evidence


def _combined_chart_outcome(
    start_item: dict,
    evaluations: list[dict],
    transition_evidence: dict[str, list[str]],
) -> tuple[dict, bool]:
    matching = _matching_outcomes(start_item, evaluations)
    statuses = [item['status'] if item is not None else 'unknown' for item in matching]
    status = _combined_election_status(start_item['effect'], statuses)
    extra = transition_evidence.get(start_item['rule_id'], ())
    transition_applied = status == 'pass' and bool(extra)
    if transition_applied:
        status = 'unknown'
    evidence = _observed_evidence(matching, status)
    evidence = _with_transition_evidence(evidence, extra, transition_applied)
    stable = not transition_applied and all(value == statuses[0] for value in statuses)
    return {**start_item, 'status': status, 'evidence': evidence}, stable


def _court_sample_outcomes(
    first_item: dict,
    evaluations: list[dict],
) -> list[PrimitiveOutcome]:
    return [
        PrimitiveOutcome(
            item['status'] if item is not None else 'unknown',
            tuple(item.get('evidence', ())) if item is not None else (),
        )
        for item in _matching_outcomes(first_item, evaluations)
    ]


def _coverage_value(coverage: Mapping[str, Any], key: str) -> Any:
    return coverage.get(key, False)


def _aggregate_court_rule(
    rule_id: str,
    samples: list[PrimitiveOutcome],
    coverage: Mapping[str, Any],
) -> PrimitiveOutcome:
    budget_exhausted = _coverage_value(coverage, 'budget_exhausted')
    local_lagna = _coverage_value(
        coverage, 'local_lagna_transitions_complete'
    )
    if rule_id == 'court.mesha-lagna-or-navamsa':
        return aggregate_court_mesha_d1_d9_window(
            samples,
            local_lagna_transitions_complete=local_lagna,
            lagna_navamsa_transitions_complete=_coverage_value(
                coverage, 'lagna_navamsa_transitions_complete'
            ),
            budget_exhausted=budget_exhausted,
        )
    if rule_id == 'court.guru-trikona':
        return aggregate_court_guru_trikona_window(
            samples,
            local_lagna_transitions_complete=local_lagna,
            guru_rasi_transitions_complete=_coverage_value(
                coverage, 'guru_rasi_transitions_complete'
            ),
            budget_exhausted=budget_exhausted,
        )
    if rule_id == 'court.house-6-without-natural-malefic':
        return aggregate_court_sixth_house_natural_malefic_window(
            samples,
            local_lagna_transitions_complete=local_lagna,
            graha_rasi_transitions_complete=_coverage_value(
                coverage, 'graha_rasi_transitions_complete'
            ),
            chandra_phase_transitions_complete=_coverage_value(
                coverage, 'chandra_phase_transitions_complete'
            ),
            budha_association_transitions_complete=_coverage_value(
                coverage, 'budha_association_transitions_complete'
            ),
            budget_exhausted=budget_exhausted,
        )
    if rule_id == 'court.lagna-sixth-lords-max-separated':
        return aggregate_court_lagna_sixth_lord_separation_window(
            samples,
            local_lagna_transitions_complete=local_lagna,
            lagna_lord_rasi_transitions_complete=_coverage_value(
                coverage, 'lagna_lord_rasi_transitions_complete'
            ),
            sixth_lord_rasi_transitions_complete=_coverage_value(
                coverage, 'sixth_lord_rasi_transitions_complete'
            ),
            budget_exhausted=budget_exhausted,
        )
    return aggregate_court_peace_pattern_window(
        samples,
        local_lagna_transitions_complete=local_lagna,
        graha_rasi_transitions_complete=_coverage_value(
            coverage, 'graha_rasi_transitions_complete'
        ),
        chandra_phase_transitions_complete=_coverage_value(
            coverage, 'chandra_phase_transitions_complete'
        ),
        budha_association_transitions_complete=_coverage_value(
            coverage, 'budha_association_transitions_complete'
        ),
        full_aspect_transitions_complete=_coverage_value(
            coverage, 'full_aspect_transitions_complete'
        ),
        budget_exhausted=budget_exhausted,
    )


def _court_window_summary(
    evaluations: list[dict],
    coverage: Mapping[str, Any],
) -> dict:
    first = evaluations[0]
    outcomes = []
    stable = True
    for first_item in first['outcomes']:
        samples = _court_sample_outcomes(first_item, evaluations)
        result = _aggregate_court_rule(first_item['rule_id'], samples, coverage)
        observed_statuses = [sample.status for sample in samples]
        stable = stable and result.status != 'unknown' and all(
            status == observed_statuses[0] for status in observed_statuses
        )
        outcomes.append(_outcome(
            {
                'id': first_item['rule_id'],
                'label': first_item['label'],
                'effect': first_item['effect'],
                'source_claim': first_item['source_claim'],
                'source_locator': first_item['source_locator'],
                **{
                    key: first_item[key]
                    for key in (
                        'convention_id', 'convention_label', 'formula',
                        'method_claims', 'decision_policy_claim',
                    )
                    if key in first_item
                },
            },
            result,
        ))
    return _summary(outcomes, stable=stable)


def _borrowing_window_summary(
    evaluations: list[dict],
    coverage: Mapping[str, Any],
) -> dict:
    first_item = evaluations[0]['outcomes'][0]
    samples = _court_sample_outcomes(first_item, evaluations)
    result = aggregate_same_rasi_conjunction_window(
        samples,
        transition_complete=bool(coverage.get('rasi_transitions_complete')),
        budget_exhausted=bool(coverage.get('budget_exhausted')),
    )
    outcome = _outcome(
        {
            'id': first_item['rule_id'],
            'label': first_item['label'],
            'effect': first_item['effect'],
            'source_claim': first_item['source_claim'],
            'source_locator': first_item['source_locator'],
            **{
                key: first_item[key]
                for key in (
                    'convention_id', 'convention_label', 'formula',
                    'method_claims', 'decision_policy_claim',
                )
                if key in first_item
            },
        },
        result,
    )
    stable = result.status != 'unknown' and all(
        sample.status == samples[0].status for sample in samples
    )
    return _summary([outcome], stable=stable)


def evaluate_election_snapshots(
    activity: str,
    charts: list[Mapping[str, Any]],
    *,
    house_frame_uncertain: bool = False,
    authoritative_lagna_rashis: list[str | None] | None = None,
    lagna_authority_uncertain: bool = False,
    supported_system: bool = True,
    court_transition_coverage: Mapping[str, Any] | None = None,
    borrowing_transition_coverage: Mapping[str, Any] | None = None,
) -> dict:
    """Conservatively combine all sampled states inside an offered window."""
    activity = resolve_activity(activity)
    if not charts:
        return _unknown_summary(activity)
    lagna_rashis = authoritative_lagna_rashis or [None] * len(charts)
    if len(lagna_rashis) != len(charts):
        lagna_rashis = [None] * len(charts)
    evaluations = [
        evaluate_election_chart(
            activity,
            chart,
            house_frame_uncertain=house_frame_uncertain,
            authoritative_lagna_rashi=lagna_rashis[index],
            lagna_authority_uncertain=lagna_authority_uncertain,
            supported_system=supported_system,
        )
        for index, chart in enumerate(charts)
    ]
    if activity == 'court':
        return _court_window_summary(
            evaluations,
            court_transition_coverage
            if isinstance(court_transition_coverage, Mapping)
            else {},
        )
    if activity == 'borrowing_money':
        return _borrowing_window_summary(
            evaluations,
            borrowing_transition_coverage
            if isinstance(borrowing_transition_coverage, Mapping)
            else {},
        )
    transition_evidence = (
        _gold_transition_evidence(charts) if activity == 'gold' else {}
    )
    first = evaluations[0]
    outcomes = []
    stable = True
    for first_outcome in first['outcomes']:
        matching = _matching_outcomes(first_outcome, evaluations)
        statuses = [
            item['status'] if item is not None else 'unknown' for item in matching
        ]
        stable = stable and all(value == statuses[0] for value in statuses)
        status = _combined_election_status(first_outcome['effect'], statuses)
        extra_evidence = transition_evidence.get(first_outcome['rule_id'], ())
        transition_applied = status == 'pass' and bool(extra_evidence)
        if transition_applied:
            status = 'unknown'
            stable = False
        evidence = _observed_evidence(matching, status)
        evidence = _with_transition_evidence(
            evidence, extra_evidence, transition_applied
        )
        outcomes.append({**first_outcome, 'status': status, 'evidence': evidence})
    return _summary(outcomes, stable=stable)
