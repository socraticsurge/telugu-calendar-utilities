"""Contract tests for Raman's Karnavedha election profile."""
import json
from datetime import date
from pathlib import Path

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal import muhurta as finder
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.election_assessors.karnavedha import (
    KARNAVEDHA_DAYLIGHT_POLICY_ID,
)

HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
ROOT = Path(__file__).resolve().parents[1]


def _day(value: date):
    return ENGINE.calculate(value, HYDERABAD)


def test_karnavedha_profile_matches_raman_chapter_viii():
    rules = ACTIVITY_RULES['karnavedha']
    assert rules['daytime_only'] is True
    assert rules['require_single_daylight_tithi'] == (
        KARNAVEDHA_DAYLIGHT_POLICY_ID)
    assert rules['require_single_daylight_nakshatra'] == (
        KARNAVEDHA_DAYLIGHT_POLICY_ID)
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram',
    ]
    assert rules['avoid_tithi_numbers'] == [4, 6, 8, 12, 14, 15]
    assert rules['allowed_lagnas'] == [
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Kanya', 'Tula',
        'Dhanu', 'Makara', 'Meena',
    ]
    assert rules['related_claims'] == [
        'muhurta.karnavedha.vidyamadhava_divergence',
        'muhurta.karnavedha.chintamani_divergence',
    ]
    assert 'not blended' in rules['source_scope']
    assert rules['manual_prerequisites'] is True
    assert rules['manual_checks'] == [
        (
            'Perform on the 12th or 16th day after birth, or in the child’s '
            '6th, 7th or 8th month.'
        ),
        'Election chart: leave the 8th house unoccupied.',
    ]


def test_karnavedha_never_returns_night_candidates():
    day = _day(date(2026, 2, 6))
    next_day = _day(date(2026, 2, 7))
    assert finder.night_slots(
        day, next_day, activity='karnavedha', engine=ENGINE,
    ) == []


def test_positive_fixture_discloses_age_and_computed_daylight_checks():
    # Friday, Krishna Panchami; permitted Lagna windows survive.
    slots = finder.day_slots(_day(date(2026, 2, 6)), activity='karnavedha')
    assert slots
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['karnavedha']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)
    assert all(
        [item['status'] for item in slot['reason_groups'][
            'day_source_outcomes']] == ['pass', 'pass']
        for slot in slots
    )
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)


def test_python_slot_finder_evaluates_daylight_once_per_day(monkeypatch):
    original = finder.evaluate_karnavedha_daylight
    calls = []

    def counted(day):
        calls.append(day.date)
        return original(day)

    monkeypatch.setattr(finder, 'evaluate_karnavedha_daylight', counted)
    slots = finder.day_slots(
        _day(date(2026, 2, 6)), activity='karnavedha')

    assert slots
    assert calls == [date(2026, 2, 6)]


@pytest.mark.parametrize(
    'configured',
    (
        (None, KARNAVEDHA_DAYLIGHT_POLICY_ID),
        (KARNAVEDHA_DAYLIGHT_POLICY_ID, None),
        (None, None),
        ('unsupported-v2', KARNAVEDHA_DAYLIGHT_POLICY_ID),
        (KARNAVEDHA_DAYLIGHT_POLICY_ID, 'unsupported-v2'),
    ),
)
def test_python_slot_finder_fails_closed_on_daylight_policy_drift(
    monkeypatch, configured,
):
    malformed = dict(ACTIVITY_RULES['karnavedha'])
    malformed['require_single_daylight_tithi'] = configured[0]
    malformed['require_single_daylight_nakshatra'] = configured[1]
    monkeypatch.setitem(finder.ACTIVITY_RULES, 'karnavedha', malformed)

    day = _day(date(2026, 2, 6))
    assert finder.day_slots(day, activity='karnavedha') == []
    assert finder.diagnose_day(day, activity='karnavedha') == (
        'Karnavedha daylight rule · Tithi boundary could not be verified; '
        'Nakshatra boundary could not be verified'
    )


