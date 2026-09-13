"""Browser smoke fixture cases; no automatic test collection."""

from __future__ import annotations

import pytest

from tests.browser_smoke.constants import MUHURTA_PLANET_RASHIS
from tests.browser_smoke.planet_fixtures import _muhurta_planets


@pytest.mark.parametrize(
    ('scenario', 'chart_index', 'expected_houses'),
    (
        ('positive', 0, {'Chandra': 1, 'Shukra': 1, 'Kuja': 2}),
        ('profile', 0, {'Chandra': 1, 'Shukra': 1, 'Kuja': 2}),
        ('failure', 0, {'Kuja': 8}),
        ('mixed', 0, {'Chandra': 1, 'Shukra': 1}),
        ('mixed', 1, {'Chandra': 2, 'Shukra': 1}),
        ('annaprasana-pass', 0, {'Guru': 1}),
        ('annaprasana-preference-miss', 0, {'Guru': 2}),
        ('annaprasana-hard-fail', 0, {'Guru': 1, 'Surya': 1}),
        (
            'annaprasana-unknown', 0,
            {'Guru': 1, 'Chandra': 1, 'Surya': 7},
        ),
        ('karnavedha-bounded', 0, {'Rahu': 1, 'Ketu': 7}),
        (
            'vidyarambha-pass', 0,
            {'Budha': 9, 'Shukra': 9, 'Guru': 9, 'Rahu': 5, 'Ketu': 11},
        ),
        (
            'vidyarambha-preference-miss', 0,
            {'Budha': 9, 'Shukra': 9, 'Guru': 10, 'Rahu': 5, 'Ketu': 11},
        ),
        (
            'vidyarambha-hard-fail', 0,
            {
                'Budha': 9, 'Shukra': 9, 'Guru': 9,
                'Rahu': 5, 'Ketu': 11, 'Surya': 8,
            },
        ),
        (
            'vidyarambha-unknown', 1,
            {'Budha': 9, 'Shukra': 9, 'Guru': 10, 'Rahu': 5, 'Ketu': 11},
        ),
    ),
)
def test_muhurta_planet_fixture_preserves_scenario_houses(
    scenario, chart_index, expected_houses,
):
    planets = _muhurta_planets(scenario, chart_index, 'Mesha')
    by_name = {planet['name']: planet for planet in planets}
    for name, house in expected_houses.items():
        assert by_name[name]['house'] == house
    assert by_name['Ketu']['house'] == (by_name['Rahu']['house'] + 5) % 12 + 1
    if scenario == 'annaprasana-unknown':
        assert by_name['Surya']['degree'] == 10.0
        assert by_name['Chandra']['degree'] == 10.0

def test_gold_planet_fixture_preserves_cap_unknown_and_lagna_projection():
    template = _muhurta_planets('gold-pass', 0, 'Mesha')
    capped = _muhurta_planets('gold-cap', 0, 'Mesha', template)
    unknown = _muhurta_planets('gold-unknown', 0, 'Mesha', template)
    projected = _muhurta_planets('gold-pass', 0, 'Vrishabha', template)
    capped_by_name = {planet['name']: planet for planet in capped}
    unknown_by_name = {planet['name']: planet for planet in unknown}
    rashis = list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena']
    lagna_index = rashis.index('Vrishabha')

    assert (capped_by_name['Surya']['rashi'], capped_by_name['Surya']['degree']) == (
        'Tula', 1.0,
    )
    assert (
        capped_by_name['Chandra']['rashi'], capped_by_name['Chandra']['degree'],
    ) == ('Vrischika', 1.0)
    assert unknown_by_name['Surya']['degree'] == 10.0
    assert [planet['rashi'] for planet in projected] == [
        planet['rashi'] for planet in template
    ]
    assert [planet['house'] for planet in projected] == [
        (rashis.index(planet['rashi']) - lagna_index) % 12 + 1
        for planet in template
    ]
