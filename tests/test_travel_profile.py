"""Contract and runtime tests for Raman's journey rules."""
from datetime import date, timedelta
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


ROOT = Path(__file__).resolve().parents[1]
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def test_travel_profile_matches_raman_chapter_xiv():
    rules = ACTIVITY_RULES['travel']
    assert rules['source_claim'] == 'muhurta.travel'
    assert rules['avoid_nakshatras'] == ['Bharani', 'Krittika']
    assert rules['prefer_nakshatras'] == [
        'Mrigashira', 'Ashwini', 'Pushya', 'Punarvasu', 'Hasta',
        'Anuradha', 'Shravana', 'Moola', 'Dhanishtha', 'Revati',
    ]


def test_travel_slots_never_admit_hard_rejected_nakshatras():
    rejected = set(ACTIVITY_RULES['travel']['avoid_nakshatras'])
    start = date(2026, 1, 1)
    saw_slots = False
    for offset in range(45):
        day = ENGINE.calculate(start + timedelta(days=offset), HYDERABAD)
        for slot in day_slots(day, activity='travel', engine=ENGINE):
            saw_slots = True
            facts = ENGINE.facts_at(
                slot['start'], day.location, vaaram=day.vaaram)
            assert facts.nakshatra not in rejected
    assert saw_slots


def test_mcp_and_browser_publish_same_travel_source_rules():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='travel', city='Hyderabad'))
    profile = result['activity_profile']
    rules = ACTIVITY_RULES['travel']
    assert profile['source_claim'] == 'muhurta.travel'
    assert profile['automated_constraints']['avoid_nakshatras'] == \
        rules['avoid_nakshatras']
    assert profile['automated_constraints']['prefer_nakshatras'] == \
        rules['prefer_nakshatras']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(
            encoding='utf-8'))
    exported = browser['rules']['travel']
    assert exported['source_claim'] == profile['source_claim']
    assert exported['avoid_nakshatras'] == rules['avoid_nakshatras']
