from datetime import datetime, timezone, date
from telugu_panchangam.engines.utils import (
    datetime_to_jd, jd_to_utc, local_midnight_jd, find_crossing,
    moon_sun_elongation, moon_longitude, sun_longitude,
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

def test_sidereal_longitude_mocked(mocker):
    import swisseph as swe
    from telugu_panchangam.engines.utils import sidereal_longitude

    mock_set_sid_mode = mocker.patch('telugu_panchangam.engines.utils.swe.set_sid_mode')
    mock_calc_ut = mocker.patch('telugu_panchangam.engines.utils.swe.calc_ut', return_value=([370.5, 0, 0, 0, 0, 0], 0))

    jd = 2451545.0
    planet = swe.SUN

    result = sidereal_longitude(jd, planet)

    mock_set_sid_mode.assert_called_once_with(swe.SIDM_LAHIRI)
    expected_flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    mock_calc_ut.assert_called_once_with(jd, planet, expected_flags)

    assert result == 10.5
