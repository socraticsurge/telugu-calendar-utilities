from datetime import date
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.cities import CITIES

HYD = next(c for c in CITIES if c.name == 'Hyderabad')


def test_no_eclipse_returns_none():
    result = get_eclipse_for_date(date(2024, 6, 15), HYD)
    assert result is None


def test_total_lunar_eclipse_visible():
    result = get_eclipse_for_date(date(2025, 9, 7), HYD)
    assert result is not None
    assert result.kind == 'Lunar'
    assert result.subtype == 'Total'
    assert result.visible is True
    assert result.start < result.end
    assert result.sutak_start is not None
    assert result.sutak_start < result.start
    assert result.sutak_end == result.end


def test_solar_eclipse_not_visible_from_hyderabad():
    result = get_eclipse_for_date(date(2026, 2, 17), HYD)
    assert result is not None
    assert result.kind == 'Solar'
    assert result.subtype == 'Annular'
    assert result.visible is False
    assert result.sutak_start is None
    assert result.sutak_end is None