def test_mcp_and_browser_publish_daytime_only_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-02-06', days=1, activity='karnavedha', city='Hyderabad',
        include_night=True))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.karnavedha'
    assert profile['automated_constraints']['daytime_only'] is True
    assert profile['automated_constraints'][
        'require_single_daylight_tithi'] == KARNAVEDHA_DAYLIGHT_POLICY_ID
    assert profile['automated_constraints'][
        'require_single_daylight_nakshatra'] == KARNAVEDHA_DAYLIGHT_POLICY_ID
    assert profile['source_scope'] == ACTIVITY_RULES['karnavedha'][
        'source_scope']
    assert profile['manual_prerequisites'] is True
    assert profile['manual_checks'] == ACTIVITY_RULES['karnavedha'][
        'manual_checks']
    assert result['slots']
    assert all(
        [outcome['status'] for outcome in slot['reason_groups'][
            'day_source_outcomes']] == ['pass', 'pass']
        for slot in result['slots']
    )
    assert all(slot['tier'] != 'Excellent' for slot in result['slots'])
    assert all(
        slot['day_dosha'] == 'practitioner_review'
        for slot in result['slots']
    )

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert browser['rules']['karnavedha']['daytime_only'] is True
    assert browser['rules']['karnavedha']['source_scope'] == (
        ACTIVITY_RULES['karnavedha']['source_scope'])


def test_mcp_drops_double_limb_day_with_exact_transition_diagnosis():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-03', days=1, activity='karnavedha', city='Hyderabad'))

    assert result['slots'] == []
    dropped = result['dropped_days']
    assert len(dropped) == 1
    assert dropped[0]['date'] == '2026-01-03'
    assert dropped[0]['reason'] == (
        'Karnavedha daylight rule · Tithi changes at '
        '2026-01-03T15:32:54+05:30 inside local daylight; '
        'Nakshatra changes at 2026-01-03T17:28:02+05:30 inside '
        'local daylight'
    )
    assert [
        (outcome['rule_id'], outcome['status'], outcome['policy_id'])
        for outcome in dropped[0]['daylight_outcomes']
    ] == [
        (
            'karnavedha.daylight-tithi-single', 'fail',
            KARNAVEDHA_DAYLIGHT_POLICY_ID,
        ),
        (
            'karnavedha.daylight-nakshatra-single', 'fail',
            KARNAVEDHA_DAYLIGHT_POLICY_ID,
        ),
    ]
    assert all(
        outcome['evidence']
        for outcome in dropped[0]['daylight_outcomes']
    )


@pytest.mark.parametrize(
    'policy_field',
    (
        'require_single_daylight_tithi',
        'require_single_daylight_nakshatra',
    ),
)
def test_mcp_fails_closed_on_unsupported_daylight_policy_id(
    monkeypatch, policy_field,
):
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    malformed = dict(ACTIVITY_RULES['karnavedha'])
    malformed[policy_field] = 'unsupported-v2'
    monkeypatch.setitem(finder.ACTIVITY_RULES, 'karnavedha', malformed)

    result = json.loads(tool_find_muhurta(
        '2026-02-06', days=1, activity='karnavedha', city='Hyderabad'))

    assert result['slots'] == []
    dropped = result['dropped_days']
    assert len(dropped) == 1
    assert dropped[0]['date'] == '2026-02-06'
    assert dropped[0]['reason'] == (
        'Karnavedha daylight rule · Tithi boundary could not be verified; '
        'Nakshatra boundary could not be verified'
    )
    assert {
        (outcome['rule_id'], outcome['status'], outcome['policy_id'])
        for outcome in dropped[0]['daylight_outcomes']
    } == {
        (
            'karnavedha.daylight-tithi-single', 'unknown',
            KARNAVEDHA_DAYLIGHT_POLICY_ID,
        ),
        (
            'karnavedha.daylight-nakshatra-single', 'unknown',
            KARNAVEDHA_DAYLIGHT_POLICY_ID,
        ),
    }
