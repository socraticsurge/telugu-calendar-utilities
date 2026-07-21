"""Business launch must disclose its capital-deployment mismatch."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.business.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_business_profile_records_scope_and_lagna_conflict():
    rules = ACTIVITY_RULES['business']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_lagna_class'] == 'Sthira'
    assert rules['prefer_tithi_class'] == 'Nanda'
    assert len(rules['manual_checks']) == 3
    assert 'Chara—not Sthira—Lagna' in rules['manual_checks'][0]
    assert 'benefics in the 5th and 9th' in rules['manual_checks'][1]
    assert 'distinct source activities' in rules['manual_checks'][2]


def test_business_claim_has_exact_capital_deployment_boundary():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Dravyaprayoga and taking a loan,' verse 27" in claim['locator']
    assert 'requires Chara Lagna' in claim['scope']
    assert 'directly contradicts the configured Sthira-Lagna bonus' in claim['scope']
    assert 'Marketplace transactions and purchase for inventory are separate' in claim['scope']


def test_mcp_and_browser_expose_business_audit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='business', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['business']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['business']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['business']['manual_checks']
