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
    'travel': (
        "B. V. Raman, Chapter XIV, 'Journeys' and 'Long-distance Journeys,' "
        'inspected in the 2020 Chistabo derivative at internal printed '
        'pp. 60-61 (physical PDF pp. 64-65)'
    ),
    'gruhapravesha': (
        "B. V. Raman, Chapter XII, 'House building,' section 'Entering a "
        "new house,' inspected in the 2020 Chistabo derivative at internal "
        'printed pp. 52-54 (physical PDF pp. 56-58)'
    ),
    'seemantha': (
        "B. V. Raman, Chapter VII-VIII transition, 'Seemantha,' inspected "
        'in the 2020 Chistabo derivative at internal printed pp. 21-22 '
        '(physical PDF pp. 24-25)'
    ),
    'surgery': (
        "B. V. Raman, Chapter XV, 'Surgical Operations,' inspected in the "
        '2020 Chistabo derivative at internal printed pp. 64-65 '
        '(physical PDF pp. 68-69)'
    ),
    'borrowing_money': (
        "B. V. Raman, Chapter X, 'Borrowing Money,' inspected in the 2020 "
        'Chistabo derivative at internal printed p. 45 (physical PDF p. 49)'
    ),
}

PERSONAL_ELECTION_RULES = {
    'travel': (
        (
            'personal.travel.lagna-exclusions',
            'reject',
            'muhurta.travel',
            LOCATORS['travel'],
        ),
        (
            'personal.travel.janma-rashi-lagna',
            'prefer',
            'muhurta.travel',
            LOCATORS['travel'],
        ),
    ),
    'gruhapravesha': (
        (
            'personal.gruhapravesha.natal-anchor-match',
            'prefer',
            'muhurta.gruhapravesha',
            LOCATORS['gruhapravesha'],
        ),
    ),
    'seemantha': (
        (
            'personal.seemantha.birth-star-exclusions',
            'reject',
            'muhurta.seemantha',
            LOCATORS['seemantha'],
        ),
    ),
    'surgery': (
        (
            'personal.surgery.chandra-outside-janma-rashi',
            'reject',
            'muhurta.surgery',
            LOCATORS['surgery'],
        ),
    ),
    'borrowing_money': (
        (
            'personal.borrowing.primary-borrower-janma-nakshatra',
            'reject',
            'muhurta.borrowing_money',
            LOCATORS['borrowing_money'],
        ),
    ),
}


def _position(order: list[str], origin: str | None, target: str | None) -> int | None:
    if origin not in order or target not in order:
        return None
    return (order.index(target) - order.index(origin)) % len(order) + 1


def _result(outcomes: list[dict], *, stable: bool = True) -> dict:
    return {
        'outcomes': outcomes,
        'rejected': any(
            item['effect'] == 'reject' and item['status'] == 'fail' for item in outcomes
        ),
        'needs_review': any(item['status'] == 'unknown' for item in outcomes),
        'preference_passes': sum(
            item['effect'] == 'prefer' and item['status'] == 'pass' for item in outcomes
        ),
        'stable': stable,
    }


def _outcome(activity: str, index: int, status: str, inputs: dict) -> dict:
    rule_id, effect, source_claim, source_locator = PERSONAL_ELECTION_RULES[activity][
        index
    ]
    return {
        'rule_id': rule_id,
        'effect': effect,
        'source_claim': source_claim,
        'source_locator': source_locator,
        'status': status,
        'inputs': inputs,
    }


def _failure_status(failed: bool | None) -> str:
    if failed is None:
        return 'unknown'
    return 'fail' if failed else 'pass'


def _anchor_status(matches: bool, all_resolved: bool) -> str:
    if matches:
        return 'pass'
    return 'fail' if all_resolved else 'unknown'


def _travel_result(participant: Mapping[str, Any], facts: Mapping[str, Any]) -> dict:
    position = _position(
        RASHI_NAMES, participant.get('janma_lagna'), facts.get('lagna')
    )
    excluded = position in {1, 5, 7, 9} if position is not None else None
    lagna_status = _failure_status(excluded)
    rashi = participant.get('janma_rashi')
    candidate_lagna = facts.get('lagna')
    rashi_status = 'unknown'
    if rashi and candidate_lagna:
        rashi_status = 'pass' if rashi == candidate_lagna else 'fail'
    return _result(
        [
            _outcome(
                'travel',
                0,
                lagna_status,
                {
                    'janma_lagna': participant.get('janma_lagna'),
                    'candidate_lagna': candidate_lagna,
                    'position': position,
                },
            ),
            _outcome(
                'travel',
                1,
                rashi_status,
                {
                    'janma_rashi': rashi,
                    'candidate_lagna': candidate_lagna,
                },
            ),
        ],
    )


def _gruhapravesha_result(
    participant: Mapping[str, Any],
    facts: Mapping[str, Any],
) -> dict:
    anchors = (
        (participant.get('nakshatra'), facts.get('nakshatra')),
        (participant.get('janma_rashi'), facts.get('lunar_rashi')),
        (participant.get('janma_lagna'), facts.get('lagna')),
    )
    matches = any(origin and origin == target for origin, target in anchors)
    all_resolved = all(origin and target for origin, target in anchors)
    status = _anchor_status(matches, all_resolved)
    return _result(
        [
            _outcome(
                'gruhapravesha',
                0,
                status,
                {
                    'janma_nakshatra': participant.get('nakshatra'),
                    'candidate_nakshatra': facts.get('nakshatra'),
                    'janma_rashi': participant.get('janma_rashi'),
                    'candidate_chandra_rashi': facts.get('lunar_rashi'),
                    'janma_lagna': participant.get('janma_lagna'),
                    'candidate_lagna': facts.get('lagna'),
                },
            )
        ],
    )


