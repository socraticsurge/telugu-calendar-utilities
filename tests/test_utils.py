from datetime import date, datetime, timezone
from unittest.mock import patch

from telugu_panchangam.engines.utils import (
    datetime_to_jd,
    get_moonrise,
    get_moonset,
    get_sunrise,
    get_sunset,
    jd_to_utc,
    local_midnight_jd,
    moon_sun_elongation,
    next_new_moon,
    previous_new_moon,
    sidereal_longitude,
    tropical_sun_longitude,
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

def test_rise_trans_functions():
    import swisseph as swe
    with patch('telugu_panchangam.engines.utils.swe.rise_trans') as mock_rise_trans:
        mock_rise_trans.return_value = (0, (2451545.123,))
        jd_start = 2451545.0
        geopos = [78.4867, 17.3850, 0.0]

        res = get_sunrise(jd_start, geopos)
        assert res == 2451545.123
        mock_rise_trans.assert_called_with(jd_start, swe.SUN, swe.CALC_RISE, geopos, 1013.25, 15.0)

        res = get_sunset(jd_start, geopos)
        assert res == 2451545.123
        mock_rise_trans.assert_called_with(jd_start, swe.SUN, swe.CALC_SET, geopos, 1013.25, 15.0)

        res = get_moonrise(jd_start, geopos)
        assert res == 2451545.123
        mock_rise_trans.assert_called_with(jd_start, swe.MOON, swe.CALC_RISE, geopos, 1013.25, 15.0)

        res = get_moonset(jd_start, geopos)
        assert res == 2451545.123
        mock_rise_trans.assert_called_with(jd_start, swe.MOON, swe.CALC_SET, geopos, 1013.25, 15.0)

@patch('telugu_panchangam.engines.utils.swe.rise_trans')
def test_get_sunset_mocked(mock_rise_trans):
    import swisseph as swe
    mock_rise_trans.return_value = (0, (2451545.5,))

    jd_start = 2451545.0
    geopos = [78.4744, 17.3850, 0.0]

    result = get_sunset(jd_start, geopos)

    assert result == 2451545.5
    mock_rise_trans.assert_called_once_with(
        jd_start, swe.SUN, swe.CALC_SET, geopos, 1013.25, 15.0
    )

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
        if jd == 0.0:
            return 12.19
        if jd == -1.0:
            return (-24.38) % 360.0
        return ((jd - 1.0) * 12.19) % 360.0

    res = previous_new_moon(mock_elong, 0.0)
    assert abs(res - (1.0 - 29.530589)) < 1e-4

@patch('telugu_panchangam.engines.utils.swe.set_sid_mode')
@patch('telugu_panchangam.engines.utils.swe.calc_ut', return_value=([370.5, 0, 0, 0, 0, 0], 0))
def test_sidereal_longitude_mocked(mock_calc_ut, mock_set_sid_mode):
    import swisseph as swe

    jd = 2451545.0
    planet = swe.SUN

    result = sidereal_longitude(jd, planet)

    mock_set_sid_mode.assert_called_once_with(swe.SIDM_LAHIRI)
    expected_flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    mock_calc_ut.assert_called_once_with(jd, planet, expected_flags)

    assert result == 10.5


def test_tropical_sun_longitude_known_value():
    # JD 2451545.0 corresponds to Jan 1.5, 2000 (J2000 epoch)
    # The expected tropical sun longitude is ~280.3689 degrees
    jd = 2451545.0
    val = tropical_sun_longitude(jd)
    assert abs(val - 280.3689) < 1e-4

def test_get_moonset():
    import swisseph as swe
    jd_start = 2460476.5
    geopos = [78.4867, 17.3850, 0.0]
    expected_ret = 123.45
    mock_tret = (expected_ret, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    with patch('swisseph.rise_trans', return_value=(0, mock_tret)) as mock_rise_trans:
        result = get_moonset(jd_start, geopos)

        mock_rise_trans.assert_called_once_with(
            jd_start, swe.MOON, swe.CALC_SET, geopos, 1013.25, 15.0
        )
        assert result == expected_ret

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
    assert min(elong, 360.0 - elong) < 1e-4

    # The next new moon should be in March 2024.
    dt_nm = jd_to_utc(next_nm_jd)
    assert dt_nm.year == 2024
    assert dt_nm.month == 3
    assert 9 <= dt_nm.day <= 11  # New moon was around March 10.
