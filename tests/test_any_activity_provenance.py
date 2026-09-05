"""The source-neutral activity selector must disclose its heuristic status."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES

ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.any.shared_scoring'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_any_activity_is_explicitly_source_neutral():
    rules = ACTIVITY_RULES['any']
    assert rules == {
        'label': 'Anything auspicious',
        'heuristic_claim': CLAIM_ID,
    }
    claim = _claim()
    assert claim['evidence_class'] == 'project_heuristic'
    assert claim['verification_state'] == 'heuristic'
    assert claim['source_ids'] == []
    assert 'adds no activity-specific rule' in claim['scope']
    assert 'not a classical election for an unspecified act' in claim['scope']


def test_mcp_and_browser_expose_any_heuristic_claim():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='any', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] is None
    assert profile['heuristic_claim'] == CLAIM_ID

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert browser['rules']['any']['heuristic_claim'] == CLAIM_ID
