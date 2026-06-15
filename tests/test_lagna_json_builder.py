"""Smoke tests for the lagna.json generator. Verifies shape, in-range
indices, monotonic minute offsets, and timezone-aware sunrise."""
from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.base import RASHI_NAMES
from scripts.build_lagna_json import build_for_city


def _hyderabad():
    return next(c for c in CITIES if c.name == 'Hyderabad')


def test_build_shape_and_indices_for_hyderabad():
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 3)
    assert data['city'] == 'Hyderabad'
    assert data['start'] == '2026-06-15'
    assert data['rasis'] == RASHI_NAMES
    assert len(data['days']) == 3
    for d in data['days']:
        assert 0 <= d['lagna0'] < 12
        assert len(d['sunrise']) == 5 and d['sunrise'][2] == ':'
        # Transitions are minutes from sunrise; should be strictly
        # increasing and stay below ~28h (since the lagna ribbon covers
        # ~24h plus the trailing partial window).
        offsets = [t[0] for t in d['transitions']]
        assert offsets == sorted(offsets)
        assert all(0 < o < 28 * 60 for o in offsets)
        # Each transition index is a valid rashi index.
        assert all(0 <= idx < 12 for _, idx in d['transitions'])


def test_sunrise_is_local_time_not_utc():
    """For Hyderabad in summer, sunrise is ~05:30–06:00 IST, never 00:xx."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 1)
    sunrise = data['days'][0]['sunrise']
    hour = int(sunrise.split(':')[0])
    assert 4 <= hour <= 7, f'Expected IST sunrise hour 4-7, got {sunrise}'


def test_lagna_advances_through_12_rashis_in_a_day():
    """Over ~24h the ascendant should pass through all 12 signs once,
    so the lagna0 sign should reappear among the transitions."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 1)
    d0 = data['days'][0]
    seen = {d0['lagna0']} | {idx for _, idx in d0['transitions']}
    assert seen == set(range(12)), f'missing rashis: {set(range(12)) - seen}'


def test_diaspora_city_still_produces_valid_json():
    """Sanity check the southern-hemisphere / non-Asia-Kolkata path."""
    sydney = next(c for c in CITIES if c.name == 'Sydney')
    data = build_for_city(sydney, date(2026, 6, 15), 1)
    assert data['days']
    assert 0 <= data['days'][0]['lagna0'] < 12
