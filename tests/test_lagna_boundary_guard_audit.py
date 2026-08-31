"""Regression contract for the election-chart Lagna boundary review band."""

import json
from datetime import date
from pathlib import Path

import pytest

from scripts.build_lagna_json import build_for_city
from telugu_panchangam.cities import CITIES
from telugu_panchangam.panchangam_names import RASHI_NAMES
from tools.audit_lagna_boundary_guard import (
    FIRST_NEW_MINUTE_LIMIT,
    GUARD_MINUTES,
    first_new_minute_offset,
    generate_report,
    published_transition_instant,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'lagna-boundary-guard-audit.json'


def test_exhaustive_audit_reproduces_the_committed_report():
    """Keep the full 22-city assurance sweep in the default repository gate."""

    expected = json.loads(FIXTURE.read_text(encoding='utf-8'))
    actual = generate_report()
    expected.pop('runtime_seconds')
    actual.pop('runtime_seconds')
    assert actual == expected


def test_committed_audit_report_covers_the_supported_product_envelope():
    report = json.loads(FIXTURE.read_text(encoding='utf-8'))
    scope = report['scope']
    guard = report['guard']
    results = report['results']

    assert report['schema_version'] == 1
    assert report['method']['dashaflow_reference_version'] == '1.1.0'
    assert scope['cities'] == [city.name for city in CITIES]
    assert scope['city_count'] == len(CITIES) == 22
    assert scope['date_start'] == '2025-01-15'
    assert scope['date_end'] == '2032-12-15'
    assert scope['date_pattern'] == '15th of every month, inclusive'
    assert scope['sampled_date_count'] == 96
    assert scope['city_date_count'] == 2_112
    assert scope['sign_transitions_per_city_date'] == 12
    assert guard == {
        'review_band_minutes_each_side': GUARD_MINUTES,
        'first_new_lagna_deadline_minutes': FIRST_NEW_MINUTE_LIMIT,
    }
    assert results['transition_count'] == 2_112 * 12 == 25_344
    assert sum(results['first_new_minute_offsets'].values()) == 25_344
    assert results['transitions_after_t_plus_2'] == 0
    assert results['max_abs_boundary_delta_minutes'] == pytest.approx(1.61088)
    assert results['guard_margin_minutes'] == pytest.approx(
        GUARD_MINUTES - results['max_abs_boundary_delta_minutes']
    )
    assert results['max_delta_case']['city'] == 'Tirupati'
    assert results['max_delta_case']['date'] == '2028-05-15'
    # Guard bands around adjacent boundaries cannot overlap in this audit.
    assert results['minimum_internal_dwell_minutes'] > 2 * GUARD_MINUTES


@pytest.mark.parametrize(
    ('city_name', 'sampled_date', 'local_time', 'new_lagna', 'first_new_offset'),
    [
        ('Hyderabad', date(2026, 1, 15), '10:19', 'Meena', 1),
        ('Sydney', date(2026, 5, 28), '14:35', 'Tula', 2),
    ],
)
def test_known_external_boundary_differences_remain_inside_the_guard_live(
    city_name,
    sampled_date,
    local_time,
    new_lagna,
    first_new_offset,
):
    city = next(city for city in CITIES if city.name == city_name)
    day = build_for_city(city, sampled_date, 1)['days'][0]

    matching = []
    for minute_offset, lagna_index in day['transitions'][:12]:
        instant = published_transition_instant(
            sampled_date,
            day['sunrise'],
            minute_offset,
            city.timezone,
        )
        if instant.strftime('%H:%M') == local_time:
            matching.append((instant, lagna_index))

    assert len(matching) == 1
    instant, lagna_index = matching[0]
    assert RASHI_NAMES[lagna_index] == new_lagna
    assert first_new_minute_offset(
        instant,
        lagna_index,
        city.lat,
        city.lon,
    ) == first_new_offset
    assert first_new_offset < GUARD_MINUTES
