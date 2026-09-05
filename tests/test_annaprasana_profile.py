"""Contract tests for Raman's Annaprasana election profile."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.lagna_hora import get_lagna_transitions
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day
from telugu_panchangam.personal.slot_scorers import slot_lagna_name


HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(value: date):
    return ENGINE.calculate(value, HYDERABAD)


def test_annaprasana_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['annaprasana']
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['allowed_nakshatras'] == [
        'Ashwini', 'Mrigashira', 'Punarvasu', 'Dhanishtha', 'Pushya',
        'Hasta', 'Swati', 'Anuradha', 'Shravana', 'Shatabhisha',
        'Uttara Phalguni', 'Chitra',
    ]
    assert rules['avoid_tithi_numbers'] == [4, 6, 8, 12, 14, 15]
    assert rules['allowed_lagnas'] == [
        'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Kanya', 'Tula',
        'Dhanu', 'Makara', 'Kumbha',
    ]


def test_positive_fixture_discloses_practitioner_checks():
    # Friday, Krishna Panchami, Hasta.
    slots = day_slots(_day(date(2026, 2, 6)), activity='annaprasana')
    assert slots
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['annaprasana']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_source_weekday_gate_and_lagna_gate_are_hard():
    assert diagnose_day(_day(date(2026, 2, 22)), activity='annaprasana') == (
        'Adivaram · Annaprasana (First feeding) source profile '
        'does not admit this weekday')
    allowed = set(ACTIVITY_RULES['annaprasana']['allowed_lagnas'])
    day = _day(date(2026, 2, 6))
    transitions = get_lagna_transitions(day)
    assert all(slot_lagna_name(transitions, slot['start']) in allowed
               for slot in day_slots(day, activity='annaprasana'))


def test_mcp_and_browser_publish_same_annaprasana_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-02-06', days=1, activity='annaprasana', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.annaprasana'
    assert profile['source_scope'] == {
        'panchangam_profile': 'python_and_mcp',
        'exact_election_chart_assessor': 'drik_browser_only',
        'event_chart_policy': (
            'election_chart.annaprasana.'
            'raman_transcription_policy_v1'),
        'general_election_chart_baseline': 'open_issue_284',
    }

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['annaprasana']
    assert exported['allowed_lagnas'] == \
        profile['automated_constraints']['allowed_lagnas']
    assert exported['manual_checks'] == profile['manual_checks']
