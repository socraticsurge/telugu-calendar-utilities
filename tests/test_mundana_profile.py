"""Contract tests for Raman's Mundana/Chaula election profile."""
import json
from datetime import date
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day, night_slots

HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(value: date):
    return ENGINE.calculate(value, HYDERABAD)


def test_mundana_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['mundana']
    assert rules['forenoon_only'] is True
    assert rules['allowed_pakshams'] == ['Shukla']
    assert rules['skip_on_combust'] == ['Guru', 'Shukra']
    assert rules['allowed_tithi_numbers'] == [2, 3, 5, 7, 10, 11, 13]
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['allowed_lagnas'] == [
        'Karka', 'Kanya', 'Mithuna', 'Meena', 'Tula', 'Vrishabha', 'Makara',
    ]


def test_mundana_candidates_end_by_solar_noon():
    day = _day(date(2026, 4, 20))
    slots = day_slots(day, activity='mundana')
    assert slots
    solar_noon = day.sunrise + (day.sunset - day.sunrise) / 2
    assert all(slot['end'] <= solar_noon for slot in slots)
    assert night_slots(day, _day(date(2026, 4, 21)),
                       activity='mundana', engine=ENGINE) == []


def test_krishna_paksha_is_rejected_with_source_reason():
    day = _day(date(2026, 4, 6))
    assert diagnose_day(day, activity='mundana') == (
        'Krishna Paksha · Mundana / Chaula (First head-shave) source profile '
        'does not admit this lunar fortnight')


def test_mcp_and_browser_publish_same_time_boundary():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-04-20', days=1, activity='mundana', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.mundana'
    assert profile['automated_constraints']['forenoon_only'] is True
    assert profile['automated_constraints']['allowed_pakshams'] == ['Shukla']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['mundana']
    assert exported['forenoon_only'] is True
    assert exported['allowed_pakshams'] == ['Shukla']
