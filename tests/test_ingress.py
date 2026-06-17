# Rashi ingress calendar tests.
#
# Reference dates verified via cross-check with panchangam Sankramanam dates
# (Sun ingress) and computed Jupiter/Rahu positions for 2026.
from datetime import date, datetime, timezone

import pytest

from telugu_panchangam.ingress import rashi_ingresses, RashiIngress, INGRESS_PLANETS


def _dt(y, m, d) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


# ── Structural tests ───────────────────────────────────────────────────────────

def test_returns_list():
    assert isinstance(rashi_ingresses(date(2026, 1, 1), date(2026, 3, 31)), list)


def test_all_entries_are_rashi_ingress():
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31))
    for r in results:
        assert isinstance(r, RashiIngress)
        assert r.planet in INGRESS_PLANETS
        assert isinstance(r.rashi, str) and len(r.rashi) > 0
        assert isinstance(r.enters, datetime)
        assert r.exits is None or isinstance(r.exits, datetime)


def test_sorted_by_entry_time():
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31))
    times = [r.enters for r in results]
    assert times == sorted(times)


def test_exits_after_enters():
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31))
    for r in results:
        if r.exits is not None:
            assert r.enters < r.exits, f'{r.planet} in {r.rashi}: enters {r.enters} >= exits {r.exits}'


def test_planet_filter():
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31), planets=['Mars'])
    assert all(r.planet == 'Mars' for r in results)
    assert len(results) >= 1


def test_invalid_planet_raises():
    with pytest.raises(ValueError, match='Unknown'):
        rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31), planets=['Neptune'])


# ── Reference date tests ───────────────────────────────────────────────────────

def test_sun_makara_sankramanam_jan_2026():
    """Makara Sankramanam 2026 falls on Jan 14 — matches panchangam reference."""
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 2, 28), planets=['Sun'])
    makara = next((r for r in results if r.rashi == 'Makara'), None)
    assert makara is not None
    assert makara.enters.day == 14
    assert makara.enters.month == 1
    assert makara.enters.year == 2026


def test_sun_mesha_sankramanam_apr_2026():
    """Mesha Sankramanam 2026 falls on Apr 14."""
    results = rashi_ingresses(date(2026, 4, 1), date(2026, 5, 15), planets=['Sun'])
    mesha = next((r for r in results if r.rashi == 'Mesha'), None)
    assert mesha is not None
    assert mesha.enters.month == 4
    assert mesha.enters.day == 14


def test_sun_has_12_ingresses_per_year():
    """Sun crosses all 12 rashis in a year."""
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31), planets=['Sun'])
    rashis_visited = {r.rashi for r in results}
    assert len(results) == 12, f'Expected 12 Sun ingresses, got {len(results)}'
    assert len(rashis_visited) == 12


def test_jupiter_enters_karka_jun_2026():
    """Jupiter enters Karka (Cancer) in June 2026."""
    results = rashi_ingresses(date(2026, 5, 1), date(2026, 7, 31), planets=['Jupiter'])
    karka = next((r for r in results if r.rashi == 'Karka'), None)
    assert karka is not None
    assert karka.enters.month == 6


def test_rahu_ketu_ingress_dec_2026():
    """Rahu enters Makara and Ketu enters Karka on the same date in Dec 2026."""
    results = rashi_ingresses(date(2026, 11, 1), date(2026, 12, 31), planets=['Rahu', 'Ketu'])
    rahu  = next((r for r in results if r.planet == 'Rahu'), None)
    ketu  = next((r for r in results if r.planet == 'Ketu'), None)
    assert rahu is not None and rahu.rashi == 'Makara'
    assert ketu is not None and ketu.rashi == 'Karka'
    assert abs((rahu.enters - ketu.enters).total_seconds()) < 60, (
        'Rahu and Ketu must enter their respective signs simultaneously'
    )


def test_saturn_stable_in_meena_all_2026():
    """Saturn stays in Meena the entire year — no ingress in 2026."""
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31), planets=['Saturn'])
    assert len(results) == 0, f'Expected 0 Saturn ingresses in 2026, got {len(results)}'


def test_mars_changes_sign_multiple_times():
    """Mars moves through several rashis per year."""
    results = rashi_ingresses(date(2026, 1, 1), date(2026, 12, 31), planets=['Mars'])
    assert len(results) >= 6, f'Expected ≥6 Mars ingresses, got {len(results)}'
