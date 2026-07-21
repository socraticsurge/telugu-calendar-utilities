"""Contract tests for Raman's well-digging election profile."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_well_digging_profile_matches_raman_chapter_xii():
    rules = ACTIVITY_RULES['well_digging']
    assert rules['allowed_nakshatras'] == [
        'Revati', 'Uttara Bhadrapada', 'Hasta', 'Anuradha',
        'Magha', 'Shravana', 'Rohini', 'Pushya',
    ]
    assert rules['allowed_lagnas'] == ['Meena', 'Karkataka', 'Makara']
    assert rules['caution_lagna_solar'] is True
    assert 'prefer_nakshatra_mukha' not in rules


def test_only_source_admitted_nakshatra_and_lagna_survive():
    slots = day_slots(_day(2026, 1, 1), activity='well_digging')
    assert slots  # Rohini fixture
    assert all(any(
        f'{lagna} lagna is admitted for Well digging' in reason
        for lagna in ('Meena', 'Karkataka', 'Makara')
        for reason in slot['reason_groups']['activity_match']
    ) for slot in slots)
    # The following day is Mrigashira, outside Raman's eight-name list.
    assert day_slots(_day(2026, 1, 2), activity='well_digging') == []


def test_surya_in_lagna_is_a_caution_not_an_invented_rejection():
    slots = day_slots(_day(2026, 2, 3), activity='well_digging')
    assert slots
    assert any('Source caution · Makara Lagna is occupied by Surya' in note
               for slot in slots for note in slot['reason_groups']['notes'])
    assert all(ACTIVITY_RULES['well_digging']['manual_checks'])


def test_mcp_browser_and_catalogue_share_well_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta
    from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES

    assert 'well_digging' in BROWSER_ACTIVITIES
    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='well_digging', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.well_digging'

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['well_digging']
    assert exported['allowed_lagnas'] == \
        profile['automated_constraints']['allowed_lagnas']
    assert exported['manual_checks'] == profile['manual_checks']
