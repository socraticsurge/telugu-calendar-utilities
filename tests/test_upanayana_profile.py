"""Contract tests for Raman's Upanayana election profile."""
from datetime import date
import json
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


def test_upanayana_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['upanayana']
    assert rules['forenoon_only'] is True
    assert rules['allowed_maasams'] == [
        'Magha', 'Phalguna', 'Chaitra', 'Vaishakha',
    ]
    assert rules['allowed_solar_signs'] == [
        'Makara', 'Kumbha', 'Meena', 'Mesha', 'Vrishabha', 'Mithuna',
    ]
    assert rules['allowed_tithi_names'] == [
        'Shukla Dwitiya', 'Shukla Tritiya', 'Shukla Panchami',
        'Shukla Saptami', 'Shukla Dashami', 'Shukla Trayodashi',
        'Krishna Pratipat', 'Krishna Dwitiya', 'Krishna Tritiya',
    ]
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]


def test_exact_tithi_gate_preserves_paksha_distinction():
    rules = ACTIVITY_RULES['upanayana']
    assert 'Shukla Saptami' in rules['allowed_tithi_names']
    assert 'Krishna Saptami' not in rules['allowed_tithi_names']


def test_positive_candidates_are_before_noon_and_never_at_night():
    day = _day(date(2026, 4, 20))
    next_day = _day(date(2026, 4, 21))
    slots = day_slots(day, activity='upanayana')
    assert slots
    solar_noon = day.sunrise + (day.sunset - day.sunrise) / 2
    assert all(slot['end'] <= solar_noon for slot in slots)
    assert night_slots(day, next_day, activity='upanayana', engine=ENGINE) == []


def test_disallowed_solar_rasi_is_explained():
    day = _day(date(2026, 4, 20))
    day.solar_sign = 'Karka'  # isolate the solar-Rasi gate from lunar month
    reason = diagnose_day(day, activity='upanayana')
    assert reason and 'does not admit this solar Rasi' in reason


def test_mcp_and_browser_publish_exact_tithi_and_solar_contract():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-04-20', days=1, activity='upanayana', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.upanayana'

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['upanayana']
    assert exported['allowed_tithi_names'] == \
        profile['automated_constraints']['allowed_tithi_names']
    assert exported['allowed_solar_signs'] == \
        profile['automated_constraints']['allowed_solar_signs']
