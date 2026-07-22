"""Contract tests for Raman's vehicle-acquisition Nakshatra rule."""
from datetime import date, timedelta
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(value: date):
    return ENGINE.calculate(value, HYDERABAD)


def test_vehicle_profile_matches_raman_chapter_iv():
    assert ACTIVITY_RULES['vehicle']['prefer_nakshatras'] == [
        'Shravana', 'Dhanishtha', 'Shatabhisha', 'Punarvasu', 'Swati',
    ]


def test_preferred_vehicle_nakshatra_emits_disclosed_bonus():
    preferred = set(ACTIVITY_RULES['vehicle']['prefer_nakshatras'])
    matched = []
    start = date(2026, 1, 1)
    for offset in range(45):
        day = _day(start + timedelta(days=offset))
        for slot in day_slots(day, activity='vehicle', engine=ENGINE):
            nakshatra = ENGINE.facts_at(
                slot['start'], day.location, vaaram=day.vaaram).nakshatra
            if nakshatra in preferred:
                matched.append(slot)
                assert any(
                    f'{nakshatra} specifically favoured for Vehicle purchase (+1)' == reason
                    for reason in slot['reason_groups']['activity_match'])
    assert matched


def test_mcp_and_browser_publish_same_vehicle_nakshatras():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=14, activity='vehicle', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.vehicle.acquisition'

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert browser['rules']['vehicle']['prefer_nakshatras'] == \
        profile['automated_constraints']['prefer_nakshatras']
