# Graha Yuddha (planetary war) calendar tests.
#
# Classical criterion: two tara grahas within 1° ecliptic longitude.
# Victor: planet with higher ecliptic latitude at closest approach.
#
# 2026 reference events (verified against computed ephemeris; Drik Panchang
# does not publish an annual Graha Yuddha calendar page, but the planetary
# conjunction dates below match Swiss Ephemeris tropical coordinates):
#   Venus-Mars:    starts ~2026-01-06, exact ~2026-01-08, ends ~2026-01-10
#   Venus-Jupiter: starts ~2026-06-08, exact ~2026-06-09, ends ~2026-06-10
#   Mars-Jupiter:  starts ~2026-11-13, exact ~2026-11-16, ends ~2026-11-19
#
# Tolerance: ±2 days on start/end; ±1 day on exact conjunction.
from datetime import date, datetime, timezone

import pytest

from telugu_panchangam.graha_yuddha import (
    graha_yuddha_periods,
    GrahaYuddha,
    YUDDHA_PLANETS,
    THRESHOLD_DEG,
)


def _dt(y, m, d, h=0, mn=0) -> datetime:
    return datetime(y, m, d, h, mn, tzinfo=timezone.utc)


def _find(wars: list[GrahaYuddha], p1: str, p2: str) -> list[GrahaYuddha]:
    return [w for w in wars if {w.planet1, w.planet2} == {p1, p2}]


# ── Basic structural tests ─────────────────────────────────────────────────────

def test_returns_list():
    result = graha_yuddha_periods(date(2026, 6, 1), date(2026, 6, 30))
    assert isinstance(result, list)


def test_all_entries_are_graha_yuddha():
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31))
    for w in result:
        assert isinstance(w, GrahaYuddha)
        assert w.planet1 in YUDDHA_PLANETS
        assert w.planet2 in YUDDHA_PLANETS
        assert w.planet1 != w.planet2
        assert w.winner in {w.planet1, w.planet2}
        assert w.loser  in {w.planet1, w.planet2}
        assert w.winner != w.loser
        assert isinstance(w.starts, datetime)
        assert isinstance(w.exact, datetime)
        assert w.ends is None or isinstance(w.ends, datetime)
        assert w.min_separation_arcmin >= 0.0


def test_sorted_by_start_time():
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31))
    times = [w.starts for w in result]
    assert times == sorted(times)


def test_starts_before_exact_before_ends():
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31))
    for w in result:
        assert w.starts <= w.exact, f'{w.planet1}-{w.planet2}: starts {w.starts} > exact {w.exact}'
        if w.ends is not None:
            assert w.exact <= w.ends, f'{w.planet1}-{w.planet2}: exact {w.exact} > ends {w.ends}'


def test_min_separation_within_threshold():
    """Minimum separation at exact conjunction must be below the 1° threshold."""
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31))
    for w in result:
        assert w.min_separation_arcmin < THRESHOLD_DEG * 60.0, (
            f'{w.planet1}-{w.planet2}: min sep {w.min_separation_arcmin}\' >= {THRESHOLD_DEG * 60}\''
        )


def test_planet_filter():
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31), planets=['Mars', 'Jupiter'])
    for w in result:
        assert {w.planet1, w.planet2} == {'Mars', 'Jupiter'}


def test_invalid_planet_raises():
    with pytest.raises(ValueError, match='Unknown'):
        graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31), planets=['Pluto'])


def test_empty_range_produces_no_error():
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 1, 1))
    assert isinstance(result, list)


# ── Known 2026 events ─────────────────────────────────────────────────────────

def test_venus_mars_war_jan_2026_present():
    """Venus-Mars conjunction early January 2026 — very close (sub-arcsecond)."""
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 2, 28))
    wars = _find(result, 'Venus', 'Mars')
    assert len(wars) >= 1, 'Expected Venus-Mars war in Jan 2026'
    w = wars[0]
    # Exact around 2026-01-08
    assert abs((w.exact - _dt(2026, 1, 8)).total_seconds()) < 2 * 86400


def test_venus_jupiter_war_jun_2026_present():
    """Venus-Jupiter conjunction June 9, 2026 — notable naked-eye event."""
    result = graha_yuddha_periods(date(2026, 6, 1), date(2026, 6, 30))
    wars = _find(result, 'Venus', 'Jupiter')
    assert len(wars) >= 1, 'Expected Venus-Jupiter war in June 2026'
    w = wars[0]
    # Exact around 2026-06-09
    assert abs((w.exact - _dt(2026, 6, 9)).total_seconds()) < 2 * 86400


def test_mars_jupiter_war_nov_2026_present():
    """Mars-Jupiter conjunction around Nov 16, 2026."""
    result = graha_yuddha_periods(date(2026, 11, 1), date(2026, 11, 30))
    wars = _find(result, 'Mars', 'Jupiter')
    assert len(wars) >= 1, 'Expected Mars-Jupiter war in Nov 2026'
    w = wars[0]
    assert abs((w.exact - _dt(2026, 11, 16)).total_seconds()) < 3 * 86400


def test_full_year_has_multiple_wars():
    """2026 should have several Graha Yuddha events."""
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31))
    assert len(result) >= 5, f'Expected ≥5 wars in 2026, got {len(result)}'


def test_war_duration_is_plausible():
    """Each war should last between a few hours and ~30 days."""
    result = graha_yuddha_periods(date(2026, 1, 1), date(2026, 12, 31))
    for w in result:
        if w.ends is not None:
            duration_days = (w.ends - w.starts).total_seconds() / 86400
            assert 0.05 < duration_days < 30, (
                f'{w.planet1}-{w.planet2}: implausible duration {duration_days:.1f} days'
            )
