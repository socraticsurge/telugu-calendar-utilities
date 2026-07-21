"""Contract tests for Raman's building-land purchase election profile."""
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


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_land_purchase_profile_matches_raman_chapter_xii():
    rules = ACTIVITY_RULES['property']
    assert rules['label'] == 'Land purchase (for building)'
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shanivaram',
    ]
    assert rules['allowed_nakshatras'] == [
        'Ashwini', 'Rohini', 'Mrigashira', 'Punarvasu', 'Pushya',
        'Uttara Phalguni', 'Hasta', 'Swati', 'Anuradha',
        'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha',
        'Uttara Bhadrapada',
    ]
    assert rules['avoid_tithi_numbers'] == [4, 9, 14]
    assert rules['prefer_lagna_class'] == 'Sthira'


def test_positive_fixture_exposes_manual_chart_requirements():
    slots = day_slots(_day(2026, 1, 1), activity='property')
    assert slots  # Thursday, Shukla Trayodashi, Rohini
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['property']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_rikta_tithi_is_hard_rejected_and_wrong_weekday_is_explained():
    # Monday + Swati otherwise fit, but Krishna Navami is Rikta.
    assert day_slots(_day(2026, 1, 12), activity='property') == []
    reason = diagnose_day(_day(2026, 1, 2), activity='property')
    assert reason == (
        'Shukravaram · Land purchase (for building) source profile '
        'does not admit this weekday'
    )


def test_mcp_and_browser_publish_same_land_purchase_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='property', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.land_purchase.building'

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['property']
    assert exported['avoid_tithi_numbers'] == \
        profile['automated_constraints']['avoid_tithi_numbers']
    assert exported['manual_checks'] == profile['manual_checks']
