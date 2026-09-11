import copy
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import COURT_SOURCE_EFFECT_POLICY
from telugu_panchangam.personal.election_assessors.court import (
    COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA,
    aggregate_court_sixth_house_natural_malefic_window,
    court_sixth_house_candidate_disposition,
    evaluate_court_sixth_house_natural_malefic,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (ROOT / 'tests/fixtures/election_chart_court_house6_malefic_oracle.json')
    .read_text(encoding='utf-8')
)


def _chart(case):
    planets = copy.deepcopy(ORACLE['base_planets'])
    overrides = case.get('overrides', {})
    for planet in planets:
        planet.update(overrides.get(planet['name'], {}))
    removed = set(case.get('remove', []))
    planets = [item for item in planets if item['name'] not in removed]
    duplicate = case.get('duplicate')
    if duplicate:
        planets.append(copy.deepcopy(next(p for p in planets if p['name'] == duplicate)))
    return {'planets': planets}


def _outcome(case):
    return evaluate_court_sixth_house_natural_malefic(
        _chart(case),
        house_frame_uncertain=case.get('house_frame_uncertain', False),
    )


def _actual(outcome):
    return {'status': outcome.status, 'evidence': list(outcome.evidence)}


def test_fixture_is_synthetic_and_metadata_keeps_source_policy_separate():
    assert ORACLE['fixture_kind'] == 'synthetic_contract_fixture'
    assert ORACLE['source_golden'] is False
    assert COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA == ORACLE['metadata']
    metadata = COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA
    assert metadata['source_statement']['claim_id'] != (
        metadata['event_policy']['effect_claim_id']
    )
    assert metadata['event_policy']['status'] == 'specified_unwired'
    registry = json.loads(
        (ROOT / 'docs/reference/election-chart-interpretations.json')
        .read_text(encoding='utf-8')
    )['interpretations']
    assert registry[metadata['convention']['classifier_id']][
        'implementation_status'
    ] == 'implemented'
    assert registry[metadata['convention']['house_occupation_id']][
        'implementation_status'
    ] == 'implemented'


def test_shared_snapshot_oracle_covers_fixed_conditional_and_malformed_states():
    for case in ORACLE['snapshot_cases']:
        assert _actual(_outcome(case)) == case['expected'], case['id']


def test_window_oracle_enforces_reject_first_and_complete_transition_coverage():
    cases = {case['id']: case for case in ORACLE['snapshot_cases']}
    for window in ORACLE['window_cases']:
        samples = [_outcome(cases[case_id]) for case_id in window['sample_case_ids']]
        outcome = aggregate_court_sixth_house_natural_malefic_window(
            samples, **window['coverage']
        )
        assert _actual(outcome) == window['expected'], window['id']


def test_known_failure_projects_to_the_accepted_reject_effect():
    case = next(
        item for item in ORACLE['snapshot_cases']
        if item['id'] == 'kuja-in-house6-fail'
    )
    outcome = _outcome(case)

    assert COURT_SOURCE_EFFECT_POLICY['atomic_rule_effects'][
        'court.house-6-without-natural-malefic'
    ] == 'reject'
    assert court_sixth_house_candidate_disposition(outcome) == 'reject'
    assert court_sixth_house_candidate_disposition(
        type(outcome)('pass', ())
    ) == 'retain'
    assert court_sixth_house_candidate_disposition(
        type(outcome)('unknown', ())
    ) == 'review'


def test_runtime_malformed_inputs_fail_closed_and_fail_still_dominates():
    unknown = evaluate_court_sixth_house_natural_malefic(None)  # type: ignore[arg-type]
    assert unknown.status == 'unknown'
    malformed_option = evaluate_court_sixth_house_natural_malefic(
        _chart({}), house_frame_uncertain='yes'  # type: ignore[arg-type]
    )
    assert malformed_option.status == 'unknown'
    fail = _outcome(next(
        item for item in ORACLE['snapshot_cases']
        if item['id'] == 'kuja-in-house6-fail'
    ))
    assert aggregate_court_sixth_house_natural_malefic_window(
        [fail],
        local_lagna_transitions_complete='bad',  # type: ignore[arg-type]
        graha_rasi_transitions_complete='bad',  # type: ignore[arg-type]
        chandra_phase_transitions_complete='bad',  # type: ignore[arg-type]
        budha_association_transitions_complete='bad',  # type: ignore[arg-type]
        budget_exhausted='bad',  # type: ignore[arg-type]
    ) == fail


def test_passing_samples_fail_closed_for_malformed_window_metadata():
    passed = _outcome(ORACLE['snapshot_cases'][0])
    outcome = aggregate_court_sixth_house_natural_malefic_window(
        [passed],
        local_lagna_transitions_complete=True,
        graha_rasi_transitions_complete=True,
        chandra_phase_transitions_complete=True,
        budha_association_transitions_complete=True,
        budget_exhausted=None,  # type: ignore[arg-type]
    )
    assert outcome.status == 'unknown'
    assert 'metadata is malformed' in outcome.evidence[0]
