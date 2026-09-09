"""Smoke tests for the lagna.json generator. Verifies shape, in-range
indices, monotonic minute offsets, and timezone-aware sunrise."""
from datetime import date, timedelta
from itertools import pairwise

import pytest

from scripts.build_lagna_json import build_for_city
from telugu_panchangam.cities import CITIES
from telugu_panchangam.panchangam_names import RASHI_NAMES

ANNUAL_CYCLE_CITIES = ('Hyderabad', 'London', 'New York', 'Sydney')


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
        assert len(d['sunrise']) == 5
        assert d['sunrise'][2] == ':'
        assert isinstance(d['guruCombust'], bool)
        assert isinstance(d['shukraCombust'], bool)
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


def test_rounded_zero_duration_terminal_transition_is_omitted():
    """A final sub-minute window must not become a zero-width JSON cell."""
    for city_name in ('Hyderabad', 'Delhi'):
        city = next(c for c in CITIES if c.name == city_name)
        row = build_for_city(city, date(2026, 9, 17), 1)['days'][0]
        offsets = [offset for offset, _ in row['transitions']]

        assert offsets[-1] < row['cycleEnd']
        assert row['cycleEnd'] not in offsets


def test_rounded_zero_duration_initial_transition_is_omitted():
    """A sub-minute sunrise cell must not become a zero-width JSON cell."""
    row = build_for_city(_hyderabad(), date(2026, 5, 16), 1)['days'][0]

    assert row['lagna0'] == 1
    assert row['transitions'][0][0] > 0


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


@pytest.mark.parametrize('city_name', ANNUAL_CYCLE_CITIES)
def test_annual_multi_city_feed_covers_one_sunrise_cycle(city_name):
    """Protect the repaired generator across a full year and both hemispheres.

    The former ``sunrise + 1 Julian day`` seed could land after the immediately
    following sunrise and make Swiss Ephemeris return the *second* following
    sunrise.  That produced 24/25-transition, roughly 2880-minute artifacts on
    127 Hyderabad dates in the original #244 audit.  The sunset-seeded boundary
    must instead produce exactly one ordered zodiac cycle on every 2026 date,
    including the London, New York, and Sydney DST transitions.
    """
    city = next(candidate for candidate in CITIES if candidate.name == city_name)
    start = date(2026, 1, 1)
    rows = build_for_city(city, start, 365)['days']

    assert [row['date'] for row in rows] == [
        (start + timedelta(days=offset)).isoformat()
        for offset in range(365)
    ]

    for row in rows:
        offsets = [offset for offset, _ in row['transitions']]
        rashis = [row['lagna0'], *(index for _, index in row['transitions'])]

        assert offsets == sorted(set(offsets))
        assert all(0 < offset < row['cycleEnd'] for offset in offsets)
        assert 1430 <= row['cycleEnd'] <= 1450
        assert len(rashis) in (13, 14)
        assert set(rashis) == set(range(12))
        assert all(
            following == (current + 1) % 12
            for current, following in pairwise(rashis)
        )
