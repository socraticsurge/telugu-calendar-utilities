# Maudhya (Asta/Udaya) calendar tests.
#
# Dates verified against drikpanchang.com Asta/Udaya pages for Hyderabad 2026.
# DP reference:
#   Saturn:   Asta 2026-03-13 19:13 IST (13:43 UTC) — Udaya 2026-04-22 04:49 IST (23:19 UTC)
#   Mars:     Udaya 2026-05-03 04:30 IST (~23:00 UTC May 2)
#   Jupiter:  Asta 2026-07-15 19:59 IST (14:29 UTC) — Udaya 2026-08-12 05:03 IST (23:33 UTC Aug 11)
#   Venus:    Udaya 2026-02-01 18:27 IST (12:57 UTC)
#
# Tolerance: ±2 days for all events (heliacal visibility is location/atmosphere dependent).
# Expected accuracy vs DP: Saturn <30 min, Jupiter/Venus <1 day, Mars <2 days.
from datetime import date, datetime, timezone

import pytest

from telugu_panchangam.maudhya_calendar import (
    PLANET_NAMES,
    CombustionPeriod,
    combustion_periods,
)
from telugu_panchangam.models.panchangam_day import Location

# Hyderabad reference location (DP reference city for 2026 calibration).
HYD = Location('Hyderabad', lat=17.3850, lon=78.4867, timezone='Asia/Kolkata', alt=531)


def _find(periods: list[CombustionPeriod], planet: str) -> list[CombustionPeriod]:
    return [p for p in periods if p.planet == planet]


def _dt(y, m, d, h=0, mn=0) -> datetime:
    return datetime(y, m, d, h, mn, tzinfo=timezone.utc)


# ── Basic structural tests ─────────────────────────────────────────────────────

def test_returns_list():
    r = combustion_periods(date(2026, 7, 1), date(2026, 8, 31), HYD)
    assert isinstance(r, list)


def test_all_entries_are_combustion_period():
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD)
    for item in r:
        assert isinstance(item, CombustionPeriod)
        assert item.planet in PLANET_NAMES
        assert isinstance(item.enters, datetime)
        assert item.exits is None or isinstance(item.exits, datetime)


def test_sorted_by_entry_time():
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD)
    times = [p.enters for p in r]
    assert times == sorted(times)


def test_enters_before_exits():
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD)
    for p in r:
        if p.exits is not None:
            assert p.enters < p.exits, f'{p.planet}: enters={p.enters} not before exits={p.exits}'


def test_planet_filter():
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD, planets=['Saturn'])
    assert all(p.planet == 'Saturn' for p in r)


def test_invalid_planet_raises():
    start = date(2026, 1, 1)
    end = date(2026, 12, 31)
    with pytest.raises(ValueError, match='Unknown'):
        combustion_periods(start, end, HYD, planets=['Pluto'])


# ── DP-verified dates (Hyderabad 2026) ────────────────────────────────────────

def test_saturn_asta_2026_enters_within_2_days():
    r = combustion_periods(date(2026, 2, 1), date(2026, 12, 31), HYD, planets=['Saturn'])
    assert len(r) >= 1
    s = r[0]
    assert s.planet == 'Saturn'
    # DP: 2026-03-13 13:43 UTC
    assert abs((s.enters - _dt(2026, 3, 13, 13, 43)).total_seconds()) < 2 * 86400, (
        f'Saturn enters {s.enters} too far from DP 2026-03-13 13:43 UTC'
    )


def test_saturn_asta_2026_exits_within_2_days():
    r = combustion_periods(date(2026, 2, 1), date(2026, 12, 31), HYD, planets=['Saturn'])
    s = r[0]
    assert s.exits is not None
    # DP: 2026-04-21 23:19 UTC
    assert abs((s.exits - _dt(2026, 4, 21, 23, 19)).total_seconds()) < 2 * 86400, (
        f'Saturn exits {s.exits} too far from DP 2026-04-21 23:19 UTC'
    )


def test_mars_udaya_2026_within_2_days():
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD, planets=['Mars'])
    # Mars was combust since Nov 2025; exits in May 2026.
    assert len(r) >= 1
    m = r[0]
    assert m.exits is not None
    # DP: ~2026-05-02 23:00 UTC
    assert abs((m.exits - _dt(2026, 5, 2, 23, 0)).total_seconds()) < 2 * 86400, (
        f'Mars exits {m.exits} too far from DP 2026-05-02 23:00 UTC'
    )


def test_jupiter_asta_2026_enters_within_2_days():
    r = combustion_periods(date(2026, 6, 1), date(2026, 12, 31), HYD, planets=['Jupiter'])
    assert len(r) >= 1
    j = r[0]
    # DP: 2026-07-15 14:29 UTC
    assert abs((j.enters - _dt(2026, 7, 15, 14, 29)).total_seconds()) < 2 * 86400, (
        f'Jupiter enters {j.enters} too far from DP 2026-07-15 14:29 UTC'
    )


def test_jupiter_asta_2026_exits_within_2_days():
    r = combustion_periods(date(2026, 6, 1), date(2026, 12, 31), HYD, planets=['Jupiter'])
    j = r[0]
    assert j.exits is not None
    # DP: 2026-08-11 23:33 UTC
    assert abs((j.exits - _dt(2026, 8, 11, 23, 33)).total_seconds()) < 2 * 86400, (
        f'Jupiter exits {j.exits} too far from DP 2026-08-11 23:33 UTC'
    )


def test_venus_udaya_feb_2026_within_2_days():
    r = combustion_periods(date(2026, 1, 1), date(2026, 3, 31), HYD, planets=['Venus'])
    # Venus was combust since ~Dec 2025, exits early Feb 2026.
    assert len(r) >= 1
    # Find the period whose exit is in Feb 2026
    v = next((p for p in r if p.exits and p.exits.month == 2), None)
    assert v is not None, 'No Venus period with exit in Feb 2026 found'
    # DP: 2026-02-01 12:57 UTC
    assert abs((v.exits - _dt(2026, 2, 1, 12, 57)).total_seconds()) < 2 * 86400, (
        f'Venus exits {v.exits} too far from DP 2026-02-01 12:57 UTC'
    )


# ── Completeness ──────────────────────────────────────────────────────────────

def test_mercury_has_multiple_periods_per_year():
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD, planets=['Mercury'])
    # Mercury has ~6 Asta periods per year (3 inferior + 3 superior conjunctions)
    assert len(r) >= 4, f'Expected ≥4 Mercury periods, got {len(r)}'


def test_no_duplicate_planets_overlap():
    """No two periods for the same planet should overlap."""
    r = combustion_periods(date(2026, 1, 1), date(2026, 12, 31), HYD)
    by_planet: dict[str, list[CombustionPeriod]] = {}
    for p in r:
        by_planet.setdefault(p.planet, []).append(p)
    for planet, ps in by_planet.items():
        for i in range(len(ps) - 1):
            a, b = ps[i], ps[i + 1]
            if a.exits is not None:
                assert a.exits <= b.enters, (
                    f'{planet}: period {i} exits {a.exits} overlaps period {i+1} enters {b.enters}'
                )
