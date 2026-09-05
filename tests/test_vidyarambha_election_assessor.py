"""Parity and source-boundary tests for the Aksharabhyasa chart assessor."""

import json
from pathlib import Path

import pytest

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.election_chart import (
    _evaluate_rule,
    evaluate_election_snapshots,
)
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_COMPLETE_ASSESSORS,
    ELECTION_CHART_MANUAL_REMAINDERS,
    ELECTION_CHART_RULES,
)
from tools.export_muhurtam_rule_crosswalk import build_crosswalk

ROOT = Path(__file__).resolve().parents[1]
PLANETS = (
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
)
FIXTURE = json.loads(
    (ROOT / 'tests/fixtures/election_chart_vidyarambha_oracle.json')
    .read_text(encoding='utf-8')
)


def _chart(snapshot, index=0):
    houses = {
        'Surya': 1,
        'Chandra': 2,
        'Kuja': 3,
        'Budha': 9,
        'Guru': 9,
        'Shukra': 9,
        'Shani': 4,
        'Rahu': 5,
        'Ketu': 6,
        **snapshot.get('houses', {}),
    }
    planets = [
        {
            'name': name,
            'rashi': 'Mesha',
            'degree': position + 0.25,
            'house': houses[name],
            'retrograde': name in {'Rahu', 'Ketu'},
        }
        for position, name in enumerate(PLANETS)
    ]
    mutation = snapshot.get('mutation')
    if mutation == 'remove-ketu':
        planets.pop()
    elif mutation == 'string-house':
        planets[0]['house'] = '1'
    elif mutation == 'duplicate-surya':
        planets[-1]['name'] = 'Surya'
    return {
        'instant': f'2030-11-17T0{index}:00:00.000Z',
        'lagna': {'rashi': 'Mesha', 'degree': 12.5},
        'planets': planets,
    }


def _outcome(result, rule_id):
    return next(item for item in result['outcomes'] if item['rule_id'] == rule_id)


def test_vidyarambha_declares_scoped_two_rule_partial_assessor():
    rules = ELECTION_CHART_RULES['vidyarambha']
    assert [rule['id'] for rule in rules] == [
        'vidyarambha.house-8-vacant',
        'vidyarambha.budha-shukra-guru-9',
    ]
    assert [rule['effect'] for rule in rules] == ['reject', 'prefer']
    assert rules[1]['kind'] == 'all_planets_in_houses'
    assert rules[1]['planets'] == ['Budha', 'Shukra', 'Guru']
    assert rules[1]['houses'] == [9]
    assert rules[1]['convention_id'] == (
        'vidyarambha-benefic-trio-co-location-v1')
    assert rules[1]['decision_policy_claim'] == (
        'election_chart.vidyarambha_reject_precedence_policy_v1')
    remainders = ELECTION_CHART_MANUAL_REMAINDERS['vidyarambha']
    assert remainders == ()
    assert ELECTION_CHART_COMPLETE_ASSESSORS == ('gold',)


@pytest.mark.parametrize('case', FIXTURE['cases'], ids=lambda item: item['id'])
def test_shared_python_typescript_vidyarambha_oracle(case):
    result = evaluate_election_snapshots(
        'vidyarambha',
        [_chart(snapshot, index) for index, snapshot in enumerate(case['snapshots'])],
        house_frame_uncertain=case.get('house_frame_uncertain', False),
    )

    assert [item['status'] for item in result['outcomes']] == (
        case['expected_statuses'])
    assert result['rejected'] is case['rejected']
    assert result['needs_review'] is case['needs_review']
    assert result['preference_passes'] == case['preference_passes']
    assert result['stable'] is case['stable']


def test_vidyarambha_co_location_formula_is_and_not_any():
    pass_result = evaluate_election_snapshots(
        'vidyarambha', [_chart({'houses': {
            'Budha': 9, 'Shukra': 9, 'Guru': 9,
        }})]
    )
    miss_result = evaluate_election_snapshots(
        'vidyarambha', [_chart({'houses': {
            'Budha': 9, 'Shukra': 9, 'Guru': 10,
        }})]
    )

    assert _outcome(
        pass_result, 'vidyarambha.budha-shukra-guru-9')['status'] == 'pass'
    miss = _outcome(
        miss_result, 'vidyarambha.budha-shukra-guru-9')
    assert miss['status'] == 'fail'
    assert miss['evidence'] == [
        'Budha house 9; Shukra house 9; Guru house 10; all must be in house 9.'
    ]


def test_reject_wins_when_the_preference_also_passes():
    result = evaluate_election_snapshots(
        'vidyarambha', [_chart({'houses': {
            'Rahu': 8, 'Budha': 9, 'Shukra': 9, 'Guru': 9,
        }})]
    )

    assert result['rejected'] is True
    assert result['preference_passes'] == 1
    assert _outcome(result, 'vidyarambha.house-8-vacant')['evidence'] == [
        'House 8 occupants: Rahu.'
    ]


def test_unknown_rule_kind_fails_closed_instead_of_becoming_any_planet():
    rule = {
        'kind': 'unsupported_future_kind',
        'planets': ['Budha', 'Shukra', 'Guru'],
        'houses': [9],
    }
    result = _evaluate_rule(rule, {
        'Budha': 9, 'Shukra': 1, 'Guru': 1,
    }, None)

    assert result.status == 'unknown'
    assert result.evidence == (
        'Unsupported election-chart rule kind: unsupported_future_kind.',)


