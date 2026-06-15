from datetime import datetime, timezone, date
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    moon_sun_elongation, moon_longitude, sun_longitude,
    previous_new_moon, next_new_moon
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

def test_next_new_moon():
    import swisseph as swe
    # Use a known date, e.g., March 15, 2024
    jd_start = swe.julday(2024, 3, 15, 0)

    # Calculate the next new moon
    jd_next = next_new_moon(moon_sun_elongation, jd_start)

    # Ensure it's strictly after jd_start
    assert jd_next > jd_start

    # Elongation at the next new moon should be close to 0 (or 360)
    elong = moon_sun_elongation(jd_next)
    assert elong < 0.1 or elong > 359.9

    # Ensure it's the *first* new moon after jd_start
    # The gap between jd_start and the next new moon should be <= a full lunar month (~29.53 days)
    assert jd_next - jd_start <= 29.6

    # Check that previous_new_moon applied to jd_next + a little offset gives jd_next back
    jd_prev = previous_new_moon(moon_sun_elongation, jd_next + 1.0)
    assert abs(jd_prev - jd_next) < 0.01