def _seemantha_result(participant: Mapping[str, Any], facts: Mapping[str, Any]) -> dict:
    position = _position(
        NAKSHATRA_NAMES, participant.get('nakshatra'), facts.get('nakshatra')
    )
    excluded = position in {3, 7, 8, 10, 22} if position is not None else None
    status = _failure_status(excluded)
    return _result(
        [
            _outcome(
                'seemantha',
                0,
                status,
                {
                    'janma_nakshatra': participant.get('nakshatra'),
                    'candidate_nakshatra': facts.get('nakshatra'),
                    'position': position,
                },
            )
        ],
    )


def _surgery_result(participant: Mapping[str, Any], facts: Mapping[str, Any]) -> dict:
    janma_rashi = participant.get('janma_rashi')
    candidate_rashi = facts.get('lunar_rashi')
    status = 'unknown'
    if janma_rashi and candidate_rashi:
        status = 'fail' if janma_rashi == candidate_rashi else 'pass'
    return _result(
        [
            _outcome(
                'surgery',
                0,
                status,
                {
                    'janma_rashi': janma_rashi,
                    'candidate_chandra_rashi': candidate_rashi,
                },
            )
        ],
    )


def _borrowing_result(
    participant: Mapping[str, Any], facts: Mapping[str, Any]
) -> dict:
    janma_nakshatra = participant.get('nakshatra')
    candidate_nakshatra = facts.get('nakshatra')
    status = 'unknown'
    if (
        janma_nakshatra in NAKSHATRA_NAMES
        and candidate_nakshatra in NAKSHATRA_NAMES
    ):
        status = (
            'fail' if janma_nakshatra == candidate_nakshatra else 'pass'
        )
    return _result(
        [
            _outcome(
                'borrowing_money',
                0,
                status,
                {
                    'primary_borrower_id': participant.get('id'),
                    'janma_nakshatra': janma_nakshatra,
                    'candidate_nakshatra': candidate_nakshatra,
                },
            )
        ],
    )


_ACTIVITY_EVALUATORS = {
    'travel': _travel_result,
    'gruhapravesha': _gruhapravesha_result,
    'seemantha': _seemantha_result,
    'surgery': _surgery_result,
    'borrowing_money': _borrowing_result,
}


def evaluate_personal_election(
    activity: str,
    participant: Mapping[str, Any] | None,
    facts: Mapping[str, Any],
) -> dict:
    """Evaluate one boundary without inventing missing natal facts."""
    if activity not in PERSONAL_ELECTION_RULES:
        return _result([])
    if participant is None:
        return _result(
            [
                _outcome(activity, index, 'unknown', {'participant_selected': False})
                for index in range(len(PERSONAL_ELECTION_RULES[activity]))
            ],
        )

    return _ACTIVITY_EVALUATORS[activity](participant, facts)


def evaluate_personal_election_window(
    activity: str,
    participant: Mapping[str, Any] | None,
    start_facts: Mapping[str, Any],
    end_facts: Mapping[str, Any],
) -> dict:
    """Compatibility wrapper for a two-snapshot offered window."""
    result = evaluate_personal_election_snapshots(
        activity, participant, [start_facts, end_facts]
    )
    for outcome in result['outcomes']:
        outcome['inputs'] = {
            'start': outcome['inputs']['start'],
            'end': outcome['inputs']['end'],
        }
    return result


def _boundary_items(start_item: dict, evaluations: list[dict]) -> list[dict | None]:
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


def _combined_status(effect: str, statuses: list[str]) -> str:
    if 'unknown' in statuses:
        return 'unknown'
    if effect == 'reject':
        return 'fail' if 'fail' in statuses else 'pass'
    if all(value == 'pass' for value in statuses):
        return 'pass'
    if all(value == 'fail' for value in statuses):
        return 'fail'
    return 'unknown'


def _combined_outcome(start_item: dict, evaluations: list[dict]) -> tuple[dict, bool]:
    boundaries = _boundary_items(start_item, evaluations)
    statuses = [
        item['status'] if item is not None else 'unknown' for item in boundaries
    ]
    outcome = {
        **start_item,
        'status': _combined_status(start_item['effect'], statuses),
        'inputs': {
            'start': boundaries[0]['inputs'] if boundaries[0] else None,
            'end': boundaries[-1]['inputs'] if boundaries[-1] else None,
            'boundaries': [item['inputs'] if item else None for item in boundaries],
        },
    }
    return outcome, all(value == statuses[0] for value in statuses)


def evaluate_personal_election_snapshots(
    activity: str,
    participant: Mapping[str, Any] | None,
    facts: list[Mapping[str, Any]],
) -> dict:
    """Conservatively combine all sampled personal election states."""
    samples = facts or [{'nakshatra': '', 'lunar_rashi': None, 'lagna': None}]
    evaluations = [
        evaluate_personal_election(activity, participant, item) for item in samples
    ]
    outcomes = []
    stable = bool(facts)
    for start_item in evaluations[0]['outcomes']:
        outcome, outcome_stable = _combined_outcome(start_item, evaluations)
        outcomes.append(outcome)
        stable = stable and outcome_stable
    return _result(outcomes, stable=stable)
