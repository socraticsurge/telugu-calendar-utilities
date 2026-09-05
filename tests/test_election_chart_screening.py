import json
import subprocess
import sys
from pathlib import Path

import pytest

from telugu_panchangam.personal.election_chart import (
    evaluate_election_chart,
    evaluate_election_snapshots,
    evaluate_election_window,
)
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_COMPLETE_ASSESSORS,
    ELECTION_CHART_MANUAL_REMAINDERS,
    ELECTION_CHART_RULES,
)

PLANETS = (
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
)


def _chart(**houses):
    return {
        'instant': '2026-09-08T05:30:00.000Z',
        'lagna': {'rashi': 'Kanya', 'degree': 12.5},
        'planets': [
            {
                'name': name,
                'rashi': 'Mesha',
                'degree': index + 0.25,
                'house': houses.get(name, index + 1),
                'retrograde': name in {'Rahu', 'Ketu'},
            }
            for index, name in enumerate(PLANETS)
        ],
    }


GOLD_POSITIONS = {
    'Surya': ('Simha', 11.0, 5),
    'Chandra': ('Makara', 15.0, 10),
    'Kuja': ('Meena', 1.0, 12),
    'Budha': ('Vrishabha', 5.0, 2),
    'Guru': ('Mesha', 12.0, 1),
    'Shukra': ('Karka', 21.0, 4),
    'Shani': ('Kanya', 17.0, 6),
    'Rahu': ('Tula', 8.0, 7),
    'Ketu': ('Mesha', 8.0, 1),
}

GOLD_ORACLE = json.loads(
    (Path(__file__).parent / 'fixtures/election_chart_gold_oracle.json')
    .read_text(encoding='utf-8')
)
GOLD_GATEWAY_ORACLE = json.loads(
    (
        Path(__file__).parent
        / 'fixtures/election_chart_gold_gateway_oracle.json'
    ).read_text(encoding='utf-8')
)
ANNAPRASANA_ORACLE = json.loads(
    (
        Path(__file__).parent
        / 'fixtures/election_chart_annaprasana_oracle.json'
    ).read_text(encoding='utf-8')
)

ANNAPRASANA_POSITIONS = {
    'Surya': ('Mithuna', 10.0, 3),
    'Chandra': ('Karka', 20.0, 4),
    'Kuja': ('Kanya', 1.0, 6),
    'Budha': ('Mesha', 5.0, 1),
    'Guru': ('Vrishabha', 12.0, 2),
    'Shukra': ('Mithuna', 21.0, 3),
    'Shani': ('Kumbha', 17.0, 11),
    'Rahu': ('Simha', 8.0, 5),
    'Ketu': ('Kumbha', 8.0, 11),
}


def _gold_chart(*, instant='2026-09-08T05:30:00.000Z', **overrides):
    planets = []
    for name in PLANETS:
        rashi, degree, house = GOLD_POSITIONS[name]
        values = {
            'name': name,
            'rashi': rashi,
            'degree': degree,
            'house': house,
            'retrograde': name in {'Rahu', 'Ketu'},
        }
        values.update(overrides.get(name, {}))
        planets.append(values)
    return {
        'instant': instant,
        'lagna': {'rashi': 'Mesha', 'degree': 12.5},
        'planets': planets,
    }


def _annaprasana_chart(
    *, instant='2026-09-08T05:30:00.000Z', **overrides,
):
    planets = []
    for name in PLANETS:
        rashi, degree, house = ANNAPRASANA_POSITIONS[name]
        values = {
            'name': name,
            'rashi': rashi,
            'degree': degree,
            'house': house,
            'retrograde': name in {'Rahu', 'Ketu'},
        }
        values.update(overrides.get(name, {}))
        planets.append(values)
    return {
        'instant': instant,
        'lagna': {'rashi': 'Mesha', 'degree': 12.5},
        'planets': planets,
    }


def _outcome(result, rule_id):
    return next(
        outcome for outcome in result['outcomes']
        if outcome['rule_id'] == rule_id
    )


