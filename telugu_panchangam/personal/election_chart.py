"""Pure evaluation of structured Muhurtam election-chart predicates."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .election_chart_rules import ELECTION_CHART_PLANETS, ELECTION_CHART_RULES


def _planet_houses(chart: Mapping[str, Any]) -> dict[str, int] | None:
    planets = chart.get('planets')
    if not isinstance(planets, list) or len(planets) != len(ELECTION_CHART_PLANETS):
        return None
    result: dict[str, int] = {}
    for item in planets:
        if not isinstance(item, Mapping):
            return None
        name, house = item.get('name'), item.get('house')
        if name not in ELECTION_CHART_PLANETS or type(house) is not int or not 1 <= house <= 12:
            return None
        if name in result:
            return None
        result[name] = house
    return result if set(result) == set(ELECTION_CHART_PLANETS) else None


def _evaluate_rule(rule: Mapping[str, Any], houses: Mapping[str, int] | None) -> str:
    if houses is None:
        return 'unknown'
    kind = rule['kind']
    if kind == 'house_empty':
        passed = rule['house'] not in houses.values()
    elif kind == 'planet_not_house':
        passed = houses.get(rule['planet']) != rule['house']
    elif kind == 'planet_in_houses':
        passed = houses.get(rule['planet']) in rule['houses']
    elif kind == 'any_planet_in_houses':
        passed = any(houses.get(planet) in rule['houses'] for planet in rule['planets'])
    else:
        return 'unknown'
    return 'pass' if passed else 'fail'


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
        'stable': stable,
    }


def evaluate_election_chart(activity: str, chart: Mapping[str, Any]) -> dict:
    """Evaluate all deterministic rules for one exact chart snapshot."""
    houses = _planet_houses(chart)
    outcomes = [
        {
            'rule_id': rule['id'],
            'label': rule['label'],
            'effect': rule['effect'],
            'source_claim': rule['source_claim'],
            'source_locator': rule['source_locator'],
            'status': _evaluate_rule(rule, houses),
        }
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
            }
            for rule in ELECTION_CHART_RULES.get(activity, ())
        ], stable=False)
    evaluations = [evaluate_election_chart(activity, chart) for chart in charts]
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
        if 'unknown' in statuses:
            status = 'unknown'
        elif first_outcome['effect'] == 'reject':
            status = 'fail' if 'fail' in statuses else 'pass'
        elif all(value == 'pass' for value in statuses):
            status = 'pass'
        elif all(value == 'fail' for value in statuses):
            status = 'fail'
        else:
            status = 'unknown'
        outcomes.append({**first_outcome, 'status': status})
    return _summary(outcomes, stable=stable)