def test_vidyarambha_lineages_and_copy_variance_are_explicit():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8')
    )
    sources = {item['id']: item for item in ledger['sources']}
    claims = {item['id']: item for item in ledger['claims']}
    rules = ACTIVITY_RULES['vidyarambha']

    assert sources['MC-NIRNAYASAGAR-1945-JAINQQ']['edition'].startswith(
        'Fifth edition, Nirnaya Sagar Press, 1945')
    assert sources['MC-NIRNAYASAGAR-1945-JAINQQ']['url'] == (
        'https://jainqq.org/explore/002342/213')
    assert rules['related_claims'] == [
        'muhurta.vidyarambha.raman_chapter_xi_scope',
        'muhurta.vidyarambha.chintamani_divergence',
    ]
    assert rules['label'] == 'Aksharabhyasa (First-letter writing)'
    assert rules['source_scope'] == (
        'This profile assesses the Chapter VIII Aksharabhyasa '
        'first-letter-writing rite only; it is not a generic '
        'education-start election.'
    )
    assert len(rules['manual_checks']) == 4
    assert 'first-letter-writing rite' in claims['muhurta.vidyarambha']['scope']
    assert 'internal printed pp. 46-47 (physical PDF pp. 50-51)' in claims[
        'muhurta.vidyarambha.raman_chapter_xi_scope']['locator']
    assert 'verses 5.37-5.38' in claims[
        'muhurta.vidyarambha.chintamani_divergence']['locator']
    assert 'does not support the Raman trio' in claims[
        'muhurta.vidyarambha.chintamani_divergence']['scope']
    assert 'inspected 2020 re-edited transcription' in rules[
        'manual_checks'][0]
    assert claims['muhurta.vidyarambha']['source_ids'] == [
        'BVR-MUHURTHA-1993', 'BVR-MUHURTHA-CHISTABO-2020',
    ]
    assert sources['BVR-MUHURTHA-1993']['inspected_directly'] is False
    assert sources['BVR-MUHURTHA-CHISTABO-2020'][
        'inspected_directly'] is True

    generated_contract = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json')
        .read_text(encoding='utf-8')
    )
    assert generated_contract['rules']['vidyarambha']['source_scope'] == (
        rules['source_scope'])
    generated = generated_contract['check_contract']['activities'][
        'vidyarambha']
    assert [row['display_section'] for row in generated['manual_checks']] == [
        'information', 'information', 'chart', 'chart',
    ]

    profile = (
        ROOT / 'docs/reference/21-vidyarambha-profile.md'
    ).read_text(encoding='utf-8')
    method = (
        ROOT / 'docs/reference/54-muhurtam-election-chart-screening.md'
    ).read_text(encoding='utf-8')
    research = (
        ROOT / 'docs/research/election-chart-automation/report-source.md'
    ).read_text(encoding='utf-8')
    assert 'first-letter-writing rite described under' in profile
    assert 'Chapter VIII' in profile
    assert 'internal printed p. 23 (physical PDF p. 26)' in (
        ' '.join(profile.split()))
    assert 'H(Budha) = 9 AND H(Shukra) = 9 AND H(Guru) = 9' in profile
    assert 'not blended into this Chapter' in profile
    assert 'physical scan p. 213' in profile
    assert 'physical scan p. 214' in profile
    assert '29 deterministic predicates' in method
    assert 'Gold is currently the only complete v1 assessor' in (
        ' '.join(method.split()))
    assert 'partial/provisional' in method
    assert '## Aksharabhyasa / Vidyarambha v1' in research


def test_canonical_computation_record_exposes_vidyarambha_contract():
    ledger = json.loads(
        (ROOT / 'docs/reference/computations.json').read_text(encoding='utf-8')
    )
    record = next(item for item in ledger['computations'] if item['id'] == (
        'personal.muhurta-slot-ranking'))

    assert 'muhurta.vidyarambha' in record['provenance']['claim_ids']
    assert 'election_chart.vidyarambha_co_location_policy_v1' in (
        record['provenance']['claim_ids'])
    assert 'election_chart.vidyarambha_reject_precedence_policy_v1' in (
        record['provenance']['claim_ids'])
    assert 'tests/test_vidyarambha_projection.py' in record['tests']
    formula = next(item for item in record['method']['formulae'] if item[
        'name'] == 'Aksharabhyasa partial chart clauses')
    assert 'H(Budha) = 9 AND H(Shukra) = 9 AND H(Guru) = 9' in (
        formula['expression'])


def test_crosswalk_marks_chart_rows_and_fallback_manual_rows_honestly():
    rows = {row['rule_id']: row for row in build_crosswalk()['rows']}
    trio = rows['vidyarambha.budha-shukra-guru-9']

    assert trio['configured_inputs']['predicate'] == 'all_planets_in_houses'
    predicate_inputs = trio['configured_inputs']['predicate_inputs']
    assert {
        key: predicate_inputs[key]
        for key in ('planets', 'houses', 'convention_id')
    } == {
        'planets': ['Budha', 'Shukra', 'Guru'],
        'houses': [9],
        'convention_id': 'vidyarambha-benefic-trio-co-location-v1',
    }
    assert predicate_inputs['decision_policy_claim'] == (
        'election_chart.vidyarambha_reject_precedence_policy_v1')
    assert trio['ranking_effect'] == 'post_screen_tie_break_preference'
    assert trio['decision_policy_claim']['id'] == (
        'election_chart.vidyarambha_reject_precedence_policy_v1')
    assert 'election_chart.vidyarambha_co_location_policy_v1' in (
        trio['configured_inputs']['predicate_inputs']['method_claims'])
    for rule_id in ('vidyarambha.manual-3', 'vidyarambha.manual-4'):
        manual = rows[rule_id]
        assert manual['applicability'] == (
            'python_or_mcp_or_non_drik_or_exact_chart_unavailable')
        assert manual['ranking_effect'].startswith('fallback_only_')
