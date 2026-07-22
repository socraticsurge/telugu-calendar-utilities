"""Contract tests for Raman's Karnavedha election profile."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, night_slots


HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(value: date):
    return ENGINE.calculate(value, HYDERABAD)


def test_karnavedha_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['karnavedha']
    assert rules['daytime_only'] is True
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['avoid_tithi_numbers'] == [4, 6, 8, 12, 14, 15]
    assert rules['allowed_lagnas'] == [
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Kanya', 'Tula',
        'Dhanu', 'Makara', 'Meena',
    ]


def test_karnavedha_never_returns_night_candidates():
    day = _day(date(2026, 2, 6))
    next_day = _day(date(2026, 2, 7))
    assert night_slots(day, next_day, activity='karnavedha', engine=ENGINE) == []


def test_positive_fixture_discloses_practitioner_checks():
    # Friday, Krishna Panchami; permitted Lagna windows survive.
    slots = day_slots(_day(date(2026, 2, 6)), activity='karnavedha')
    assert slots
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['karnavedha']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_mcp_and_browser_publish_daytime_only_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-02-06', days=1, activity='karnavedha', city='Hyderabad',
        include_night=True))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.karnavedha'
    assert profile['automated_constraints']['daytime_only'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert browser['rules']['karnavedha']['daytime_only'] is True
