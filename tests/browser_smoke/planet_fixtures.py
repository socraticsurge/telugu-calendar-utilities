"""Browser smoke planet fixtures; no automatic test collection."""

from __future__ import annotations

from tests.browser_smoke.calendar_fixtures import _fixture_navamsa_rashi
from tests.browser_smoke.constants import MUHURTA_PLANET_NAMES, MUHURTA_PLANET_RASHIS


def _gold_pass_planets(canonical_lagnas):
    """Build a complete chart where both luminaries pass all Gold clauses."""
    rashis = list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena']
    if isinstance(canonical_lagnas, str):
        canonical_lagnas = (canonical_lagnas,)
    lagna_indexes = [rashis.index(lagna) for lagna in canonical_lagnas]
    lagna_index = lagna_indexes[0]
    pair = _find_gold_luminary_pair(rashis, lagna_indexes)
    assert pair is not None
    surya_rashi, surya_house, chandra_rashi, chandra_house = pair
    positions = _gold_positions(rashis, lagna_index, surya_rashi, chandra_rashi)
    planets = []
    for index, name in enumerate(MUHURTA_PLANET_NAMES):
        rashi, degree = positions.get(
            name, (rashis[(lagna_index + 1) % 12], index + 0.25)
        )
        planets.append({
            'name': name,
            'rashi': rashi,
            'degree': degree,
            'house': (rashis.index(rashi) - lagna_index) % 12 + 1,
            'retrograde': name in {'Shani', 'Rahu', 'Ketu'},
        })
    return planets


def _find_gold_luminary_pair(rashis, lagna_indexes):
    forbidden_houses = {6, 8, 12}
    surya_forbidden = {'Vrishabha', 'Tula', 'Makara', 'Kumbha'}
    for surya_index, surya_rashi in enumerate(rashis):
        chandra_index = (surya_index + 6) % 12
        surya_houses = [
            (surya_index - index) % 12 + 1 for index in lagna_indexes
        ]
        chandra_houses = [
            (chandra_index - index) % 12 + 1 for index in lagna_indexes
        ]
        if surya_rashi in surya_forbidden or rashis[chandra_index] == 'Vrischika':
            continue
        if forbidden_houses.isdisjoint(surya_houses + chandra_houses):
            return (
                surya_rashi, surya_houses[0],
                rashis[chandra_index], chandra_houses[0],
            )
    return None


def _gold_positions(rashis, lagna_index, surya_rashi, chandra_rashi):
    safe_degrees = (1.0, 5.0, 9.0, 11.0, 15.0, 19.0, 23.0, 27.0)
    surya_degree = next(
        degree for degree in safe_degrees
        if _fixture_navamsa_rashi(surya_rashi, degree) != 'Tula'
    )
    chandra_degree = next(
        degree for degree in safe_degrees
        if _fixture_navamsa_rashi(chandra_rashi, degree) != 'Vrischika'
    )
    return {
        'Surya': (surya_rashi, surya_degree),
        'Chandra': (chandra_rashi, chandra_degree),
        # Keep the rounded mean-node facts exactly opposite, as required by
        # the current public DashaFlow response contract.
        'Rahu': (rashis[(lagna_index + 1) % 12], 10.0),
        'Ketu': (rashis[(lagna_index + 7) % 12], 10.0),
    }

_GOLD_SCENARIOS = {'gold-pass', 'gold-cap', 'gold-unknown'}

_ANNAPRASANA_CHART_SCENARIOS = {
    'annaprasana-pass',
    'annaprasana-preference-miss',
    'annaprasana-hard-fail',
    'annaprasana-unknown',
}

_KARNAVEDHA_CHART_SCENARIOS = {
    'karnavedha-pass', 'karnavedha-chart-unknown', 'karnavedha-bounded',
}

_VIDYARAMBHA_CHART_SCENARIOS = {
    'vidyarambha-pass',
    'vidyarambha-preference-miss',
    'vidyarambha-hard-fail',
    'vidyarambha-unknown',
}

_COURT_CHART_SCENARIOS = {
    'court-pass', 'court-preference-miss', 'court-hard-fail', 'court-unknown',
}