def test_annaprasana_declares_six_rule_raman_transcription_assessor():
    rules = ELECTION_CHART_RULES['annaprasana']

    assert [rule['id'] for rule in rules] == [
        'annaprasana.house-10-vacant',
        'annaprasana.budha-not-7',
        'annaprasana.kuja-not-8',
        'annaprasana.shukra-not-9',
        'annaprasana.benefic-occupies-lagna',
        'annaprasana.no-natural-malefic-in-lagna',
    ]
    assert [rule['effect'] for rule in rules] == [
        'reject', 'reject', 'reject', 'reject', 'prefer', 'reject',
    ]
    assert all(
        rule['source_claim']
        == 'muhurta.annaprasana.raman_transcription_chart'
        for rule in rules
    )
    assert all(
        rule['source_locator']
        == (
            "B. V. Raman, Chapter VIII, 'First feeding on rice "
            "(Annaprasana),' inspected in the 2020 Chistabo derivative at "
            'internal printed p. 22 '
            '(physical PDF p. 25)'
        )
        for rule in rules
    )
    assert rules[4]['decision_policy_claim'] == (
        'election_chart.annaprasana.raman_transcription_policy_v1')
    assert all(
        'decision_policy_claim' not in rule
        for rule in (*rules[:4], rules[5])
    )
    assert rules[4]['convention_id'] == (
        'whole-sign-physical-occupation-v1')
    assert rules[5]['convention_id'] == (
        'annaprasana-natural-malefic-lagna-v1')
    assert set(rules[5]['method_claims']) == {
        'election_chart.natural_malefics.bphs_3_11_modern_witness',
        'election_chart.whole_sign_house_policy_v1',
        'election_chart.mean_node_policy_v1',
        'election_chart.budha_same_sign_association_policy_v1',
        'election_chart.raman_180_degree_paksha_policy_v1',
        'election_chart.lunar_phase_boundary_guard_policy_v1',
        'election_chart.annaprasana_fail_closed_aggregation_policy_v1',
    }
    assert ELECTION_CHART_MANUAL_REMAINDERS['annaprasana'] == ()
    assert {'gold', 'annaprasana'} <= set(ELECTION_CHART_COMPLETE_ASSESSORS)


@pytest.mark.parametrize(
    'case', ANNAPRASANA_ORACLE['cases'], ids=lambda case: case['id'])
def test_annaprasana_shared_python_typescript_oracle(case):
    result = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(**case['overrides']))

    assert [item['status'] for item in result['outcomes']] == (
        case['expected_statuses'])
    assert result['rejected'] is case['rejected']
    assert result['preference_passes'] == case['preference_passes']
    assert result['needs_review'] is case['needs_review']


@pytest.mark.parametrize(
    'case', ANNAPRASANA_ORACLE['geographic_cases'],
    ids=lambda case: case['id'],
)
def test_annaprasana_multi_city_live_projection_golden_cases(case):
    result = evaluate_election_chart('annaprasana', case['chart'])

    assert [item['status'] for item in result['outcomes']] == (
        case['expected_statuses'])
    assert result['rejected'] is case['rejected']
    assert result['preference_passes'] == case['preference_passes']
    assert result['needs_review'] is case['needs_review']

    rashis = (
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
        'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
    )
    lagna_index = rashis.index(case['chart']['lagna']['rashi'])
    assert all(
        planet['house']
        == ((rashis.index(planet['rashi']) - lagna_index) % 12) + 1
        for planet in case['chart']['planets']
    )


def test_annaprasana_geographic_golden_set_spans_dates_and_cities():
    cases = ANNAPRASANA_ORACLE['geographic_cases']

    assert {case['city'] for case in cases} == {'Hyderabad', 'Sydney'}
    assert len({case['chart']['instant'][:10] for case in cases}) == 2
    assert ANNAPRASANA_ORACLE['geographic_source'] == {
        'service': 'DashaFlow sidecar /calculate',
        'engine': 'DashaFlow 1.1.0',
        'ayanamsha': 'Lahiri',
        'ephemeris': 'moshier',
        'retrieved_on': '2026-08-30',
        'projection_note': (
            'Planet Rashis and degrees come from the live sidecar. Houses are '
            'the returned Whole Sign projection and are re-evaluated by the '
            'assessor; no birth-profile data is involved.'
        ),
    }


