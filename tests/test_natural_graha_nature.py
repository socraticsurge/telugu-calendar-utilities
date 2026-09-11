import copy
import json
from pathlib import Path

import pytest

from telugu_panchangam.personal.election_assessors.conventions import (
    ELECTION_CHART_CONVENTIONS,
)
from telugu_panchangam.personal.election_assessors.graha_nature import (
    NATURAL_GRAHA_NATURE_CONVENTION_ID,
    classify_natural_graha_natures,
    evaluate_existential_benefic_house_set,
    evaluate_forbidden_malefic_house_set,
)
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_PLANETS,
)

ROOT = Path(__file__).parents[1]
FIXTURE = json.loads(
    (ROOT / 'tests/fixtures/natural_graha_nature_v1.json').read_text(
        encoding='utf-8'
    )
)


def _chart(overrides=None):
    chart = copy.deepcopy(FIXTURE['base_chart'])
    for planet in chart['planets']:
        planet.update((overrides or {}).get(planet['name'], {}))
    return chart


def _invalid_chart(mutation):
    chart = _chart()
    if mutation['kind'] == 'remove':
        chart['planets'] = [
            item for item in chart['planets']
            if item['name'] != mutation['planet']
        ]
    else:
        planet = next(
            item for item in chart['planets']
            if item['name'] == mutation['planet']
        )
        if mutation['kind'] == 'rename':
            planet['name'] = mutation['value']
        else:
            planet[mutation['field']] = mutation['value']
    return chart


def test_generated_convention_declares_source_and_project_boundaries():
    convention = ELECTION_CHART_CONVENTIONS[
        NATURAL_GRAHA_NATURE_CONVENTION_ID
    ]

    assert FIXTURE['convention_id'] == NATURAL_GRAHA_NATURE_CONVENTION_ID
    assert convention['fixed_malefics'] == [
        'Surya', 'Kuja', 'Shani', 'Rahu', 'Ketu',
    ]
    assert convention['fixed_benefics'] == ['Guru', 'Shukra']
    assert convention['chandra_phase_guard_degrees'] == 0.02
    assert convention['phase_quantization_decimal_places'] == 10
    assert convention['phase_quantization_rounding'] == 'half_up_nonnegative'
    assert convention['budha_association'] == 'same_sidereal_rashi'
    assert convention['house_system'] == 'whole_sign'
    assert set(convention['method_claims']) == {
        'election_chart.natural_graha_nature.phaladeepika_2_27',
        'election_chart.natural_malefics.bphs_3_11_modern_witness',
        'election_chart.budha_same_sign_association_policy_v1',
        'election_chart.raman_180_degree_paksha_policy_v1',
        'election_chart.lunar_phase_boundary_guard_policy_v1',
        'election_chart.mean_node_policy_v1',
    }

    generated = json.loads(
        (ROOT / 'src/data/election-chart-rules.generated.json').read_text(
            encoding='utf-8'
        )
    )
    assert generated['conventions'][NATURAL_GRAHA_NATURE_CONVENTION_ID] == (
        convention
    )


@pytest.mark.parametrize(
    'case', FIXTURE['classifier_cases'], ids=lambda case: case['id']
)
def test_shared_classifier_cases(case):
    result = classify_natural_graha_natures(_chart(case['overrides']))

    assert result.complete is True
    for planet, expected in case['expected'].items():
        assert result.natures[planet] == expected
    assert len(result.evidence) == 2


@pytest.mark.parametrize(
    'case', FIXTURE['invalid_cases'], ids=lambda case: case['id']
)
def test_invalid_or_incomplete_nine_graha_data_fails_closed(case):
    result = classify_natural_graha_natures(
        _invalid_chart(case['mutation'])
    )

    assert result.complete is False
    assert tuple(result.natures) == ELECTION_CHART_PLANETS
    assert set(result.natures.values()) == {'unknown'}
    assert 'unavailable or invalid' in result.evidence[0]


@pytest.mark.parametrize(
    'case', FIXTURE['predicate_cases'], ids=lambda case: case['id']
)
def test_shared_decisive_witness_predicate_cases(case):
    chart = _chart(case['overrides'])
    if case['predicate'] == 'existential_benefic':
        outcome = evaluate_existential_benefic_house_set(
            chart, case['houses']
        )
    else:
        outcome = evaluate_forbidden_malefic_house_set(
            chart, case['houses']
        )

    assert outcome.status == case['expected_status']
    assert case['evidence_contains'] in ' '.join(outcome.evidence)


@pytest.mark.parametrize('houses', ([], [0], [13], [True], '1', None))
def test_malformed_house_sets_return_unknown(houses):
    assert evaluate_existential_benefic_house_set(
        _chart(), houses
    ).status == 'unknown'
    assert evaluate_forbidden_malefic_house_set(
        _chart(), houses
    ).status == 'unknown'


def test_missing_chart_data_keeps_both_predicates_unknown():
    chart = _chart()
    chart['planets'].pop()

    assert evaluate_existential_benefic_house_set(
        chart, [1]
    ).status == 'unknown'
    assert evaluate_forbidden_malefic_house_set(
        chart, [1]
    ).status == 'unknown'