def _gold_muhurta_planets(scenario, canonical_lagna, gold_template):
    """Keep longitudes coherent while applying a controlled Gold outcome."""
    planets = [
        dict(planet)
        for planet in (gold_template or _gold_pass_planets(canonical_lagna))
    ]
    rashis = list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena']
    lagna_index = rashis.index(canonical_lagna)
    for planet in planets:
        planet['house'] = (
            rashis.index(planet['rashi']) - lagna_index
        ) % 12 + 1
    if scenario == 'gold-cap':
        for name, rashi in (('Surya', 'Tula'), ('Chandra', 'Vrischika')):
            next(item for item in planets if item['name'] == name).update({
                'rashi': rashi,
                'degree': 1.0,
                'house': (rashis.index(rashi) - lagna_index) % 12 + 1,
            })
    elif scenario == 'gold-unknown':
        next(item for item in planets if item['name'] == 'Surya')[
            'degree'
        ] = 10.0
    return planets

def _annaprasana_house_overrides(scenario):
    overrides = {}
    if scenario != 'annaprasana-preference-miss':
        overrides['Guru'] = 1
    if scenario == 'annaprasana-hard-fail':
        overrides['Surya'] = 1
    elif scenario == 'annaprasana-unknown':
        overrides.update({'Chandra': 1, 'Surya': 7})
    return overrides

def _vidyarambha_house_overrides(scenario, chart_index):
    overrides = {'Budha': 9, 'Shukra': 9, 'Guru': 9, 'Rahu': 5}
    if scenario == 'vidyarambha-preference-miss':
        overrides['Guru'] = 10
    elif scenario == 'vidyarambha-hard-fail':
        overrides['Surya'] = 8
    elif scenario == 'vidyarambha-unknown' and chart_index % 2:
        overrides['Guru'] = 10
    return overrides

def _court_house_overrides(scenario):
    houses = {'Guru': 1, 'Kuja': 1, 'Budha': 7, 'Rahu': 2}
    if scenario == 'court-preference-miss':
        houses.update({'Guru': 2, 'Kuja': 2, 'Budha': 2})
    elif scenario == 'court-hard-fail':
        houses['Shani'] = 6
    elif scenario == 'court-unknown':
        houses.update({'Surya': 12, 'Chandra': 6})
    return houses

def _muhurta_house_overrides(scenario, chart_index):
    if scenario in _ANNAPRASANA_CHART_SCENARIOS:
        return _annaprasana_house_overrides(scenario)
    if scenario in _KARNAVEDHA_CHART_SCENARIOS:
        # Mean nodes remain opposite while neither occupies house 8.
        return {'Rahu': 1, 'Ketu': 7}
    if scenario in {'positive', 'profile'}:
        # Both generic-purchase preferences pass; travel's Kuja exclusion also
        # passes. Other houses deliberately stay compact and deterministic.
        return {'Chandra': 1, 'Shukra': 1, 'Kuja': 2}
    if scenario == 'failure':
        return {'Kuja': 8}
    if scenario == 'mixed':
        # Alternating Chandra makes the preference genuinely mixed within the
        # offered window without inventing a hard rejection.
        return {'Chandra': 1 if chart_index % 2 == 0 else 2, 'Shukra': 1}
    if scenario in _VIDYARAMBHA_CHART_SCENARIOS:
        return _vidyarambha_house_overrides(scenario, chart_index)
    if scenario in _COURT_CHART_SCENARIOS:
        return _court_house_overrides(scenario)
    return {}

def _planets_from_houses(houses, canonical_lagna):
    rashis = list(MUHURTA_PLANET_RASHIS) + ['Makara', 'Kumbha', 'Meena']
    lagna_index = rashis.index(canonical_lagna)
    return [
        {
            'name': name,
            'rashi': rashis[(lagna_index + houses[name] - 1) % 12],
            'degree': 10 if name in {'Rahu', 'Ketu'} else index + 0.25,
            'house': houses[name],
            'retrograde': name in {'Shani', 'Rahu', 'Ketu'},
        }
        for index, name in enumerate(MUHURTA_PLANET_NAMES)
    ]

def _muhurta_planets(
    scenario, chart_index, canonical_lagna, gold_template=None,
):
    """Return strict planets whose Rashis encode scenario-specific houses."""
    if scenario in _GOLD_SCENARIOS:
        return _gold_muhurta_planets(
            scenario, canonical_lagna, gold_template,
        )
    houses = {name: 2 for name in MUHURTA_PLANET_NAMES}
    houses.update(_muhurta_house_overrides(scenario, chart_index))
    houses['Ketu'] = (houses['Rahu'] + 5) % 12 + 1
    planets = _planets_from_houses(houses, canonical_lagna)
    if scenario in {'annaprasana-unknown', 'court-unknown'}:
        next(item for item in planets if item['name'] == 'Surya')[
            'degree'] = 10.0
        next(item for item in planets if item['name'] == 'Chandra')[
            'degree'] = 10.0
    return planets
