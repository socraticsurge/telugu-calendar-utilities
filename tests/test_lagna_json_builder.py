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
        # increasing and stay strictly inside the day cycle.
        offsets = [t[0] for t in d['transitions']]
        assert offsets == sorted(offsets)
        assert all(0 < o < d['cycleEnd'] for o in offsets)
        # Each transition index is a valid rashi index.
        assert all(0 <= idx < 12 for _, idx in d['transitions'])
        # cycleEnd marks where the last visible rashi ends — i.e. the
        # start of the trailing partial wrap that duplicates the
        # leading rashi. Typically ~22h after sunrise for Hyderabad
        # (varies with latitude/season).
        assert 1200 <= d['cycleEnd'] < 1440
        # cycleEnd must be strictly later than the last transition.
        assert d['cycleEnd'] > offsets[-1]


def test_sunrise_is_local_time_not_utc():
    """For Hyderabad in summer, sunrise is ~05:30–06:00 IST, never 00:xx."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 1)
    sunrise = data['days'][0]['sunrise']
    hour = int(sunrise.split(':')[0])
    assert 4 <= hour <= 7, f'Expected IST sunrise hour 4-7, got {sunrise}'


def test_lagna_advances_through_12_rashis_in_a_day():
    """Over ~24h the ascendant should pass through all 12 signs once.
    With the trailing wrap dropped, lagna0 + the 11 transitions cover
    every rashi exactly once."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 1)
    d0 = data['days'][0]
    rashis = [d0['lagna0']] + [idx for _, idx in d0['transitions']]
    assert sorted(rashis) == list(range(12)), \
        f'expected each rashi once, got {sorted(rashis)}'


def test_diaspora_city_still_produces_valid_json():
    """Sanity check the southern-hemisphere / non-Asia-Kolkata path."""
    sydney = next(c for c in CITIES if c.name == 'Sydney')
    data = build_for_city(sydney, date(2026, 6, 15), 1)
    assert data['days']
    assert 0 <= data['days'][0]['lagna0'] < 12


def test_cell_count_is_consistent_across_consecutive_days():
    """The 24h panchangam slice can capture 13 OR 14 engine windows
    depending on how far past the leading rashi the cycle wraps before
    next sunrise. Both must collapse to the same 12 visible cells —
    that's a previous regression (2026-06-16 wrongly produced 13 cells
    next to 2026-06-15's 12)."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 5)
    counts = [1 + len(d['transitions']) for d in data['days']]
    assert all(c == 12 for c in counts), \
        f'expected 12 cells per day, got {counts}'
