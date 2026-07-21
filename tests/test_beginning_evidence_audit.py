"""New Beginning must disclose its Dharma-kriya scope mismatch."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.beginning.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_beginning_profile_records_scope_and_proxy_conflict():
    rules = ACTIVITY_RULES['beginning']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_tithi_class'] == 'Nanda'
    assert rules['prefer_choghadiya'] == ('Amrit', 1)
    assert len(rules['manual_checks']) == 3
    assert 'thirteen Nakshatras' not in rules['manual_checks'][0]
    assert 'Guru in Lagna' in rules['manual_checks'][1]
    assert 'not every modern project' in rules['manual_checks'][2]


def test_beginning_claim_has_exact_dharma_kriya_boundary():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert 'Dharma-kriya commencement in verse 30' in claim['locator']
    assert 'thirteen Nakshatras' in claim['scope']
    assert 'not a universal modern' in claim['scope']
    assert 'Amrit Choghadiya and Nanda-Tithi rewards' in claim['scope']


def test_mcp_and_browser_expose_beginning_audit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='beginning', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['beginning']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['beginning']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['beginning']['manual_checks']
