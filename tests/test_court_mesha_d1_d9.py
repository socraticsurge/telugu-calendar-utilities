"""Court Mesha D1/D9 admission stays authoritative, guarded, and mirrored."""

import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.election_assessors.court import (
    COURT_MESHA_D1_D9_METADATA,
    aggregate_court_mesha_d1_d9_window,
    court_mesha_admission_kind,
    evaluate_court_mesha_d1_d9,
)

ORACLE = json.loads(
    (
        Path(__file__).parent
        / 'fixtures/election_chart_court_mesha_oracle.json'
    ).read_text(encoding='utf-8')
)


def _actual(outcome):
    return {'status': outcome.status, 'evidence': list(outcome.evidence)}


def _outcome(case):
    return evaluate_court_mesha_d1_d9(
        case.get('chart'),
        authoritative_d1_rashi=case.get('authoritative_d1_rashi'),
        lagna_authority_uncertain=case.get(
            'lagna_authority_uncertain', False
        ),
        supported_system=case.get('supported_system', True),
    )


def test_fixture_is_synthetic_and_policy_layers_are_separate():
    assert ORACLE['fixture_kind'] == 'synthetic_contract_fixture'
    assert ORACLE['source_golden'] is False
    assert COURT_MESHA_D1_D9_METADATA == ORACLE['metadata']
    assert COURT_MESHA_D1_D9_METADATA['source_statement']['claim_id'] != (
        COURT_MESHA_D1_D9_METADATA['event_policy']['effect_claim_id']
    )
    assert COURT_MESHA_D1_D9_METADATA['event_policy']['status'] == (
        'specified_unwired'
    )
    assert COURT_MESHA_D1_D9_METADATA['conditional_admission'] == {
        'id': 'court.mesha-navamsa-unresolved',
        'status': 'specified_unwired',
        'delivery_issue': 285,
        'rule': (
            'Only a valid non-Mesha D1 candidate whose D9 alternative is not '
            'yet resolved may be provisionally retained.'
        ),
    }

    # The foundation does not prematurely broaden the base shortlist.
    assert ACTIVITY_RULES['court']['allowed_lagnas'] == ['Mesha']


def test_registered_authority_and_documentation_match_the_foundation():
    root = Path(__file__).parents[1]
    provenance = json.loads(
        (root / 'docs/reference/provenance.json').read_text(encoding='utf-8')
    )
    claim_ids = {claim['id'] for claim in provenance['claims']}
    metadata = COURT_MESHA_D1_D9_METADATA
    assert metadata['source_statement']['claim_id'] in claim_ids
    assert metadata['event_policy']['effect_claim_id'] in claim_ids
    assert set(metadata['convention']['method_claim_ids']) <= claim_ids

    report = (root / 'docs/reference/34-court-evidence-audit.md').read_text(
        encoding='utf-8'
    )
    assert 'Mesha D1-or-D9 predicate foundation' in report
    assert '`specified_unwired` predicate foundation' in report


def test_snapshot_oracle_covers_d1_d9_authority_and_unavailable_states():
    for case in ORACLE['snapshot_cases']:
        assert _actual(_outcome(case)) == case['expected'], case['id']


def test_only_an_unresolved_non_mesha_d9_alternative_is_provisional():
    cases = {case['id']: case for case in ORACLE['snapshot_cases']}
    passed = _outcome(cases['non-mesha-d1-mesha-d9-passes'])
    failed = _outcome(cases['resolved-non-mesha-d1-and-d9-fail'])
    unknown = _outcome(cases['internal-navamsa-boundary-is-unknown'])

    assert court_mesha_admission_kind('Mesha') == 'unconditional'
    assert court_mesha_admission_kind('Vrishabha') == 'provisional'
    assert court_mesha_admission_kind('Vrishabha', unknown) == 'provisional'
    assert court_mesha_admission_kind('Vrishabha', passed) == 'admitted'
    assert court_mesha_admission_kind('Vrishabha', failed) == 'rejected'
    assert court_mesha_admission_kind(None) == 'unavailable'


def test_window_oracle_preserves_reject_precedence_and_transition_guards():
    cases = {case['id']: case for case in ORACLE['snapshot_cases']}
    for window in ORACLE['window_cases']:
        samples = [_outcome(cases[case_id]) for case_id in window['sample_case_ids']]
        outcome = aggregate_court_mesha_d1_d9_window(
            samples, **window['coverage']
        )
        expected = (
            cases[window['expected_case_id']]['expected']
            if 'expected_case_id' in window
            else window['expected']
        )
        assert _actual(outcome) == expected, window['id']


def test_runtime_invalid_inputs_fail_closed():
    invalid = evaluate_court_mesha_d1_d9(
        {'lagna': {'rashi': 'Vrishabha', 'degree': True}},
        authoritative_d1_rashi='Vrishabha',
    )
    assert invalid.status == 'unknown'

    passed = _outcome(ORACLE['snapshot_cases'][0])
    assert aggregate_court_mesha_d1_d9_window(
        [passed],
        local_lagna_transitions_complete=True,
        lagna_navamsa_transitions_complete=True,
        budget_exhausted='no',
    ).status == 'unknown'
