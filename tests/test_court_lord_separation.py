import copy
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import COURT_SOURCE_EFFECT_POLICY
from telugu_panchangam.personal.election_assessors.court import (
    COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA,
    aggregate_court_lagna_sixth_lord_separation_window,
    evaluate_court_lagna_sixth_lord_separation,
)
from telugu_panchangam.personal.election_assessors.lordship import (
    CLASSICAL_RASI_LORDS,
    derive_lagna_sixth_lords,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (ROOT / 'tests/fixtures/election_chart_court_lord_separation_oracle.json')
    .read_text(encoding='utf-8')
)


def _chart(case):
    planets = copy.deepcopy(ORACLE['base_planets'])
    for planet in planets:
        planet.update(case.get('overrides', {}).get(planet['name'], {}))
    removed = set(case.get('remove', []))
    planets = [item for item in planets if item['name'] not in removed]
    duplicate = case.get('duplicate')
    if duplicate:
        planets.append(copy.deepcopy(next(p for p in planets if p['name'] == duplicate)))
    return {'planets': planets}


def _outcome(case):
    return evaluate_court_lagna_sixth_lord_separation(
        _chart(case),
        authoritative_lagna_rashi=case['lagna'],
        lagna_authority_uncertain=case.get('lagna_authority_uncertain', False),
    )


def _actual(outcome):
    return {'status': outcome.status, 'evidence': list(outcome.evidence)}


def test_metadata_separates_source_ownership_distance_and_event_effect():
    assert ORACLE['fixture_kind'] == 'synthetic_contract_fixture'
    assert ORACLE['source_golden'] is False
    assert COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA == ORACLE['metadata']
    metadata = COURT_LAGNA_SIXTH_LORD_SEPARATION_METADATA
    assert metadata['source_statement']['claim_id'] != (
        metadata['convention']['separation_claim_id']
    )
    assert metadata['event_policy']['effect'] == 'prefer'
    assert metadata['event_policy']['status'] == 'specified_unwired'
    assert COURT_SOURCE_EFFECT_POLICY['atomic_rule_effects'][
        metadata['event_policy']['id']
    ] == 'prefer'

    registry = json.loads(
        (ROOT / 'docs/reference/election-chart-interpretations.json')
        .read_text(encoding='utf-8')
    )
    ownership = registry['interpretations'][metadata['convention']['ownership_id']]
    assert ownership['implementation_status'] == 'implemented'
    assert metadata['convention']['ownership_claim_id'] in ownership['source_claims']
    assert metadata['convention']['separation_claim_id'] in ownership['method_claims']

    claims = {
        claim['id'] for claim in json.loads(
            (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8')
        )['claims']
    }
    assert metadata['source_statement']['claim_id'] in claims
    assert metadata['convention']['ownership_claim_id'] in claims
    assert metadata['convention']['separation_claim_id'] in claims


def test_all_twelve_lagnas_derive_classical_lords_without_nodes():
    assert set(CLASSICAL_RASI_LORDS.values()).isdisjoint({'Rahu', 'Ketu'})
    assert set(CLASSICAL_RASI_LORDS) == {case['lagna'] for case in ORACLE['lagna_cases']}
    for case in ORACLE['lagna_cases']:
        assert derive_lagna_sixth_lords(case['lagna']) == (
            case['lagna_lord'], case['sixth_rashi'], case['sixth_lord']
        )


def test_snapshot_oracle_covers_opposition_asymmetry_same_owner_and_conflicts():
    for case in ORACLE['snapshot_cases']:
        assert _actual(_outcome(case)) == case['expected'], case['id']


def test_window_oracle_requires_complete_lagna_and_lord_ingress_coverage():
    cases = {case['id']: case for case in ORACLE['snapshot_cases']}
    for window in ORACLE['window_cases']:
        outcome = aggregate_court_lagna_sixth_lord_separation_window(
            [_outcome(cases[case_id]) for case_id in window['sample_case_ids']],
            **window['coverage'],
        )
        assert _actual(outcome) == window['expected'], window['id']


def test_runtime_malformed_configuration_fails_closed():
    assert evaluate_court_lagna_sixth_lord_separation(
        _chart({}), authoritative_lagna_rashi=None  # type: ignore[arg-type]
    ).status == 'unknown'
    assert evaluate_court_lagna_sixth_lord_separation(
        _chart({}),
        authoritative_lagna_rashi='Mesha',
        lagna_authority_uncertain='yes',  # type: ignore[arg-type]
    ).status == 'unknown'
