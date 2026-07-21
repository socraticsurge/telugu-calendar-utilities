"""Contract tests for Raman's felling-trees lunar-quarter rule."""
from datetime import date
import json

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


LAST_QUARTER_TITHIS = [
    'Krishna Ashtami', 'Krishna Navami', 'Krishna Dashami',
    'Krishna Ekadashi', 'Krishna Dwadashi', 'Krishna Trayodashi',
    'Krishna Chaturdashi', 'Amavasya',
]
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def test_wood_cutting_profile_matches_raman_chapter_xiii():
    rules = ACTIVITY_RULES['wood_cutting']
    assert rules['source_claim'] == 'muhurta.wood_cutting'
    assert rules['allowed_tithi_names'] == LAST_QUARTER_TITHIS
    assert rules['skip_on_panchaka_nakshatra'] is True
    assert rules['manual_checks']


def test_mcp_publishes_wood_cutting_claim_and_last_quarter_gate():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='wood_cutting', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.wood_cutting'
    assert profile['automated_constraints']['allowed_tithi_names'] == \
        LAST_QUARTER_TITHIS
    assert profile['manual_checks'] == \
        ACTIVITY_RULES['wood_cutting']['manual_checks']


def test_wood_cutting_slots_enforce_last_quarter_at_slot_time():
    first_half = ENGINE.calculate(date(2026, 1, 1), HYDERABAD)
    assert day_slots(first_half, activity='wood_cutting', engine=ENGINE) == []

    last_quarter = ENGINE.calculate(date(2026, 1, 11), HYDERABAD)
    slots = day_slots(last_quarter, activity='wood_cutting', engine=ENGINE)
    assert slots
    for slot in slots:
        facts = ENGINE.facts_at(
            slot['start'], last_quarter.location,
            vaaram=last_quarter.vaaram)
        assert facts.tithi in LAST_QUARTER_TITHIS
