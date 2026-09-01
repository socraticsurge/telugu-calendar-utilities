import json
import subprocess
import sys
from pathlib import Path

import pytest

from telugu_panchangam.personal.election_chart import (
    evaluate_election_chart,
    evaluate_election_snapshots,
    evaluate_election_window,
)
from telugu_panchangam.personal.election_chart_rules import ELECTION_CHART_RULES

PLANETS = (
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
    'Shukra', 'Shani', 'Rahu', 'Ketu',
)


def _chart(**houses):
    return {
        'instant': '2026-09-08T05:30:00.000Z',
        'lagna': {'rashi': 'Kanya', 'degree': 12.5},
        'planets': [
            {
                'name': name,
                'rashi': 'Mesha',
                'degree': index + 0.25,
                'house': houses.get(name, index + 1),
                'retrograde': name in {'Rahu', 'Ketu'},
            }
            for index, name in enumerate(PLANETS)
        ],
    }


def test_gold_remains_manual_without_inventing_an_aspect_model():
    assert ELECTION_CHART_RULES.get('gold', ()) == ()


def test_wedding_named_prohibition_rejects():
    result = evaluate_election_chart('wedding', _chart(Kuja=8))
    assert result['rejected'] is True
    assert any(
        outcome['rule_id'] == 'wedding.kuja-not-8'
        and outcome['status'] == 'fail'
        and 'printed pp. 41-42' in outcome['source_locator']
        for outcome in result['outcomes']
    )


def test_vacancy_includes_nodes_under_disclosed_whole_sign_convention():
    result = evaluate_election_chart('gruhapravesha', _chart(Rahu=8))
    assert result['rejected'] is True


def test_incomplete_chart_fails_closed_to_unknown():
    chart = _chart()
    chart['planets'].pop()
    result = evaluate_election_chart('wedding', chart)
    assert result['rejected'] is False
    assert result['needs_review'] is True
    assert all(outcome['status'] == 'unknown' for outcome in result['outcomes'])


@pytest.mark.parametrize('invalid_house', [True, False, 0, 13])
def test_invalid_house_values_fail_closed_to_unknown(invalid_house):
    chart = _chart()
    chart['planets'][0]['house'] = invalid_house
    result = evaluate_election_chart('wedding', chart)
    assert result['rejected'] is False
    assert result['needs_review'] is True
    assert all(outcome['status'] == 'unknown' for outcome in result['outcomes'])


def test_window_uses_both_boundaries():
    start = _chart(Kuja=7)
    end = _chart(Kuja=8)
    end['instant'] = '2026-09-08T06:18:00.000Z'
    result = evaluate_election_window('wedding', start, end)
    assert result['stable'] is False
    assert result['rejected'] is True


def test_interior_failure_cannot_hide_behind_matching_endpoints():
    result = evaluate_election_snapshots('wedding', [
        _chart(Kuja=7),
        _chart(Kuja=8),
        _chart(Kuja=7),
    ])
    assert result['stable'] is False
    assert result['rejected'] is True


def test_generated_browser_rule_contract_is_current():
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, 'tools/export_election_chart_rules.py', '--check'],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_every_rule_uses_a_registered_provenance_claim():
    root = Path(__file__).parents[1]
    provenance = json.loads((root / 'docs/reference/provenance.json').read_text())
    claim_ids = {claim['id'] for claim in provenance['claims']}

    for rules in ELECTION_CHART_RULES.values():
        for rule in rules:
            assert rule['source_claim'] in claim_ids


def test_provenance_distinguishes_the_drik_website_post_screen():
    root = Path(__file__).parents[1]
    provenance = json.loads((root / 'docs/reference/provenance.json').read_text())
    claims = {claim['id']: claim for claim in provenance['claims']}
    automated_claims = {
        rule['source_claim']
        for rules in ELECTION_CHART_RULES.values()
        for rule in rules
    }
    for claim_id in automated_claims:
        assert 'Drik website post-screen' in claims[claim_id]['scope'], claim_id
