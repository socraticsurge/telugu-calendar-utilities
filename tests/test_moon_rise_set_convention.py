"""Research-only lunar mode comparisons; no frozen helper changes."""
import json
from datetime import datetime
from pathlib import Path

import pytest
import swisseph as swe

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.utils import jd_to_utc, local_midnight_jd

ORACLE = json.loads((Path(__file__).parent / 'fixtures/moon_rise_set_convention_oracle.json').read_text())
EVENTS = {'moonrise': swe.CALC_RISE, 'moonset': swe.CALC_SET}


def mode_difference(city, expected, event, flags):
    # A Panchang page can print a next-civil-day event before the next sunrise.
    midnight = local_midnight_jd(expected.date(), city.timezone)
    status, values = swe.rise_trans(
        midnight, swe.MOON, event | flags, (city.lon, city.lat, 0), 1013.25, 15)
    assert status == 0
    return abs((jd_to_utc(values[0]) - expected).total_seconds())


@pytest.mark.parametrize('case', ORACLE['cases'], ids=lambda c: c['city'] + c['page_date'])
def test_topocentric_centre_no_refraction_matches_labeled_published_moon_events(case):
    city = next(city for city in CITIES if city.name == case['city'])
    for name, published in case['published'].items():
        expected = datetime.fromisoformat(published)
        candidate = mode_difference(city, expected, EVENTS[name], swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION)
        current = mode_difference(city, expected, EVENTS[name], 0)
        assert candidate <= ORACLE['tolerance_seconds']
        assert current > ORACLE['tolerance_seconds']


def test_full_hindu_rising_flag_is_not_an_equivalent_moon_correction():
    differences = []
    for case in ORACLE['cases']:
        city = next(city for city in CITIES if city.name == case['city'])
        for name, published in case['published'].items():
            differences.append(mode_difference(
                city, datetime.fromisoformat(published), EVENTS[name], swe.BIT_HINDU_RISING))
    assert max(differences) > 20 * 60
