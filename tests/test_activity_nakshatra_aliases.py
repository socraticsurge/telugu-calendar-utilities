"""Source spellings must match canonical engine Nakshatras at runtime."""
from datetime import date

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import (
    canonical_activity_nakshatra,
    canonical_activity_nakshatras,
)
from telugu_panchangam.personal.muhurta import day_slots


def _hyderabad():
    return next(city for city in CITIES if city.name == 'Hyderabad')


def test_source_spellings_normalize_to_engine_names():
    assert canonical_activity_nakshatra('Ashwini') == 'Ashvini'
    assert canonical_activity_nakshatra('Moola') == 'Mula'
    assert canonical_activity_nakshatra('Pushya') == 'Pushya'
    assert canonical_activity_nakshatras(
        ['Ashwini', 'Moola', 'Pushya']) == {'Ashvini', 'Mula', 'Pushya'}


@pytest.mark.parametrize(
    ('target', 'canonical_name'),
    [
        (date(2026, 6, 2), 'Mula'),
        (date(2026, 6, 12), 'Ashvini'),
    ],
)
def test_travel_source_preferences_fire_for_legacy_spellings(
        target, canonical_name):
    day = DrikGanitaEngine().calculate(target, _hyderabad())
    assert day.nakshatra.name == canonical_name
    slots = day_slots(day, activity='travel')
    assert slots
    assert any(
        f'{canonical_name} specifically favoured for Travel / journey (+1)'
        in reason
        for slot in slots
        for reason in slot['reasons']
    )
