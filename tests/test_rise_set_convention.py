"""Independent solar oracle and Swiss convention experiments for issue 177.

These tests do not change the frozen engine or certify polar engine outputs.
"""
import json
from datetime import date, datetime
from pathlib import Path

import pytest
import swisseph as swe

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.utils import (
    get_sunrise,
    get_sunset,
    jd_to_utc,
    local_midnight_jd,
)

ORACLE = json.loads(
    (Path(__file__).parent / 'fixtures/rise_set_convention_oracle.json').read_text())


@pytest.mark.parametrize('case', ORACLE['cases'], ids=lambda c: c['city'] + c['date'])
def test_current_solar_convention_matches_independent_published_minutes(case):
    city = next(city for city in CITIES if city.name == case['city'])
    midnight = local_midnight_jd(date.fromisoformat(case['date']), city.timezone)
    geopos = (city.lon, city.lat, 0.0)
    sunrise = get_sunrise(midnight, geopos)
    sunset = get_sunset(sunrise, geopos)
    for key, actual, event in (
        ('sunrise', sunrise, swe.CALC_RISE),
        ('sunset', sunset, swe.CALC_SET),
    ):
        expected = datetime.fromisoformat(case['published'][key])
        assert abs((jd_to_utc(actual) - expected).total_seconds()) <= ORACLE['tolerance_seconds']
        status, candidate = swe.rise_trans(
            midnight, swe.SUN, event | swe.BIT_HINDU_RISING, geopos, 1013.25, 15.0)
        assert status == 0
        # This alternate convention is distinguishable in each source cell.
        assert abs((jd_to_utc(candidate[0]) - expected).total_seconds()) > 120


@pytest.mark.parametrize('event', [swe.CALC_RISE, swe.CALC_SET])
def test_observer_atmosphere_experiment_has_measurable_pressure_temperature_effect(event):
    midnight = local_midnight_jd(date(2026, 1, 1), 'Asia/Kolkata')
    def event_jd(altitude, pressure, temperature):
        status, values = swe.rise_trans(
            midnight, swe.SUN, event, (78.4867, 17.385, altitude), pressure, temperature)
        assert status == 0
        return values[0]
    baseline = event_jd(0, 1013.25, 15)
    altitude_only = event_jd(531, 1013.25, 15)
    automatic_pressure = event_jd(531, 0, 15)
    colder_air = event_jd(0, 1013.25, 0)
    assert abs(altitude_only - baseline) * 86400 < 1
    assert 5 < abs(automatic_pressure - baseline) * 86400 < 30
    assert 5 < abs(colder_air - baseline) * 86400 < 30


@pytest.mark.parametrize('day', [date(2026, 6, 21), date(2026, 12, 21)])
@pytest.mark.parametrize('event', [swe.CALC_RISE, swe.CALC_SET])
def test_swiss_polar_no_event_is_a_status_not_a_timestamp(day, event):
    status, values = swe.rise_trans(
        local_midnight_jd(day, 'Europe/Oslo'), swe.SUN, event,
        (18.9553, 69.6492, 0), 1013.25, 15)
    assert status == -2
    assert values[0] == 0


@pytest.mark.parametrize('event', [swe.CALC_RISE, swe.CALC_SET])
def test_swiss_polar_moon_no_event_uses_the_same_status_contract(event):
    status, values = swe.rise_trans(
        local_midnight_jd(date(2026, 12, 21), 'Europe/Oslo'), swe.MOON, event,
        (18.9553, 69.6492, 0), 1013.25, 15)
    assert status == -2
    assert values[0] == 0


def test_swiss_invalid_body_raises_instead_of_returning_an_event():
    jd = swe.julday(2026, 1, 1)
    with pytest.raises(swe.Error):
        swe.rise_trans(jd, -999, swe.CALC_RISE, (0, 0, 0))
