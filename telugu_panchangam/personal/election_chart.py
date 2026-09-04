"""Pure evaluation of structured Muhurtam election-chart predicates."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from itertools import pairwise
from typing import Any

from .election_assessors.facts import planet_houses, planet_positions
from .election_assessors.primitives import (
    GOLD_MAX_SAMPLE_GAP_MINUTES,
    PrimitiveOutcome,
    evaluate_full_aspect,
    evaluate_well_situated,
    gold_transition_uncertainty,
)
from .election_chart_rules import ELECTION_CHART_RULES


def _evaluate_rule(
    rule: Mapping[str, Any],
    houses: Mapping[str, int] | None,
    positions: Mapping[str, Any] | None,
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    kind = rule['kind']
    if kind == 'planet_well_situated':
        return evaluate_well_situated(
            rule, positions, house_frame_uncertain=house_frame_uncertain)
    if kind == 'planet_receives_full_aspect':
        return evaluate_full_aspect(rule, positions)
    if houses is None or house_frame_uncertain:
        return PrimitiveOutcome('unknown')
    if kind == 'house_empty':
        passed = rule['house'] not in houses.values()
    elif kind == 'planet_not_house':
        passed = houses.get(rule['planet']) != rule['house']
    elif kind == 'planet_in_houses':
        passed = houses.get(rule['planet']) in rule['houses']
    elif kind == 'any_planet_in_houses':
        passed = any(houses.get(planet) in rule['houses'] for planet in rule['planets'])
    else:
        return PrimitiveOutcome('unknown')
    return PrimitiveOutcome('pass' if passed else 'fail')


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
        'convention_id', 'convention_label', 'formula', 'method_claims',
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


def _gold_transition_evidence(
    charts: list[Mapping[str, Any]],
) -> dict[str, list[str]]:
    rules = ELECTION_CHART_RULES.get('gold', ())
    evidence: dict[str, list[str]] = {}
    for start_chart, end_chart in pairwise(charts):
        start_positions = planet_positions(start_chart)
        end_positions = planet_positions(end_chart)
        if start_positions is None or end_positions is None:
            continue
        gap_minutes = _instant_minutes_between(start_chart, end_chart)
        if (
            gap_minutes is None
            or gap_minutes <= 0
            or gap_minutes > GOLD_MAX_SAMPLE_GAP_MINUTES
        ):
            for rule in rules:
                evidence.setdefault(rule['id'], []).append(
                    'The chart instants do not prove the required '
                    'ten-minute transition coverage.'
                )
            continue
        for rule in rules:
            detail = gold_transition_uncertainty(
                rule, start_positions, end_positions, gap_minutes,
            )
            if detail and detail not in evidence.setdefault(rule['id'], []):
                evidence[rule['id']].append(detail)
    return evidence


def evaluate_election_chart(
    activity: str,
    chart: Mapping[str, Any],
    *,
    house_frame_uncertain: bool = False,
) -> dict:
    """Evaluate all deterministic rules for one exact chart snapshot."""
    houses = planet_houses(chart)
    positions = planet_positions(chart)
    outcomes = [
        _outcome(rule, _evaluate_rule(
            rule,
            houses,
            positions,
            house_frame_uncertain=house_frame_uncertain,
        ))
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


def evaluate_election_snapshots(
    activity: str,
    charts: list[Mapping[str, Any]],
    *,
    house_frame_uncertain: bool = False,
) -> dict:
    """Conservatively combine all sampled states inside an offered window."""
    if not charts:
        return _summary([
            {
                'rule_id': rule['id'],
                'label': rule['label'],
                'effect': rule['effect'],
                'source_claim': rule['source_claim'],
                'source_locator': rule['source_locator'],
                'status': 'unknown',
                'evidence': [],
                **({
                    key: rule[key]
                    for key in (
                        'convention_id', 'convention_label', 'formula',
                        'method_claims', 'decision_policy_claim',
                    )
                    if key in rule
                }),
            }
            for rule in ELECTION_CHART_RULES.get(activity, ())
        ], stable=False)
    evaluations = [
        evaluate_election_chart(
            activity, chart, house_frame_uncertain=house_frame_uncertain)
        for chart in charts
    ]
    transition_evidence = (
        _gold_transition_evidence(charts) if activity == 'gold' else {}
    )
    first = evaluations[0]
    outcomes = []
    stable = True
    for first_outcome in first['outcomes']:
        statuses = [
            next(
                (item['status'] for item in result['outcomes']
                 if item['rule_id'] == first_outcome['rule_id']),
                'unknown',
            )
            for result in evaluations
        ]
        if any(status != statuses[0] for status in statuses):
            stable = False
        if first_outcome['effect'] in {'reject', 'qualify'} and 'fail' in statuses:
            status = 'fail'
        elif 'unknown' in statuses:
            status = 'unknown'
        elif first_outcome['effect'] == 'reject':
            status = 'fail' if 'fail' in statuses else 'pass'
        elif all(value == 'pass' for value in statuses):
            status = 'pass'
        elif all(value == 'fail' for value in statuses):
            status = 'fail'
        else:
            status = 'unknown'
        extra_evidence = transition_evidence.get(first_outcome['rule_id'], ())
        transition_applied = status == 'pass' and bool(extra_evidence)
        if transition_applied:
            status = 'unknown'
            stable = False
        matching = [
            next(
                (item for item in result['outcomes']
                 if item['rule_id'] == first_outcome['rule_id']),
                None,
            )
            for result in evaluations
        ]
        evidence: list[str] = []
        for item in matching:
            if not item or item['status'] != status:
                continue
            for detail in item.get('evidence', ()):
                if detail not in evidence:
                    evidence.append(detail)
                if len(evidence) == 3:
                    break
            if len(evidence) == 3:
                break
        for detail in extra_evidence:
            if not transition_applied or detail in evidence:
                continue
            evidence.append(detail)
            if len(evidence) == 3:
                break
        outcomes.append({**first_outcome, 'status': status, 'evidence': evidence})
    return _summary(outcomes, stable=stable)