def test_annaprasana_reports_observed_facts_for_each_predicate_shape():
    result = evaluate_election_chart('annaprasana', _annaprasana_chart())

    assert _outcome(
        result, 'annaprasana.house-10-vacant')['evidence'] == [
            'House 10 occupants: none.',
        ]
    assert _outcome(
        result, 'annaprasana.budha-not-7')['evidence'] == [
            'Budha occupies house 1, outside house 7.',
        ]
    assert _outcome(
        result, 'annaprasana.benefic-occupies-lagna')['evidence'] == [
            'Lagna occupants among Budha, Guru and Shukra: Budha.',
        ]
    assert _outcome(
        result, 'annaprasana.no-natural-malefic-in-lagna')['evidence'] == [
            'Natural malefics in Lagna: none; Chandra is outside Lagna.',
        ]


def test_annaprasana_waning_chandra_rejects_but_waxing_does_not():
    waning = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(
            Chandra={'rashi': 'Mesha', 'degree': 5.0, 'house': 1}))
    waxing = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(
            Surya={'rashi': 'Meena', 'degree': 10.0, 'house': 12},
            Chandra={'rashi': 'Mesha', 'degree': 20.0, 'house': 1},
        ))

    waning_outcome = _outcome(
        waning, 'annaprasana.no-natural-malefic-in-lagna')
    waxing_outcome = _outcome(
        waxing, 'annaprasana.no-natural-malefic-in-lagna')
    assert waning_outcome['status'] == 'fail'
    assert 'waning Chandra' in ' '.join(waning_outcome['evidence'])
    assert waning['rejected'] is True
    assert waxing_outcome['status'] == 'pass'
    assert 'waxing Chandra' in ' '.join(waxing_outcome['evidence'])
    assert waxing['rejected'] is False


@pytest.mark.parametrize('elongation', [0.0, 0.02, 179.98, 180.0, 180.02])
def test_annaprasana_two_decimal_phase_guard_is_inclusive(elongation):
    result = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(
            Surya={'rashi': 'Tula', 'degree': 10.0, 'house': 7},
            Chandra={
                'rashi': 'Tula' if elongation < 30 else 'Mesha',
                'degree': 10.0 + elongation if elongation < 20 else (
                    elongation - 170.0),
                'house': 1,
            },
        ))

    assert _outcome(
        result, 'annaprasana.no-natural-malefic-in-lagna')[
            'status'] == 'unknown'
    assert result['needs_review'] is True


def test_annaprasana_fixed_malefic_failure_dominates_phase_unknown():
    result = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(
            Surya={'rashi': 'Mesha', 'degree': 10.0, 'house': 1},
            Chandra={'rashi': 'Mesha', 'degree': 10.0, 'house': 1},
        ))

    outcome = _outcome(
        result, 'annaprasana.no-natural-malefic-in-lagna')
    assert outcome['status'] == 'fail'
    assert outcome['evidence'] == ['Natural malefics in Lagna: Surya.']
    assert result['rejected'] is True
    assert result['needs_review'] is False


def test_annaprasana_fail_closed_window_aggregation_is_effect_aware():
    preference_mixed = evaluate_election_snapshots('annaprasana', [
        _annaprasana_chart(),
        _annaprasana_chart(
            instant='2026-09-08T05:40:00.000Z',
            Budha={'rashi': 'Vrishabha', 'house': 2}),
    ])
    mandatory_fail_and_unknown = evaluate_election_snapshots(
        'annaprasana', [
            _annaprasana_chart(
                Surya={'rashi': 'Mesha', 'degree': 10.0, 'house': 1}),
            _annaprasana_chart(
                instant='2026-09-08T05:40:00.000Z',
                Surya={'rashi': 'Tula', 'degree': 10.0, 'house': 7},
                Chandra={'rashi': 'Mesha', 'degree': 10.0, 'house': 1}),
        ],
    )

    assert _outcome(
        preference_mixed,
        'annaprasana.benefic-occupies-lagna')['status'] == 'unknown'
    assert preference_mixed['needs_review'] is True
    assert _outcome(
        mandatory_fail_and_unknown,
        'annaprasana.no-natural-malefic-in-lagna')['status'] == 'fail'
    assert mandatory_fail_and_unknown['rejected'] is True


