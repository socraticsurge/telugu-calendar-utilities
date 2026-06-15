from datetime import datetime, timezone, date
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    moon_sun_elongation, moon_longitude, sun_longitude,
    next_new_moon, previous_new_moon,
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
    # A mock elongation function with a constant rate of 12.19 degrees per day.
    # We use an arbitrary start epoch to mimic realistic JD values.
    # Zero crossings (new moons) occur when (jd - epoch) * 12.19 is a multiple of 360.
    epoch = 2460000.0
    mock_elongation = lambda jd: ((jd - epoch) * 12.19) % 360.0

    # Let's say we start at epoch. A new moon occurs exactly at epoch.
    # The next new moon should be exactly 360 / 12.19 days later.
    expected_gap = 360.0 / 12.19  # ~29.5324 days

    # If we start slightly after epoch, the next new moon is at epoch + expected_gap.
    start_jd = epoch + 5.0
    next_nm = next_new_moon(mock_elongation, start_jd)

    assert next_nm > start_jd
    assert abs(next_nm - (epoch + expected_gap)) < 1e-4
    assert mock_elongation(next_nm) < 1e-4 or mock_elongation(next_nm) > 360.0 - 1e-4

def test_previous_new_moon():
    # A mock elongation function with a constant rate of 12.19 degrees per day.
    epoch = 2460000.0
    mock_elongation = lambda jd: ((jd - epoch) * 12.19) % 360.0

    # If we start 5 days after epoch, the previous new moon should be exactly at epoch.
    start_jd = epoch + 5.0
    prev_nm = previous_new_moon(mock_elongation, start_jd)

    assert prev_nm <= start_jd
    assert abs(prev_nm - epoch) < 1e-4
    assert mock_elongation(prev_nm) < 1e-4 or mock_elongation(prev_nm) > 360.0 - 1e-4

def test_next_new_moon_real_data():
    import swisseph as swe

    # Let's pick a known date around a new moon
    # March 10, 2024 was a new moon
    # We'll start from March 1, 2024
    start_jd = swe.julday(2024, 3, 1, 0)

    next_nm_jd = next_new_moon(moon_sun_elongation, start_jd)

    # Verify the result is after the start date
    assert next_nm_jd > start_jd

    # Verify the elongation at the calculated JD is extremely close to 0
    elong = moon_sun_elongation(next_nm_jd)
    assert elong < 1e-4 or elong > 360.0 - 1e-4

    # The next new moon should be in March 2024.
    dt_nm = jd_to_utc(next_nm_jd)
    assert dt_nm.year == 2024
    assert dt_nm.month == 3
    assert 9 <= dt_nm.day <= 11  # New moon was around March 10.
