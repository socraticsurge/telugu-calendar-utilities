"""Contract tests for Raman's house-foundation election profile."""
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


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_foundation_profile_matches_raman_chapter_xii():
    rules = ACTIVITY_RULES['bhumi_puja']
    assert rules['allowed_maasams'] == [
        'Chaitra', 'Vaishakha', 'Shravana', 'Kartika', 'Magha',
    ]
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['avoid_vara_paksha'] == [('Somavaram', 'Krishna')]
    assert rules['allowed_solar_classes'] == ['Sthira', 'Chara']
    assert rules['allowed_tithi_numbers'] == [1, 2, 3, 5, 6, 7, 10, 11, 13, 15]
    assert rules['required_lagna_class'] == 'Sthira'
    assert set(rules['prefer_nakshatras']) < set(rules['allowed_nakshatras'])


def test_positive_fixture_exposes_best_nakshatra_fixed_lagna_and_manual_checks():
    # 2026-04-20: Vaishakha, Monday, Mesha Surya, Shukla Tritiya,
    # Rohini. Only its fixed-Lagna candidate survives.
    slots = day_slots(_day(2026, 4, 20), activity='bhumi_puja')
    assert slots
    assert all(any('satisfies required Sthira class' in reason
                   for reason in slot['reason_groups']['activity_match'])
               for slot in slots)
    assert any('Rohini specifically favoured' in reason
               for slot in slots for reason in slot['reasons'])
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['bhumi_puja']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_source_profile_rejections_are_explained():
    # 2026-06-17 is Jyeshtha Maasa, explicitly outside the admitted list.
    reason = diagnose_day(_day(2026, 6, 17), activity='bhumi_puja')
    assert reason and 'does not admit this lunar month' in reason


def test_mcp_and_browser_publish_same_foundation_constraints():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-04-20', days=1, activity='bhumi_puja', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.bhumi_puja.foundation'
    assert profile['manual_checks'] == ACTIVITY_RULES['bhumi_puja']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['bhumi_puja']
    assert exported['allowed_tithi_numbers'] == \
        profile['automated_constraints']['allowed_tithi_numbers']
    assert exported['manual_checks'] == profile['manual_checks']
