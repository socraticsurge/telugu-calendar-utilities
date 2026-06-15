from datetime import datetime, timezone, date
from unittest.mock import patch
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    moon_sun_elongation, moon_longitude, sun_longitude, get_sunset,
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

@patch('telugu_panchangam.engines.utils.swe.rise_trans')
def test_get_sunset(mock_rise_trans):
    import swisseph as swe
    mock_rise_trans.return_value = (0, (2451545.5,))

    jd_start = 2451545.0
    geopos = [78.4744, 17.3850, 0.0]

    result = get_sunset(jd_start, geopos)

    assert result == 2451545.5
    mock_rise_trans.assert_called_once_with(
        jd_start, swe.SUN, swe.CALC_SET, geopos, 1013.25, 15.0
    )
