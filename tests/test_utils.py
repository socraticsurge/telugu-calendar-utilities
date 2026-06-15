from datetime import datetime, timezone, date
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    moon_sun_elongation, moon_longitude, sun_longitude,
    previous_new_moon, next_new_moon,
)

def test_datetime_to_jd_known_value():
    # J2000.0 epoch: Jan 1.5, 2000 = JD 2451545.0
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    assert abs(jd - 2451545.0) < 1e-5

def test_jd_to_utc_roundtrip():
    dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    jd = datetime_to_jd(dt)
    dt2 = jd_to_utc(jd)
    assert abs((dt2 - dt).total_seconds()) < 1

def test_local_midnight_jd_kolkata():
    # Kolkata is UTC+5:30, so midnight local = 18:30 UTC previous day
    d = date(2024, 6, 15)
    jd = local_midnight_jd(d, 'Asia/Kolkata')
    utc_dt = jd_to_utc(jd)
    assert utc_dt.hour == 18
    assert utc_dt.minute == 30
    assert utc_dt.day == 14  # previous UTC day

def test_moon_sun_elongation_range():
    import swisseph as swe
    jd = swe.julday(2024, 3, 15, 0)
    elong = moon_sun_elongation(jd)
    assert 0.0 <= elong < 360.0


def test_previous_new_moon_mock():
    def mock_elongation(jd):
        return (jd * 12.0) % 360.0

    assert abs(previous_new_moon(mock_elongation, 30.0) - 30.0) < 1e-4
    assert abs(previous_new_moon(mock_elongation, 31.0) - 30.0) < 1e-4
    assert abs(previous_new_moon(mock_elongation, 29.0) - 0.0) < 1e-4


def test_next_new_moon_mock():
    def mock_elongation(jd):
        return (jd * 12.0) % 360.0

    assert abs(next_new_moon(mock_elongation, 1.0) - 30.0) < 1e-4
    assert abs(next_new_moon(mock_elongation, 30.0) - 60.0) < 1e-4


def test_previous_new_moon_real():
    import swisseph as swe
    jd_start = swe.julday(2024, 4, 10, 0)
    nm_jd = previous_new_moon(moon_sun_elongation, jd_start)
    elong = moon_sun_elongation(nm_jd)
    assert elong < 1e-4 or abs(elong - 360.0) < 1e-4

    next_nm_jd = next_new_moon(moon_sun_elongation, jd_start)
    elong_next = moon_sun_elongation(next_nm_jd)
    assert elong_next < 1e-4 or abs(elong_next - 360.0) < 1e-4
    assert next_nm_jd > jd_start


def test_previous_new_moon_overshoot():
    # Test case where initial approximation lands ahead of target, requiring backward jump
    def mock_elong(jd):
        if jd == 0.0: return 12.19
        if jd == -1.0: return (-24.38) % 360.0
        return ((jd - 1.0) * 12.19) % 360.0

    res = previous_new_moon(mock_elong, 0.0)
    assert abs(res - (1.0 - 29.530589)) < 1e-4
