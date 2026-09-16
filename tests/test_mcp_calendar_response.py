"""Boundary cases for shared MCP projections and unchanged request validation."""

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from telugu_panchangam.mcp import calendar_response as response
from telugu_panchangam.mcp import tools


@pytest.mark.parametrize('name', ['maudhya_to_dict', 'panchaka_to_dict'])
def test_missing_scalar_results_stay_null(name):
    assert getattr(response, name)(None) is None


@pytest.mark.parametrize(
    'name', ['window_to_dict', 'ghati_window_to_dict', 'eclipse_to_dict', 'ghati_clock']
)
def test_missing_timed_results_stay_null(name):
    assert getattr(response, name)(None, 'Asia/Kolkata') is None


def event_day(**overrides):
    values = dict(
        festivals=[],
        nakshatra=SimpleNamespace(name='Rohini'),
        is_ekadashi=False,
        is_amavasya=False,
        is_pournami=False,
        is_shani_pradosham=False,
        is_soma_pradosham=False,
        is_pradosham=False,
        sankramanam=None,
        eclipse=None,
    )
    return SimpleNamespace(**{**values, **overrides})


@pytest.mark.parametrize(
    ('flags', 'expected'),
    [
        ({}, []),
        ({'is_pradosham': True}, ['Pradosham']),
        ({'is_soma_pradosham': True, 'is_pradosham': True}, ['Soma Pradosham']),
        (
            {
                'is_shani_pradosham': True,
                'is_soma_pradosham': True,
                'is_pradosham': True,
            },
            ['Shani Pradosham'],
        ),
        ({'sankramanam': 'Makara'}, ['Makara Sankramanam']),
        (
            {'sankramanam': 'Makara', 'festivals': ['Makara Sankranti']},
            ['Makara Sankranti'],
        ),
        ({'sankramanam': 'Mithuna'}, ['Mithuna Sankramanam']),
    ],
)
def test_special_event_precedence_and_no_duplicate_makara(flags, expected):
    day = event_day(**flags)
    before = list(day.festivals)
    assert response.special_events(day) == expected
    assert day.festivals == before


def test_special_event_order():
    day = event_day(
        festivals=['Festival'],
        nakshatra=SimpleNamespace(name='Ashvini'),
        is_ekadashi=True,
        is_amavasya=True,
        is_pournami=True,
        is_pradosham=True,
        sankramanam='Mithuna',
        eclipse=SimpleNamespace(kind='Lunar', subtype='Total'),
    )
    assert response.special_events(day) == [
        'Festival',
        'Ganda Moola (Ashvini)',
        'Ekadashi — fasting day',
        'Amavasya',
        'Pournami',
        'Pradosham',
        'Mithuna Sankramanam',
        'Lunar Eclipse (Total)',
    ]


def test_window_timezone_and_rounding():
    moment = datetime(2026, 6, 10, tzinfo=timezone.utc)
    window = SimpleNamespace(
        name='Window',
        start=moment,
        end=moment,
        start_ghati=1.123456,
        end_ghati=2.123456,
    )
    assert response.ghati_window_to_dict(window, 'Asia/Kolkata') == {
        'name': 'Window',
        'start': '05:30',
        'end': '05:30',
        'start_ghati': 1.1235,
        'end_ghati': 2.1235,
    }


@pytest.mark.parametrize(
    ('start', 'end', 'limit'),
    [
        ('2026-01-01', '2026-01-01', 30),
        ('2026-01-01', '2026-01-31', 30),
        ('2026-01-01', '2027-01-01', 365),
        ('2026-01-01', '2028-01-01', 730),
    ],
)
def test_inclusive_date_limits_stay_compatible(start, end, limit):
    assert tools._date_interval(start, end, limit, 'too long') == (
        date.fromisoformat(start),
        date.fromisoformat(end),
    )


def test_empty_rashi_is_skipped_only_by_tarabalam():
    tools._validate_tarabalam_rashis([''], ['Ashvini'])
    with pytest.raises(ValueError):
        tools._validate_aligned_rashis('janma_rasis', [''], ['Ashvini'])


@pytest.mark.parametrize(
    ('label', 'expected'),
    [
        ('janma_rasis', 'Invalid rashi name.'),
        ('janma_lagnas', 'Invalid lagna rashi name.'),
    ],
)
def test_invalid_aligned_name_messages(label, expected):
    with pytest.raises(ValueError) as error:
        tools._validate_aligned_rashis(label, [123], ['Ashvini'])
    assert str(error.value) == expected


def test_new_response_module_remains_visible_in_architecture_report():
    from tools.analyze_computation_architecture import source_scope_class

    assert (
        source_scope_class('telugu_panchangam/mcp/calendar_response.py')
        == 'additive-feature'
    )
