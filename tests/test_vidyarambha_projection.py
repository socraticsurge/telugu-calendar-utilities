"""Replay the bounded multi-date, multi-city Vidyarambha projection corpus."""

import json
from pathlib import Path

import pytest

from telugu_panchangam.personal.election_chart import (
    evaluate_election_snapshots,
)

FIXTURE = json.loads(
    (
        Path(__file__).parent
        / 'fixtures/election_chart_vidyarambha_projection.json'
    ).read_text(encoding='utf-8')
)


def test_projection_corpus_labels_external_and_local_evidence_honestly():
    capture = FIXTURE['capture']
    assert capture['kind'] == 'deterministic_dasha_flow_http_contract_replay'
    assert capture['engine'] == {
        'name': 'DashaFlow',
        'version': '1.1.0',
        'ayanamsha': 'Lahiri',
        'ephemeris': 'moshier',
        'node_convention': 'mean',
        'house_system': 'whole_sign',
    }
    assert capture['sidecar_contract']['endpoint'] == (
        '/v1/election-chart/derive')
    assert capture['local_gateway_contract']['endpoint'] == (
        '/api/guest/muhurta/election-charts')
    assert capture['local_gateway_contract']['request'] == {
        'location': {
            'latitude': 17.385,
            'longitude': 78.4867,
            'timezone': 'Asia/Kolkata',
        },
        'instants': [
            '2026-05-30T11:00:00.000Z',
            '2030-11-17T09:30:00.000Z',
        ],
    }
    assert 'not externally published-page matches' in (
        capture['local_gateway_contract']['scope'])

    cases = {case['id']: case for case in FIXTURE['cases']}
    external = set(capture['external_anchor']['cases'])
    assert external == {
        'washington-dc-2026-07-14', 'hyderabad-2026-08-27'}
    assert all('source_url' in cases[case_id] for case_id in external)
    local_ids = set(cases) - external
    assert local_ids == {
        'hyderabad-2026-05-30-local-conflict',
        'hyderabad-2030-11-17-local-all-pass',
    }
    assert all('source_url' not in cases[case_id] for case_id in local_ids)
    assert all(cases[case_id]['verification_scope'] == (
        'local_gateway_projection_not_external_match')
        for case_id in local_ids)

    timezones = {
        case['request']['location']['timezone'] for case in FIXTURE['cases']}
    dates = {
        instant[:10]
        for case in FIXTURE['cases']
        for instant in case['request']['instants']
    }
    assert timezones == {'America/New_York', 'Asia/Kolkata'}
    assert dates == {
        '2026-05-30', '2026-07-14', '2026-08-27', '2030-11-17'}


@pytest.mark.parametrize('case', FIXTURE['cases'], ids=lambda item: item['id'])
def test_vidyarambha_replays_projection_cases(case):
    assert [chart['instant'] for chart in case['charts']] == (
        case['request']['instants'])

    result = evaluate_election_snapshots('vidyarambha', case['charts'])

    assert [item['status'] for item in result['outcomes']] == (
        case['expected_statuses'])
    assert result['rejected'] is case['rejected']
    assert result['needs_review'] is case['needs_review']
    assert result['preference_passes'] == case['preference_passes']
    assert result['stable'] is case['stable']
