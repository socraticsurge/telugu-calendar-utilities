"""Contract tests for Raman's Vidyarambha/Aksharabhyasa profile."""
from datetime import date
import json
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


def test_vidyarambha_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['vidyarambha']
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['allowed_nakshatras'] == [
        'Ashwini', 'Punarvasu', 'Ardra', 'Hasta',
        'Chitra', 'Swati', 'Shravana', 'Revati',
    ]
    assert rules['allowed_lagnas'] == [
        'Mesha', 'Karka', 'Tula', 'Makara',
        'Mithuna', 'Kanya', 'Dhanu', 'Meena',
    ]


def test_unlisted_weekday_is_rejected_with_source_reason():
    assert diagnose_day(_day(date(2026, 2, 22)), activity='vidyarambha') == (
        'Adivaram · Education start (Vidyarambha) source profile '
        'does not admit this weekday')


def test_positive_fixture_discloses_practitioner_checks():
    slots = day_slots(_day(date(2026, 2, 6)), activity='vidyarambha')
    assert slots
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['vidyarambha']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_mcp_and_browser_publish_same_vidyarambha_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-02-06', days=1, activity='vidyarambha', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.vidyarambha'

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['vidyarambha']
    assert exported['allowed_nakshatras'] == \
        profile['automated_constraints']['allowed_nakshatras']
    assert exported['allowed_lagnas'] == \
        profile['automated_constraints']['allowed_lagnas']
