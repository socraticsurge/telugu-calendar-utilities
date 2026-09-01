import json
from pathlib import Path

from telugu_panchangam.personal.personal_election import (
    evaluate_personal_election_window,
)

FIXTURES = json.loads(
    (Path(__file__).parent / 'fixtures/personal-election-parity.json').read_text()
)


def test_personal_election_fixtures_match_python_contract():
    for case in FIXTURES:
        result = evaluate_personal_election_window(
            case['activity'], case['participant'], case['start'], case['end'])
        actual = {
            'rejected': result['rejected'],
            'needs_review': result['needs_review'],
            'preference_passes': result['preference_passes'],
            'stable': result['stable'],
            'statuses': [item['status'] for item in result['outcomes']],
        }
        assert actual == case['expected'], case['label']


def test_personal_rule_outcomes_are_source_attributed_and_input_reviewable():
    for case in FIXTURES:
        result = evaluate_personal_election_window(
            case['activity'], case['participant'], case['start'], case['end'])
        for outcome in result['outcomes']:
            assert outcome['rule_id'].startswith(f"personal.{case['activity']}.")
            assert outcome['source_claim'].startswith('muhurta.')
            assert 'printed pp.' in outcome['source_locator']
            assert set(outcome['inputs']) == {'start', 'end'}
