"""Contract tests for Raman's Namakarana election profile."""
import json
from datetime import date
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day

HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(value: date):
    return ENGINE.calculate(value, HYDERABAD)


def test_namakarana_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['naming']
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['allowed_nakshatras'] == [
        'Anuradha', 'Punarvasu', 'Magha', 'Uttara Phalguni',
        'Uttara Ashadha', 'Uttara Bhadrapada', 'Shatabhisha', 'Swati',
        'Dhanishtha', 'Shravana', 'Rohini', 'Ashwini', 'Mrigashira',
        'Revati', 'Hasta', 'Pushya',
    ]
    assert rules['avoid_tithi_numbers'] == [4, 6, 8, 9, 12, 14, 15]
    assert rules['prefer_lagna_class'] == 'Sthira'


def test_source_gates_reject_unlisted_weekday_and_tithi():
    # 2026-01-04 is Sunday; source weekday gate fires before slot scoring.
    assert diagnose_day(_day(date(2026, 1, 4)), activity='naming') == (
        'Adivaram · Naming (Namakaranam) source profile '
        'does not admit this weekday')
    # Thursday + Shatabhisha otherwise pass, but Shukla Chaturthi is rejected.
    chaturthi = _day(date(2026, 1, 22))
    assert diagnose_day(chaturthi, activity='naming') is None
    assert day_slots(chaturthi, activity='naming') == []


def test_positive_fixture_discloses_practitioner_checks():
    # Monday, Shukla Pratipat, Uttara Ashadha.
    slots = day_slots(_day(date(2026, 1, 19)), activity='naming')
    assert slots
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['naming']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_mcp_and_browser_publish_same_namakarana_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-19', days=1, activity='naming', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.namakarana'

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['naming']
    assert exported['allowed_nakshatras'] == \
        profile['automated_constraints']['allowed_nakshatras']
    assert exported['manual_checks'] == profile['manual_checks']
