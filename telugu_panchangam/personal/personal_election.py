"""Pure, source-backed personal predicates for candidate Muhurtam windows.

Only bounded natal facts already held in the browser are represented here.
The matching TypeScript evaluator is parity-tested against these outcomes;
neither implementation transmits a profile or treats a natal chart as the
candidate election chart.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES, RASHI_NAMES

LOCATORS = {
    'travel': "Chapter XIV, 'Journeys' and 'Long-distance Journeys,' printed pp. 60-61 (PDF pp. 64-65)",
    'gruhapravesha': "Chapter XII, 'House building,' section 'Entering a new house,' printed pp. 52-54 (PDF pp. 56-58)",
    'seemantha': "Chapter VII, 'Seemantha,' printed pp. 20-21 (PDF pp. 24-25)",
    'surgery': "Chapter XV, 'Surgical Operations,' printed pp. 64-65 (PDF pp. 68-69)",
}

PERSONAL_ELECTION_RULES = {
    'travel': (
        ('personal.travel.lagna-exclusions', 'reject', 'muhurta.travel', LOCATORS['travel']),
        ('personal.travel.janma-rashi-lagna', 'prefer', 'muhurta.travel', LOCATORS['travel']),
    ),
    'gruhapravesha': (
        ('personal.gruhapravesha.natal-anchor-match', 'prefer', 'muhurta.gruhapravesha', LOCATORS['gruhapravesha']),
    ),
    'seemantha': (
        ('personal.seemantha.birth-star-exclusions', 'reject', 'muhurta.seemantha', LOCATORS['seemantha']),
    ),
    'surgery': (
        ('personal.surgery.chandra-outside-janma-rashi', 'reject', 'muhurta.surgery', LOCATORS['surgery']),
    ),
}


def _position(order: list[str], origin: str | None, target: str | None) -> int | None:
    if origin not in order or target not in order:
        return None
    return (order.index(target) - order.index(origin)) % len(order) + 1


def _result(activity: str, outcomes: list[dict], *, stable: bool = True) -> dict:
    return {
        'outcomes': outcomes,
        'rejected': any(
            item['effect'] == 'reject' and item['status'] == 'fail'
            for item in outcomes
        ),
        'needs_review': any(item['status'] == 'unknown' for item in outcomes),
        'preference_passes': sum(
            item['effect'] == 'prefer' and item['status'] == 'pass'
            for item in outcomes
        ),
        'stable': stable,
    }


def _outcome(activity: str, index: int, status: str, inputs: dict) -> dict:
    rule_id, effect, source_claim, source_locator = PERSONAL_ELECTION_RULES[activity][index]
    return {
        'rule_id': rule_id,
        'effect': effect,
        'source_claim': source_claim,
        'source_locator': source_locator,
        'status': status,
        'inputs': inputs,
    }


def evaluate_personal_election(
    activity: str,
    participant: Mapping[str, Any] | None,
    facts: Mapping[str, Any],
) -> dict:
    """Evaluate one boundary without inventing missing natal facts."""
    if activity not in PERSONAL_ELECTION_RULES:
        return _result(activity, [])
    if participant is None:
        return _result(activity, [
            _outcome(activity, index, 'unknown', {'participant_selected': False})
            for index in range(len(PERSONAL_ELECTION_RULES[activity]))
        ])

    if activity == 'travel':
        position = _position(
            RASHI_NAMES, participant.get('janma_lagna'), facts.get('lagna'))
        excluded = position in {1, 5, 7, 9} if position is not None else None
        lagna_status = 'unknown' if excluded is None else ('fail' if excluded else 'pass')
        rashi = participant.get('janma_rashi')
        candidate_lagna = facts.get('lagna')
        rashi_status = (
            'unknown' if not rashi or not candidate_lagna
            else 'pass' if rashi == candidate_lagna
            else 'fail'
        )
        return _result(activity, [
            _outcome(activity, 0, lagna_status, {
                'janma_lagna': participant.get('janma_lagna'),
                'candidate_lagna': candidate_lagna,
                'position': position,
            }),
            _outcome(activity, 1, rashi_status, {
                'janma_rashi': rashi,
                'candidate_lagna': candidate_lagna,
            }),
        ])

    if activity == 'gruhapravesha':
        anchors = (
            (participant.get('nakshatra'), facts.get('nakshatra')),
            (participant.get('janma_rashi'), facts.get('lunar_rashi')),
            (participant.get('janma_lagna'), facts.get('lagna')),
        )
        matches = any(origin and origin == target for origin, target in anchors)
        all_resolved = all(origin and target for origin, target in anchors)
        status = 'pass' if matches else ('fail' if all_resolved else 'unknown')
        return _result(activity, [_outcome(activity, 0, status, {
            'janma_nakshatra': participant.get('nakshatra'),
            'candidate_nakshatra': facts.get('nakshatra'),
            'janma_rashi': participant.get('janma_rashi'),
            'candidate_chandra_rashi': facts.get('lunar_rashi'),
            'janma_lagna': participant.get('janma_lagna'),
            'candidate_lagna': facts.get('lagna'),
        })])

    if activity == 'seemantha':
        position = _position(
            NAKSHATRA_NAMES, participant.get('nakshatra'), facts.get('nakshatra'))
        excluded = position in {3, 7, 8, 10, 22} if position is not None else None
        status = 'unknown' if excluded is None else ('fail' if excluded else 'pass')
        return _result(activity, [_outcome(activity, 0, status, {
            'janma_nakshatra': participant.get('nakshatra'),
            'candidate_nakshatra': facts.get('nakshatra'),
            'position': position,
        })])

    janma_rashi = participant.get('janma_rashi')
    candidate_rashi = facts.get('lunar_rashi')
    status = (
        'unknown' if not janma_rashi or not candidate_rashi
        else 'fail' if janma_rashi == candidate_rashi
        else 'pass'
    )
    return _result(activity, [_outcome(activity, 0, status, {
        'janma_rashi': janma_rashi,
        'candidate_chandra_rashi': candidate_rashi,
    })])


def evaluate_personal_election_window(
    activity: str,
    participant: Mapping[str, Any] | None,
    start_facts: Mapping[str, Any],
    end_facts: Mapping[str, Any],
) -> dict:
    """Compatibility wrapper for a two-snapshot offered window."""
    result = evaluate_personal_election_snapshots(
        activity, participant, [start_facts, end_facts])
    for outcome in result['outcomes']:
        outcome['inputs'] = {
            'start': outcome['inputs']['start'],
            'end': outcome['inputs']['end'],
        }
    return result


def evaluate_personal_election_snapshots(
    activity: str,
    participant: Mapping[str, Any] | None,
    facts: list[Mapping[str, Any]],
) -> dict:
    """Conservatively combine all sampled personal election states."""
    samples = facts or [{'nakshatra': '', 'lunar_rashi': None, 'lagna': None}]
    evaluations = [
        evaluate_personal_election(activity, participant, item)
        for item in samples
    ]
    start = evaluations[0]
    outcomes = []
    stable = bool(facts)
    for start_item in start['outcomes']:
        boundary_items = [
            next(
                (item for item in result['outcomes']
                 if item['rule_id'] == start_item['rule_id']),
                None,
            )
            for result in evaluations
        ]
        statuses = [
            item['status'] if item is not None else 'unknown'
            for item in boundary_items
        ]
        if 'unknown' in statuses:
            status = 'unknown'
        elif start_item['effect'] == 'reject':
            status = 'fail' if 'fail' in statuses else 'pass'
        elif all(value == 'pass' for value in statuses):
            status = 'pass'
        elif all(value == 'fail' for value in statuses):
            status = 'fail'
        else:
            status = 'unknown'
        stable = stable and all(value == statuses[0] for value in statuses)
        outcomes.append({
            **start_item,
            'status': status,
            'inputs': {
                'start': boundary_items[0]['inputs'] if boundary_items[0] else None,
                'end': boundary_items[-1]['inputs'] if boundary_items[-1] else None,
                'boundaries': [
                    item['inputs'] if item else None for item in boundary_items
                ],
            },
        })
    return _result(activity, outcomes, stable=stable)