def test_annaprasana_absent_commendation_is_not_a_rejection_or_penalty():
    result = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(
            Budha={'rashi': 'Vrishabha', 'house': 2}))

    assert _outcome(
        result, 'annaprasana.benefic-occupies-lagna')['status'] == 'fail'
    assert result['preference_passes'] == 0
    assert result['rejected'] is False
    assert result['needs_review'] is False


def test_annaprasana_incomplete_and_uncertain_frames_fail_closed():
    incomplete = _annaprasana_chart()
    incomplete['planets'].pop()

    missing = evaluate_election_chart('annaprasana', incomplete)
    uncertain = evaluate_election_chart(
        'annaprasana', _annaprasana_chart(), house_frame_uncertain=True)

    assert all(item['status'] == 'unknown' for item in missing['outcomes'])
    assert all(item['status'] == 'unknown' for item in uncertain['outcomes'])


def test_annaprasana_provenance_separates_sources_and_product_conventions():
    root = Path(__file__).parents[1]
    provenance = json.loads(
        (root / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    sources = {source['id']: source for source in provenance['sources']}
    claims = {claim['id']: claim for claim in provenance['claims']}

    transcription = sources['BVR-MUHURTHA-CHISTABO-2020']
    assert transcription['authority_type'] == 'inspected_derivative'
    assert transcription['inspected_directly'] is True
    assert transcription['related_work_id'] == 'BVR-MUHURTHA-1993'
    assert transcription['exact_edition_match_verified'] is False
    assert transcription['physical_pdf_page_count'] == 78
    assert transcription['sha256'] == (
        'b8b878a444a487c83810329fdf8f057c40e92221a867db480d864da8be21a133'
    )
    assert sources['BVR-MUHURTHA-1993']['inspected_directly'] is False
    chart_claim = claims['muhurta.annaprasana.raman_transcription_chart']
    assert chart_claim['source_ids'] == [
        'BVR-MUHURTHA-1993', 'BVR-MUHURTHA-CHISTABO-2020']
    assert chart_claim['locator'].endswith(
        'internal printed p. 22 (physical PDF p. 25)')
    assert 'inspected in the 2020 Chistabo derivative' in chart_claim['locator']
    assert 'strength' not in chart_claim['scope'].lower()

    paksha_claim = claims['muhurta.raman_transcription.paksha_definition']
    assert paksha_claim['source_ids'] == [
        'BVR-MUHURTHA-1993', 'BVR-MUHURTHA-CHISTABO-2020']
    assert paksha_claim['locator'] == (
        "B. V. Raman, Chapter II, 'On certain special yogas,' inspected in "
        'the 2020 Chistabo derivative at internal printed p. 4 '
        '(physical PDF p. 7)'
    )

    paksha_policy = claims['election_chart.raman_180_degree_paksha_policy_v1']
    assert paksha_policy['source_ids'] == [
        'BVR-MUHURTHA-1993', 'BVR-MUHURTHA-CHISTABO-2020']
    assert paksha_policy['locator'] == (
        'B. V. Raman, Chapter II, inspected in the 2020 Chistabo derivative '
        'at internal printed p. 4 (physical PDF p. 7); '
        'annaprasana-natural-malefic-lagna-v1'
    )

    selection_policy = claims[
        'election_chart.annaprasana.raman_transcription_policy_v1']
    assert selection_policy['source_ids'] == []
    assert 'muhurta.annaprasana.raman_transcription_chart' in (
        selection_policy['scope'])
    assert 'muhurta.annaprasana.source_divergence' in selection_policy['scope']
    assert 'carry the external source IDs' in selection_policy['scope']

    bphs = sources['BPHS-ELS-3.11-MODERN-WITNESS']
    assert bphs['authority_type'] == 'modern_text_witness'
    divergence = claims['muhurta.annaprasana.source_divergence']
    assert divergence['verification_state'] == 'contradicted'
    assert set(divergence['source_ids']) == {
        'KALAPRAKASIKA-IYER-1917-AES-1982',
        'MC-NSP-1945-5E',
    }
    assert 'Shukra outside the 7th' in divergence['scope']
    assert 'Budha outside the 9th' in divergence['scope']
    assert 'weak or waning Chandra' in divergence['scope']
    assert 'full Chandra in Lagna' in divergence['scope']

    convention_claims = {
        'election_chart.whole_sign_house_policy_v1',
        'election_chart.mean_node_policy_v1',
        'election_chart.budha_same_sign_association_policy_v1',
        'election_chart.raman_180_degree_paksha_policy_v1',
        'election_chart.lunar_phase_boundary_guard_policy_v1',
        'election_chart.annaprasana_fail_closed_aggregation_policy_v1',
    }
    assert all(
        claims[claim_id]['evidence_class'] == 'project_heuristic'
        and claims[claim_id]['verification_state'] == 'heuristic'
        for claim_id in convention_claims
    )


def test_gold_declares_four_qualification_rules_and_no_chart_remainder():
    rules = ELECTION_CHART_RULES['gold']
    assert [rule['id'] for rule in rules] == [
        'gold.surya-well-situated',
        'gold.chandra-well-situated',
        'gold.surya-fully-aspected',
        'gold.chandra-fully-aspected',
    ]
    assert {rule['effect'] for rule in rules} == {'qualify'}
    assert all(rule['convention_id'] for rule in rules)
    assert all(rule['method_claims'] for rule in rules)
    assert all(
        rule['decision_policy_claim']
        == 'election_chart.gold_qualification_policy_v1'
        for rule in rules
    )
    assert ELECTION_CHART_MANUAL_REMAINDERS['gold'] == ()
    classical = {
        'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani',
    }
    for rule in rules[2:]:
        assert set(rule['aspectors']) <= classical
        assert rule['planet'] not in rule['aspectors']
        assert not {'Rahu', 'Ketu'} & set(rule['aspectors'])


@pytest.mark.parametrize(
    'case', GOLD_ORACLE['cases'], ids=lambda case: case['id'])
def test_gold_shared_python_typescript_oracle(case):
    """Both runtimes consume this corpus so their controlling outcomes agree."""
    result = evaluate_election_chart(
        'gold', _gold_chart(**case['overrides']))

    assert [item['status'] for item in result['outcomes']] == (
        case['expected_statuses'])
    assert result['qualification_failed'] is case['qualification_failed']
    assert result['needs_review'] is case['needs_review']


def test_gold_gateway_oracle_is_actual_multi_city_date_evidence():
    """Keep real gateway cells distinct from synthetic predicate probes."""
    source = GOLD_GATEWAY_ORACLE['source']
    assert source['endpoint'] == (
        'https://astrochaganti.com/api/guest/muhurta/election-charts')
    assert source['gateway_source_revision'] == (
        '4106f09708a154f1c2401880ebe8f9c0b9162eb5')
    assert source['sidecar_source_revision'] == (
        'c84fd856b17120c80e1bb7e455246a0ec8e429ea')
    assert source['engine'] == {
        'name': 'DashaFlow',
        'version': '1.1.0',
        'ayanamsha': 'Lahiri',
        'ephemeris': 'moshier',
        'node_convention': 'mean',
    }
    cases = GOLD_GATEWAY_ORACLE['cases']
    assert {case['city'] for case in cases} == {'Hyderabad', 'Sydney'}
    assert len({case['chart']['instant'][:10] for case in cases}) >= 2
    assert {
        tag for case in cases for tag in case['coverage']
    } == {'pass', 'fail', 'unknown', 'conflict', 'boundary'}

    rashis = (
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya',
        'Tula', 'Vrischika', 'Dhanu', 'Makara', 'Kumbha', 'Meena',
    )
    for case in cases:
        chart = case['chart']
        assert [planet['name'] for planet in chart['planets']] == list(PLANETS)
        assert len({planet['name'] for planet in chart['planets']}) == 9
        lagna_index = rashis.index(chart['lagna']['rashi'])
        assert all(
            planet['house']
            == (rashis.index(planet['rashi']) - lagna_index) % 12 + 1
            for planet in chart['planets']
        )


@pytest.mark.parametrize(
    'case', GOLD_GATEWAY_ORACLE['cases'], ids=lambda case: case['id'])
def test_gold_real_gateway_outcome_oracle(case):
    result = evaluate_election_chart('gold', case['chart'])

    assert [item['status'] for item in result['outcomes']] == (
        case['expected_statuses'])
    assert result['qualification_failed'] is case['qualification_failed']
    assert result['needs_review'] is case['needs_review']


def test_gold_golden_fixture_passes_placement_and_full_aspect_rules():
    result = evaluate_election_chart('gold', _gold_chart())

    assert [outcome['status'] for outcome in result['outcomes']] == [
        'pass', 'pass', 'pass', 'pass',
    ]
    assert {
        key: result[key]
        for key in (
            'rejected', 'needs_review', 'preference_passes',
            'qualification_failed', 'stable',
        )
    } == {
        'rejected': False,
        'needs_review': False,
        'preference_passes': 0,
        'qualification_failed': False,
        'stable': True,
    }
    assert _outcome(
        result, 'gold.surya-fully-aspected')['evidence'] == [
            'Full Graha Drishti to Surya: Guru.',
        ]
    assert _outcome(
        result, 'gold.chandra-fully-aspected')['evidence'] == [
            'Full Graha Drishti to Chandra: Shukra.',
        ]


@pytest.mark.parametrize(
    ('rule_id', 'overrides', 'evidence'),
    (
        ('gold.surya-well-situated', {'Surya': {'house': 6}}, 'house 6'),
        ('gold.chandra-well-situated', {'Chandra': {'house': 8}}, 'house 8'),
        (
            'gold.surya-well-situated',
            {'Surya': {'rashi': 'Vrishabha'}},
            'enemy Rasi Vrishabha',
        ),
        (
            'gold.surya-well-situated',
            {'Surya': {'rashi': 'Tula'}},
            'debilitation Rasi Tula',
        ),
        (
            'gold.surya-well-situated',
            {'Surya': {'degree': 20.1}},
            'debilitation Navamsa Tula',
        ),
        (
            'gold.chandra-well-situated',
            {'Chandra': {'rashi': 'Simha', 'degree': 21.0}},
            'solar clearance 10.00\N{DEGREE SIGN} below 12\N{DEGREE SIGN}',
        ),
    ),
)
def test_gold_known_adverse_placement_fails_qualification_without_rejection(
    rule_id, overrides, evidence,
):
    result = evaluate_election_chart('gold', _gold_chart(**overrides))
    outcome = _outcome(result, rule_id)

    assert outcome['status'] == 'fail'
    assert evidence in ' '.join(outcome['evidence'])
    assert result['qualification_failed'] is True
    assert result['rejected'] is False


@pytest.mark.parametrize(
    ('overrides', 'rule_id', 'evidence'),
    (
        (
            {'Surya': {'degree': 10.0}},
            'gold.surya-well-situated',
            'Navamsa boundary',
        ),
        (
            {'Chandra': {'rashi': 'Simha', 'degree': 23.0}},
            'gold.chandra-well-situated',
            'solar-clearance threshold',
        ),
    ),
)
def test_gold_guard_bands_fail_closed_to_unknown(overrides, rule_id, evidence):
    result = evaluate_election_chart('gold', _gold_chart(**overrides))
    outcome = _outcome(result, rule_id)

    assert outcome['status'] == 'unknown'
    assert evidence in ' '.join(outcome['evidence'])
    assert result['needs_review'] is True
    assert result['qualification_failed'] is False


def test_gold_incomplete_chart_makes_all_four_qualifications_unknown():
    chart = _gold_chart()
    chart['planets'].pop()
    result = evaluate_election_chart('gold', chart)

    assert [outcome['status'] for outcome in result['outcomes']] == [
        'unknown', 'unknown', 'unknown', 'unknown',
    ]
    assert result['needs_review'] is True
    assert result['qualification_failed'] is False
    assert result['rejected'] is False


def test_gold_full_aspect_accepts_a_malefic_classical_aspector():
    result = evaluate_election_chart('gold', _gold_chart(
        Guru={'rashi': 'Mithuna'},
        Shani={'rashi': 'Mithuna'},
    ))
    outcome = _outcome(result, 'gold.surya-fully-aspected')

    assert outcome['status'] == 'pass'
    assert outcome['evidence'] == ['Full Graha Drishti to Surya: Shani.']


@pytest.mark.parametrize(
    ('target_rule', 'overrides'),
    (
        (
            'gold.surya-fully-aspected',
            {'Guru': {'rashi': 'Mithuna'}},
        ),
        (
            'gold.chandra-fully-aspected',
            {'Shukra': {'rashi': 'Simha'}},
        ),
    ),
)
def test_gold_missing_full_aspect_fails_qualification(target_rule, overrides):
    result = evaluate_election_chart('gold', _gold_chart(**overrides))
    outcome = _outcome(result, target_rule)

    assert outcome['status'] == 'fail'
    assert outcome['evidence'][0].startswith('No v1 full Graha Drishti')
    assert result['qualification_failed'] is True
    assert result['needs_review'] is False


def test_gold_snapshot_fail_dominates_unknown_for_the_same_rule():
    result = evaluate_election_snapshots('gold', [
        _gold_chart(instant='2026-09-08T05:30:00.000Z'),
        _gold_chart(
            instant='2026-09-08T05:40:00.000Z',
            Surya={'degree': 10.0},
        ),
        _gold_chart(
            instant='2026-09-08T05:50:00.000Z',
            Surya={'house': 6},
        ),
    ])

    assert _outcome(
        result, 'gold.surya-well-situated')['status'] == 'fail'
    assert result['stable'] is False
    assert result['qualification_failed'] is True
    assert result['needs_review'] is True
    assert result['rejected'] is False


def test_gold_unrepresented_navamsa_transition_fails_closed():
    result = evaluate_election_snapshots('gold', [
        _gold_chart(
            instant='2026-09-08T05:30:00.000Z',
            Surya={'degree': 9.96},
        ),
        _gold_chart(
            instant='2026-09-08T05:35:00.000Z',
            Surya={'degree': 9.96},
        ),
    ])

    outcome = _outcome(result, 'gold.surya-well-situated')
    assert outcome['status'] == 'unknown'
    assert 'transition cannot be excluded' in ' '.join(outcome['evidence'])
    assert result['stable'] is False
    assert result['needs_review'] is True


def test_gold_unrepresented_solar_clearance_transition_fails_closed():
    result = evaluate_election_snapshots('gold', [
        _gold_chart(
            instant='2026-09-08T05:30:00.000Z',
            Chandra={'rashi': 'Simha', 'degree': 23.1},
        ),
        _gold_chart(
            instant='2026-09-08T05:35:00.000Z',
            Chandra={'rashi': 'Simha', 'degree': 23.1},
        ),
    ])

    outcome = _outcome(result, 'gold.chandra-well-situated')
    assert outcome['status'] == 'unknown'
    assert 'solar-clearance transition' in ' '.join(outcome['evidence'])
    assert result['needs_review'] is True


def test_gold_sampling_gap_over_ten_minutes_fails_closed():
    result = evaluate_election_snapshots('gold', [
        _gold_chart(instant='2026-09-08T05:30:00.000Z'),
        _gold_chart(instant='2026-09-08T05:41:00.000Z'),
    ])

    assert {item['status'] for item in result['outcomes']} == {'unknown'}
    assert all(
        'ten-minute transition coverage' in ' '.join(item['evidence'])
        for item in result['outcomes']
    )
    assert result['stable'] is False
    assert result['needs_review'] is True


def test_gold_rashi_rounding_boundary_fails_closed_for_aspects():
    result = evaluate_election_chart(
        'gold', _gold_chart(Guru={'degree': 0.0}))

    outcome = _outcome(result, 'gold.surya-fully-aspected')
    assert outcome['status'] == 'unknown'
    assert 'Rasi boundary guard' in ' '.join(outcome['evidence'])


def test_gold_secure_aspector_dominates_an_unrelated_boundary_uncertainty():
    result = evaluate_election_chart('gold', _gold_chart(
        Guru={'degree': 0.0},
        Shani={'rashi': 'Mithuna'},
    ))

    outcome = _outcome(result, 'gold.surya-fully-aspected')
    assert outcome['status'] == 'pass'
    assert 'Full Graha Drishti to Surya: Shani.' in outcome['evidence']


def test_gold_secure_continuous_aspect_dominates_unrelated_motion():
    result = evaluate_election_snapshots('gold', [
        _gold_chart(
            instant='2026-09-08T05:30:00.000Z',
            Guru={'rashi': 'Mithuna'},
            Shani={'rashi': 'Mithuna'},
        ),
        _gold_chart(
            instant='2026-09-08T05:35:00.000Z',
            Guru={'rashi': 'Dhanu'},
            Shani={'rashi': 'Mithuna'},
        ),
    ])

    outcome = _outcome(result, 'gold.surya-fully-aspected')
    assert outcome['status'] == 'pass'
    assert 'Full Graha Drishti to Surya: Shani.' in outcome['evidence']
    assert _outcome(result, 'gold.chandra-fully-aspected')['status'] == 'pass'


def test_gold_uncertain_house_frame_keeps_aspect_assessment_available():
    result = evaluate_election_snapshots(
        'gold', [_gold_chart()], house_frame_uncertain=True)

    assert [outcome['status'] for outcome in result['outcomes']] == [
        'unknown', 'unknown', 'pass', 'pass',
    ]
    assert result['needs_review'] is True
    assert result['qualification_failed'] is False


def test_wedding_named_prohibition_rejects():
    result = evaluate_election_chart('wedding', _chart(Kuja=8))
    assert result['rejected'] is True
    assert any(
        outcome['rule_id'] == 'wedding.kuja-not-8'
        and outcome['status'] == 'fail'
        and 'internal printed pp. 41-42' in outcome['source_locator']
        for outcome in result['outcomes']
    )


def test_vacancy_includes_nodes_under_disclosed_whole_sign_convention():
    result = evaluate_election_chart('gruhapravesha', _chart(Rahu=8))
    assert result['rejected'] is True


def test_incomplete_chart_fails_closed_to_unknown():
    chart = _chart()
    chart['planets'].pop()
    result = evaluate_election_chart('wedding', chart)
    assert result['rejected'] is False
    assert result['needs_review'] is True
    assert all(outcome['status'] == 'unknown' for outcome in result['outcomes'])


@pytest.mark.parametrize('invalid_house', [True, False, 0, 13])
def test_invalid_house_values_fail_closed_to_unknown(invalid_house):
    chart = _chart()
    chart['planets'][0]['house'] = invalid_house
    result = evaluate_election_chart('wedding', chart)
    assert result['rejected'] is False
    assert result['needs_review'] is True
    assert all(outcome['status'] == 'unknown' for outcome in result['outcomes'])


def test_window_uses_both_boundaries():
    start = _chart(Kuja=7)
    end = _chart(Kuja=8)
    end['instant'] = '2026-09-08T06:18:00.000Z'
    result = evaluate_election_window('wedding', start, end)
    assert result['stable'] is False
    assert result['rejected'] is True


def test_interior_failure_cannot_hide_behind_matching_endpoints():
    result = evaluate_election_snapshots('wedding', [
        _chart(Kuja=7),
        _chart(Kuja=8),
        _chart(Kuja=7),
    ])
    assert result['stable'] is False
    assert result['rejected'] is True


def test_generated_browser_rule_contract_is_current():
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, 'tools/export_election_chart_rules.py', '--check'],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_every_rule_uses_registered_source_method_and_policy_claims():
    root = Path(__file__).parents[1]
    provenance = json.loads((root / 'docs/reference/provenance.json').read_text())
    claim_ids = {claim['id'] for claim in provenance['claims']}

    for rules in ELECTION_CHART_RULES.values():
        for rule in rules:
            assert rule['source_claim'] in claim_ids
            for claim_id in rule.get('method_claims', ()):
                assert claim_id in claim_ids
            if 'decision_policy_claim' in rule:
                assert rule['decision_policy_claim'] in claim_ids


def test_provenance_distinguishes_the_drik_website_post_screen():
    root = Path(__file__).parents[1]
    provenance = json.loads((root / 'docs/reference/provenance.json').read_text())
    claims = {claim['id']: claim for claim in provenance['claims']}
    automated_claims = {
        rule['source_claim']
        for rules in ELECTION_CHART_RULES.values()
        for rule in rules
    }
    for claim_id in automated_claims:
        assert 'Drik website post-screen' in claims[claim_id]['scope'], claim_id
