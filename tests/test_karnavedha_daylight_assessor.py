"""Raman-policy Karnavedha daylight assessor and external oracle contract."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.models.panchangam_day import Span
from telugu_panchangam.personal.election_assessors.karnavedha import (
    KARNAVEDHA_DAYLIGHT_POLICY_ID,
    KARNAVEDHA_NAKSHATRA_RULE_ID,
    KARNAVEDHA_TITHI_RULE_ID,
    evaluate_karnavedha_daylight,
    karnavedha_daylight_drop_reason,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (ROOT / 'tests/fixtures/karnavedha_daylight_drikpanchang_oracle.json')
    .read_text(encoding='utf-8')
)
ENGINE = DrikGanitaEngine()


def _city(name: str):
    return next(city for city in CITIES if city.name == name)


def _outcome(result: dict, rule_id: str) -> dict:
    return next(
        outcome for outcome in result['outcomes']
        if outcome['rule_id'] == rule_id
    )


def _local(value, timezone: str):
    return value.astimezone(ZoneInfo(timezone))


def test_external_fixture_declares_two_cities_dst_and_precision_boundary():
    assert ORACLE['policy_id'] == KARNAVEDHA_DAYLIGHT_POLICY_ID
    assert ORACLE['interval'] == '[local sunrise, local sunset)'
    assert ORACLE['comparison']['inspection_method'].startswith(
        'Manual rendered Chrome inspection')
    assert ORACLE['comparison']['published_precision'] == 'minute'
    assert ORACLE['comparison']['tolerance_seconds'] == 120
    assert ORACLE['comparison']['maximum_observed_delta_seconds'] == 91
    assert len(ORACLE['cases']) == 8
    assert {case['city'] for case in ORACLE['cases']} == {
        'Hyderabad', 'New York',
    }
    assert {
        case['engine']['sunrise'][-6:]
        for case in ORACLE['cases'] if case['city'] == 'New York'
    } == {'-05:00', '-04:00'}
    assert all(
        case['url'].startswith(
            'https://www.drikpanchang.com/panchang/day-panchang.html?')
        for case in ORACLE['cases']
    )


@pytest.mark.parametrize(
    'case', ORACLE['cases'], ids=lambda case: case['id'])
def test_engine_daylight_transitions_match_external_oracle(case):
    day = ENGINE.calculate(date.fromisoformat(case['date']), _city(case['city']))
    timezone = case['timezone']
    observed = {
        'sunrise': _local(day.sunrise, timezone),
        'sunset': _local(day.sunset, timezone),
        'tithi_transition': _local(day.tithi.end, timezone),
        'nakshatra_transition': _local(day.nakshatra.end, timezone),
    }
    for field, actual in observed.items():
        expected_engine = datetime.fromisoformat(case['engine'][field])
        expected_external = datetime.fromisoformat(
            case['drikpanchang'][field])
        assert actual == expected_engine
        assert abs((actual - expected_external).total_seconds()) <= (
            ORACLE['comparison']['tolerance_seconds'])

    result = evaluate_karnavedha_daylight(day)
    assert _outcome(result, KARNAVEDHA_TITHI_RULE_ID)['status'] == (
        case['expected']['tithi'])
    assert _outcome(result, KARNAVEDHA_NAKSHATRA_RULE_ID)['status'] == (
        case['expected']['nakshatra'])
    assert result['admissible'] is (
        set(case['expected'].values()) == {'pass'})


def test_half_open_daylight_interval_includes_sunrise_and_excludes_sunset():
    day = ENGINE.calculate(date(2026, 2, 6), _city('Hyderabad'))
    at_endpoints = replace(
        day,
        tithi=Span('Endpoint Tithi', day.sunrise, day.sunset),
        nakshatra=Span('Endpoint Nakshatra', day.sunrise, day.sunset),
    )
    result = evaluate_karnavedha_daylight(at_endpoints)
    assert [item['status'] for item in result['outcomes']] == ['pass', 'pass']
    assert result['admissible'] is True

    interior = replace(
        at_endpoints,
        tithi=replace(
            at_endpoints.tithi,
            end=day.sunset - timedelta(microseconds=1),
        ),
    )
    result = evaluate_karnavedha_daylight(interior)
    assert _outcome(result, KARNAVEDHA_TITHI_RULE_ID)['status'] == 'fail'
    assert result['rejected'] is True
    assert result['admissible'] is False


@pytest.mark.parametrize(
    ('mutation', 'evidence_fragment'),
    (
        ('missing-span', 'unavailable'),
        ('naive-boundary', 'timezone-aware'),
        ('span-not-active', 'does not contain local sunrise'),
        ('invalid-daylight', 'daylight boundaries'),
    ),
)
def test_malformed_or_uncertain_boundaries_fail_closed(mutation, evidence_fragment):
    day = ENGINE.calculate(date(2026, 2, 6), _city('Hyderabad'))
    if mutation == 'missing-span':
        day = replace(day, tithi=None)
    elif mutation == 'naive-boundary':
        day = replace(
            day,
            tithi=replace(day.tithi, end=day.tithi.end.replace(tzinfo=None)),
        )
    elif mutation == 'span-not-active':
        day = replace(
            day,
            tithi=replace(day.tithi, start=day.sunrise + timedelta(minutes=1)),
        )
    else:
        day = replace(day, sunset=day.sunrise)

    result = evaluate_karnavedha_daylight(day)
    tithi = _outcome(result, KARNAVEDHA_TITHI_RULE_ID)
    assert tithi['status'] == 'unknown'
    assert evidence_fragment in ' '.join(tithi['evidence'])
    assert result['needs_review'] is True
    assert result['admissible'] is False
    assert 'could not be verified' in karnavedha_daylight_drop_reason(result)


def test_drop_reason_names_each_failed_day_limb_once():
    day = ENGINE.calculate(date(2026, 1, 3), _city('Hyderabad'))
    result = evaluate_karnavedha_daylight(day)
    reason = karnavedha_daylight_drop_reason(result)

    assert reason.count('Tithi') == 1
    assert reason.count('Nakshatra') == 1
    assert '15:32:54' in reason
    assert '17:28:02' in reason
