"""Smoke tests for the lagna.json generator. Verifies shape, in-range
indices, monotonic minute offsets, and timezone-aware sunrise."""
from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.panchangam_names import RASHI_NAMES
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
        # cycleEnd is the engine cycle's end — i.e. next sunrise as
        # an offset from this day's sunrise. Should be ~1440 min (24h)
        # within a couple of minutes of seasonal sunrise drift.
        assert 1430 <= d['cycleEnd'] <= 1450
        # cycleEnd must be strictly later than the last transition.
        assert d['cycleEnd'] > offsets[-1]


def test_sunrise_is_local_time_not_utc():
    """For Hyderabad in summer, sunrise is ~05:30–06:00 IST, never 00:xx."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 1)
    sunrise = data['days'][0]['sunrise']
    hour = int(sunrise.split(':')[0])
    assert 4 <= hour <= 7, f'Expected IST sunrise hour 4-7, got {sunrise}'


def test_lagna_covers_all_12_rashis_in_a_day():
    """Over ~24h the ascendant passes through all 12 signs at least
    once. The leading rashi typically also appears as a trailing wrap
    (cycle is ~23h56m), so the set of distinct rashis seen equals
    exactly the 12 zodiac signs."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 1)
    d0 = data['days'][0]
    rashis = {d0['lagna0']} | {idx for _, idx in d0['transitions']}
    assert rashis == set(range(12)), \
        f'expected all 12 rashis, missing {set(range(12)) - rashis}'


def test_diaspora_city_still_produces_valid_json():
    """Sanity check the southern-hemisphere / non-Asia-Kolkata path."""
    sydney = next(c for c in CITIES if c.name == 'Sydney')
    data = build_for_city(sydney, date(2026, 6, 15), 1)
    assert data['days']
    assert 0 <= data['days'][0]['lagna0'] < 12


def test_cell_count_is_13_or_14_per_day():
    """The 24h panchangam slice captures 13 OR 14 engine windows
    depending on how far past the leading rashi the cycle has wrapped
    by next sunrise. Both are intellectually honest representations
    of the actual lagna cycle; we display all windows the engine
    returns so users see the cycle as it really unfolds, including
    the leading partial (tail of yesterday's wrap) and trailing
    partial(s) (start of tomorrow's leading rashi)."""
    data = build_for_city(_hyderabad(), date(2026, 6, 15), 7)
    counts = [1 + len(d['transitions']) for d in data['days']]
    assert all(c in (13, 14) for c in counts), \
        f'expected 13 or 14 cells per day, got {counts}'
