"""MCP refactor compatibility: pinned bytes are not an accuracy oracle."""

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from telugu_panchangam.mcp import tools

DAY = {'date_str': '2026-06-10', 'city': 'Hyderabad'}
RANGE = {'start_date': '2026-06-10', 'end_date': '2026-06-12'}
CASES = [
    ('cities', 'tool_list_supported_cities', {}),
    ('day', 'tool_get_panchangam', DAY),
    ('surya', 'tool_get_panchangam', {**DAY, 'system': 'surya_siddhanta'}),
    ('vakya', 'tool_get_panchangam', {**DAY, 'system': 'vakya'}),
    ('raman', 'tool_get_panchangam', {**DAY, 'ayanamsa': 'raman'}),
    ('eclipse-day', 'tool_get_panchangam', {**DAY, 'date_str': '2025-09-07'}),
    ('sankranti', 'tool_get_panchangam', {**DAY, 'date_str': '2026-01-14'}),
    ('london-dst', 'tool_get_panchangam', {'date_str': '2026-03-29', 'city': 'London'}),
    ('windows', 'tool_get_muhurta', DAY),
    ('horas', 'tool_get_daily_horas', DAY),
    ('lagnas', 'tool_get_lagna_transitions', DAY),
    ('range', 'tool_get_panchangam_range', {**RANGE, 'city': 'Hyderabad'}),
    (
        'special-days',
        'tool_get_special_days',
        {'year': 2026, 'month': 6, 'city': 'Hyderabad'},
    ),
    (
        'december',
        'tool_get_special_days',
        {'year': 2026, 'month': 12, 'city': 'London'},
    ),
    (
        'tara',
        'tool_find_tarabalam_days',
        {
            'janma_nakshatras': ['Ashvini', 'Rohini'],
            'start_date': '2026-06-10',
            'days': 2,
            'janma_rasis': ['Mesha', None],
        },
    ),
    (
        'tara-empty-rashi',
        'tool_find_tarabalam_days',
        {
            'janma_nakshatras': ['Ashvini'],
            'start_date': '2026-06-10',
            'days': 1,
            'janma_rasis': [''],
        },
    ),
    ('grahas', 'tool_get_graha_positions', DAY),
    ('gochara', 'tool_get_gochara', {**DAY, 'janma_rasi': 'Mesha'}),
    (
        'phalalu',
        'tool_get_rasi_phalalu',
        {**DAY, 'janma_rasi': 'Mesha', 'janma_nakshatra': 'Ashvini'},
    ),
    ('combustion', 'tool_get_combustion_calendar', RANGE),
    ('wars', 'tool_get_graha_yuddha', RANGE),
    ('ingresses', 'tool_get_rashi_ingresses', RANGE),
    (
        'eclipses',
        'tool_get_eclipse_calendar',
        {'start_date': '2025-09-01', 'end_date': '2025-09-30'},
    ),
    ('shuddhi', 'tool_get_panchanga_shuddhi', DAY),
    (
        'custom-coordinates',
        'tool_get_panchangam',
        {**DAY, 'latitude': 17.385, 'longitude': 78.4867, 'timezone': 'Asia/Kolkata'},
    ),
    (
        'bad-date-first',
        'tool_get_panchangam',
        {**DAY, 'date_str': 'bad', 'system': 'bad'},
    ),
    (
        'bad-system-first',
        'tool_get_panchangam',
        {**DAY, 'system': 'bad', 'latitude': 91, 'longitude': 181},
    ),
    ('bad-latitude', 'tool_get_panchangam', {**DAY, 'latitude': 91, 'longitude': 181}),
    ('bad-longitude', 'tool_get_panchangam', {**DAY, 'latitude': 0, 'longitude': 181}),
    ('long-city', 'tool_get_panchangam', {**DAY, 'city': 'x' * 81}),
    ('partial-coordinates', 'tool_get_panchangam', {**DAY, 'latitude': 91}),
    (
        'range-order',
        'tool_get_panchangam_range',
        {'start_date': '2026-06-12', 'end_date': '2026-06-10', 'city': 'Hyderabad'},
    ),
    (
        'range-limit',
        'tool_get_panchangam_range',
        {'start_date': '2026-06-01', 'end_date': '2026-07-02', 'city': 'Hyderabad'},
    ),
    (
        'combustion-limit',
        'tool_get_combustion_calendar',
        {'start_date': '2026-01-01', 'end_date': '2027-01-02'},
    ),
    ('war-planets', 'tool_get_graha_yuddha', {**RANGE, 'planets': ['Sun', 'bad']}),
    ('ingress-planets', 'tool_get_rashi_ingresses', {**RANGE, 'planets': ['bad']}),
    (
        'combustion-planets',
        'tool_get_combustion_calendar',
        {**RANGE, 'planets': ['bad']},
    ),
    (
        'eclipse-limit',
        'tool_get_eclipse_calendar',
        {'start_date': '2026-01-01', 'end_date': '2028-01-02'},
    ),
    (
        'invalid-month-first',
        'tool_get_special_days',
        {'year': 2026, 'month': 13, 'city': 'Hyderabad', 'system': 'bad'},
    ),
    (
        'invalid-tara-mode-first',
        'tool_find_tarabalam_days',
        {'janma_nakshatras': [], 'start_date': 'bad', 'chandra_mode': 'bad'},
    ),
    (
        'invalid-tara-name',
        'tool_find_tarabalam_days',
        {'janma_nakshatras': [None], 'start_date': 'bad'},
    ),
    (
        'unaligned-tara',
        'tool_find_tarabalam_days',
        {'janma_nakshatras': ['Ashvini'], 'start_date': 'bad', 'janma_rasis': []},
    ),
]
FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'mcp-handler-compatibility.json'


@pytest.mark.parametrize(
    ('case_id', 'tool_name', 'parameters'), CASES, ids=[case[0] for case in CASES]
)
def test_handler_response_bytes_stay_compatible(case_id, tool_name, parameters):
    baseline = json.loads(FIXTURE_PATH.read_text())
    actual = getattr(tools, tool_name)(**parameters)
    assert hashlib.sha256(actual.encode()).hexdigest() == baseline['responses'][case_id]


def test_all_public_tool_signatures_stay_compatible():
    baseline = json.loads(FIXTURE_PATH.read_text())
    actual = {
        name: str(inspect.signature(getattr(tools, name)))
        for name in dir(tools)
        if name.startswith('tool_')
    }
    assert actual == baseline['signatures']


def test_unexpected_failure_is_logged_and_not_exposed(monkeypatch, caplog):
    def fail(*args, **kwargs):
        raise RuntimeError('private calculation detail')

    monkeypatch.setattr(tools._ENGINES['drik'], 'calculate', fail)
    response = tools.tool_get_panchangam(**DAY)
    assert json.loads(response) == {
        'error': 'Calculation failed. Please check your inputs and try again.'
    }
    assert 'private calculation detail' not in response
    assert 'tool call failed' in caplog.text


def test_location_altitude_contract_and_inferred_timezone(monkeypatch):
    monkeypatch.setattr(
        tools, 'timezone_for_coordinates', lambda lat, lon: 'Asia/Kolkata'
    )
    assert tools._resolve_city('Hyderabad', None, None, None).alt == 0
    assert tools._resolve_city_with_alt('Hyderabad', None, None, None).alt == 531
    custom = tools._resolve_city('', 17.385, 78.4867, None)
    assert (custom.name, custom.timezone, custom.alt) == ('Custom', 'Asia/Kolkata', 0)
