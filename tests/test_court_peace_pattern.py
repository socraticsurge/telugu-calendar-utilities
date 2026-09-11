import copy
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import COURT_SOURCE_EFFECT_POLICY
from telugu_panchangam.personal.election_assessors.benefic_patterns import (
    KENDRA_HOUSES,
    MALE_RASIS,
)
from telugu_panchangam.personal.election_assessors.court import (
    COURT_PEACE_PATTERN_METADATA,
    aggregate_court_peace_pattern_window,
    evaluate_court_peace_pattern,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (ROOT / 'tests/fixtures/election_chart_court_peace_pattern_oracle.json')
    .read_text(encoding='utf-8')
)


def _chart(case):
    overrides = case.get('overrides', {})
    removed = frozenset(case.get('remove', []))
    planets = [
        {
            **copy.deepcopy(planet),
            **overrides.get(planet['name'], {}),
        }
        for planet in ORACLE['base_planets']
        if planet['name'] not in removed
    ]
    duplicate = case.get('duplicate')
    if duplicate:
        source = next(planet for planet in planets if planet['name'] == duplicate)
        planets.append(copy.deepcopy(source))
    return {'planets': planets}


def _outcome(case):
    return evaluate_court_peace_pattern(
        _chart(case),
        house_frame_uncertain=case.get('house_frame_uncertain', False),
    )


def test_metadata_records_selected_grammar_direction_and_inform_effect():
    assert ORACLE['fixture_kind'] == 'synthetic_contract_fixture'
    assert ORACLE['source_golden'] is False
    assert COURT_PEACE_PATTERN_METADATA == ORACLE['metadata']
    assert tuple(KENDRA_HOUSES) == (1, 4, 7, 10)
    assert MALE_RASIS == {
        'Mesha', 'Mithuna', 'Simha', 'Tula', 'Dhanu', 'Kumbha'
    }
    policy = COURT_PEACE_PATTERN_METADATA['event_policy']
    assert policy['effect'] == 'inform'
    assert policy['status'] == 'specified_unwired'
    assert COURT_SOURCE_EFFECT_POLICY['atomic_rule_effects'][policy['id']] == 'inform'


def test_snapshot_oracle_covers_each_or_arm_together_unknown_and_malformed():
    outcomes = {}
    for case in ORACLE['snapshot_cases']:
        outcome = _outcome(case)
        outcomes[case['id']] = outcome
        assert outcome.status == case['expected_status'], case['id']
    assert 'Resolved natural-benefic witness: Guru (house 4).' in (
        outcomes['kendra-arm-only'].evidence[0]
    )
    assert 'Guru in Mithuna receives full Graha Drishti from Shukra' in (
        ' '.join(outcomes['male-rasi-aspect-arm-only'].evidence)
    )
    both = ' '.join(outcomes['both-arms'].evidence)
    assert 'Kendra arm: Resolved' in both
    assert 'Male-Rasi aspect arm: Resolved' in both


def test_resolved_miss_is_neutral_and_never_predictive():
    miss = next(
        case for case in ORACLE['snapshot_cases']
        if case['id'] == 'neither-arm-resolved'
    )
    text = ' '.join(_outcome(miss).evidence).lower()
    assert all(word not in text for word in ('conflict', 'victory', 'loss', 'settlement'))


def test_window_oracle_keeps_unknowns_in_disclosure_only():
    cases = {case['id']: case for case in ORACLE['snapshot_cases']}
    for window in ORACLE['window_cases']:
        outcome = aggregate_court_peace_pattern_window(
            [_outcome(cases[case_id]) for case_id in window['sample_case_ids']],
            **window['coverage'],
        )
        assert outcome.status == window['expected_status'], window['id']
        if outcome.status == 'fail':
            assert 'no adverse inference' in ' '.join(outcome.evidence).lower()


def test_runtime_malformed_configuration_fails_closed():
    assert evaluate_court_peace_pattern(
        _chart({}), house_frame_uncertain='yes'  # type: ignore[arg-type]
    ).status == 'unknown'
