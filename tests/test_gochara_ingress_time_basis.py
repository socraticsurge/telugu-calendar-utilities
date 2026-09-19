"""Ingress date contracts preserve IST across location-aware consumers."""

import json
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from scripts.build_gochara_json import HYD_GEO, build
from telugu_panchangam.engines.utils import (
    datetime_to_jd,
    get_sunrise,
    jd_to_utc,
    local_midnight_jd,
)
from telugu_panchangam.gochara.positions import _next_ingress, graha_positions
from telugu_panchangam.mcp.tools import tool_get_graha_positions


@pytest.mark.parametrize('city,zone,day,graha', [
    ('New York', 'America/New_York', '2026-06-03', 'Chandra'),
    ('Sydney', 'Australia/Sydney', '2026-07-16', 'Surya'),
])
def test_non_ist_city_still_receives_explicit_ist_ingress_date(city, zone, day, graha):
    result = json.loads(tool_get_graha_positions(day, city))
    position = next(item for item in result['grahas'] if item['graha'] == graha)
    jd = datetime_to_jd(datetime.fromisoformat(day).replace(tzinfo=timezone.utc))
    graha_positions(jd)  # The public owner sets/restores Lahiri mode.
    event = _next_ingress(jd, graha)
    instant = jd_to_utc(event[0])
    ist_date = instant.astimezone(ZoneInfo('Asia/Kolkata')).date().isoformat()
    local_date = instant.astimezone(ZoneInfo(zone)).date().isoformat()
    assert ist_date != local_date
    assert position['rasi_until'] == ist_date


def test_generated_ingress_rows_preserve_exact_ist_dates_and_existing_rows():
    day = date(2026, 7, 16)
    data = build(day, 2)
    positions = graha_positions(get_sunrise(local_midnight_jd(day, 'Asia/Kolkata'), HYD_GEO))
    assert data['ingressTimeBasis'] == 'Asia/Kolkata'
    assert len(data['ingresses']) == len(data['days']) == len(data['retro']) == 2
    assert data['ingresses'][0] == [
        [p['rasi_until'], data['rasis'].index(p['next_rasi'])] for p in positions
    ]
    assert data['days'][0] == [data['rasis'].index(p['rasi']) for p in positions]
    assert data['retro'][0] == [int(p['retrograde']) for p in positions]
    # The Sun changes after Hyderabad sunrise: the exact date is July 16,
    # whereas the first changed sunrise snapshot is July 17.
    assert data['ingresses'][0][0][0] == '2026-07-16'
    assert data['days'][0][0] != data['days'][1][0]


def test_missing_ingress_remains_explicit_null(monkeypatch):
    from scripts import build_gochara_json

    positions = [
        {'rasi': 'Mesha', 'retrograde': False, 'rasi_until': None, 'next_rasi': None}
        for _ in range(9)
    ]
    monkeypatch.setattr(build_gochara_json, 'graha_positions', lambda _jd: positions)
    assert build(date(2026, 7, 16), 1)['ingresses'] == [[None] * 9]


def test_mcp_description_discloses_ist_date_contract():
    from telugu_panchangam.mcp.server import get_graha_positions

    assert 'IST/Asia-Kolkata calendar date regardless of city' in get_graha_positions.__doc__
    assert 'not an exact instant' in get_graha_positions.__doc__
