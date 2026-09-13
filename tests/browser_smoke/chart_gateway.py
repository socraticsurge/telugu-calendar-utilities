"""Browser smoke chart gateway; no automatic test collection."""

from __future__ import annotations

import json

from tests.browser_smoke.calendar_fixtures import (
    _court_lagna_fixture,
    _fixture_lagna_for_instant,
    _karnavedha_bounded_feed_fixture,
    _karnavedha_feed_fixture,
    _muhurta_lagna_fixture,
)
from tests.browser_smoke.constants import MUHURTA_FEED_FIXTURE
from tests.browser_smoke.planet_fixtures import (
    _COURT_CHART_SCENARIOS,
    _gold_pass_planets,
    _muhurta_planets,
)


def _muhurta_chart_payload(request_payload, scenario, lagna_fixture=None):
    location = request_payload['location']
    instants = request_payload['instants']
    gold_templates = _gold_templates_for_instants(instants, scenario, lagna_fixture)
    return {
        'contract_version': '1.0',
        'engine': {
            'name': 'DashaFlow',
            'version': '1.1.0-test',
            'ayanamsha': 'Lahiri',
            'ephemeris': 'swiss',
            'node_convention': 'mean',
        },
        'house_system': 'whole_sign',
        'location': location,
        'data': {
            'charts': [
                {
                    'instant': instant,
                    'lagna': {
                        'rashi': _fixture_lagna_for_instant(
                            instant, lagna_fixture,
                        ),
                        'degree': 12.5,
                    },
                    'planets': _muhurta_planets(
                        scenario,
                        index,
                        _fixture_lagna_for_instant(instant, lagna_fixture),
                        gold_templates[index],
                    ),
                }
                for index, instant in enumerate(instants)
            ],
        },
    }

def _install_muhurta_routes(
    page, docs_server, scenario, lagna_fixture=None,
):
    """Intercept every mutable Muhurtam dependency for a built-site test."""
    if scenario in _COURT_CHART_SCENARIOS and lagna_fixture is None:
        lagna_fixture = _court_lagna_fixture()
    calls = []
    feed_text = (
        _karnavedha_bounded_feed_fixture()
        if scenario == 'karnavedha-bounded'
        else _karnavedha_feed_fixture(scenario)
        if scenario.startswith('karnavedha-')
        else MUHURTA_FEED_FIXTURE.read_text(encoding='utf-8')
    )
    if scenario.startswith('annaprasana-'):
        feed_text = feed_text.replace('Revati', 'Pushya')

    page.route(
        'https://gc.zgo.at/**',
        lambda route: route.fulfill(
            status=200, content_type='application/javascript', body='',
        ),
    )
    page.route(
        'https://panchangam.goatcounter.com/**',
        lambda route: route.fulfill(status=204, body=''),
    )
    page.route(
        '**/feeds/*.ics',
        lambda route: route.fulfill(
            status=200, content_type='text/calendar', body=feed_text,
        ),
    )
    page.route(
        '**/feeds/*-lagna.json',
        lambda route: route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps(lagna_fixture or _muhurta_lagna_fixture()),
        ),
    )

    def fulfill_chart_gateway(route):
        request = route.request
        if scenario in {
            'offline', 'annaprasana-offline', 'karnavedha-offline',
        }:
            route.abort('failed')
            return
        headers = {
            'Access-Control-Allow-Origin': docs_server,
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Cache-Control': 'private, no-store',
        }
        if request.method == 'OPTIONS':
            route.fulfill(status=204, headers=headers, body='')
            return
        payload = request.post_data_json
        calls.append(payload)
        body = (
            {'contract_version': '1.0', 'data': {'charts': []}}
            if scenario == 'malformed'
            else _muhurta_chart_payload(payload, scenario, lagna_fixture)
        )
        route.fulfill(
            status=200,
            headers=headers,
            content_type='application/json',
            body=json.dumps(body),
        )

    page.route(
        'http://127.0.0.1:3000/api/guest/muhurta/election-charts',
        fulfill_chart_gateway,
    )
    return calls


def _gold_window_groups(instants):
    # These are the seven candidate-window starts generated from the
    # pinned June 11 ICS. A gateway batch can contain several windows;
    # planetary positions must stay coherent inside each one, while each
    # synthetic window may use its own controlled Gold outcome fixture.
    slot_starts = {
        '2026-06-11T01:56:00.000Z',
        '2026-06-11T05:27:00.000Z',
        '2026-06-11T06:19:00.000Z',
        '2026-06-11T07:12:00.000Z',
        '2026-06-11T10:42:00.000Z',
        '2026-06-11T11:35:00.000Z',
        '2026-06-11T12:27:00.000Z',
    }
    groups = []
    current = []
    for index, instant in enumerate(instants):
        if current and instant in slot_starts:
            groups.append(current)
            current = []
        current.append(index)
    if current:
        groups.append(current)
    return groups


def _gold_templates_for_instants(instants, scenario, lagna_fixture):
    gold_templates = [None] * len(instants)
    if scenario not in {'gold-pass', 'gold-cap', 'gold-unknown'}:
        return gold_templates
    for group in _gold_window_groups(instants):
        template = _gold_pass_planets([
            _fixture_lagna_for_instant(instants[index], lagna_fixture)
            for index in group
        ])
        for index in group:
            gold_templates[index] = template
    return gold_templates
