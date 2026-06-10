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


def test_list_eclipses_in_range_finds_known_lunar():
    from telugu_panchangam.eclipses import list_eclipses_in_range
    from telugu_panchangam.engines.utils import local_midnight_jd
    from datetime import date
    jd_start = local_midnight_jd(date(2025, 9, 1), 'Asia/Kolkata')
    jd_end = local_midnight_jd(date(2025, 9, 30), 'Asia/Kolkata')
    eclipses = list_eclipses_in_range(jd_start, jd_end)
    kinds = [e['kind'] for e in eclipses]
    assert 'Lunar' in kinds


def test_list_eclipses_in_range_no_eclipse_empty_period():
    from telugu_panchangam.eclipses import list_eclipses_in_range
    from telugu_panchangam.engines.utils import local_midnight_jd
    from datetime import date
    jd_start = local_midnight_jd(date(2024, 6, 14), 'UTC')
    jd_end = local_midnight_jd(date(2024, 6, 16), 'UTC')
    eclipses = list_eclipses_in_range(jd_start, jd_end)
    assert eclipses == []


def test_get_eclipse_from_precomputed_matches_get_eclipse_for_date():
    from telugu_panchangam.eclipses import (
        list_eclipses_in_range, get_eclipse_from_precomputed, get_eclipse_for_date
    )
    from telugu_panchangam.engines.utils import local_midnight_jd
    from datetime import date
    eclipse_date = date(2025, 9, 7)
    jd_start = local_midnight_jd(date(2025, 9, 1), 'Asia/Kolkata')
    jd_end = local_midnight_jd(date(2025, 9, 30), 'Asia/Kolkata')
    precomputed = list_eclipses_in_range(jd_start, jd_end)
    HYD = next(c for c in __import__('telugu_panchangam.cities', fromlist=['CITIES']).CITIES if c.name == 'Hyderabad')
    direct = get_eclipse_for_date(eclipse_date, HYD)
    from_cache = get_eclipse_from_precomputed(eclipse_date, precomputed, HYD)
    assert direct is not None
    assert from_cache is not None
    assert direct.kind == from_cache.kind
    assert direct.subtype == from_cache.subtype
    assert direct.visible == from_cache.visible
    assert direct.start == from_cache.start
    assert direct.end == from_cache.end
    assert direct.sutak_start == from_cache.sutak_start
    assert direct.sutak_end == from_cache.sutak_end
