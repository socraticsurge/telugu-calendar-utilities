"""Capital-deployment rules preserve Chintamani 27 on every surface."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.capital_deployment'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_business_key_is_exact_capital_deployment_profile():
    rules = ACTIVITY_RULES['business']
    assert rules['label'] == 'Deploying capital / business investment'
    assert rules['source_claim'] == CLAIM_ID
    assert 'audit_claim' not in rules
    assert rules['manual_prerequisites'] is True
    assert len(rules['allowed_nakshatras']) == 12
    assert rules['required_lagna_class'] == 'Chara'
    for field in (
        'prefer_choghadiya', 'prefer_tithi_class', 'prefer_vara',
        'prefer_lagna_class',
    ):
        assert field not in rules


def test_claim_has_exact_scope_and_chart_boundary():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Dravyaprayoga and taking a loan,' verse 27" in claim['locator']
    assert 'twelve named Nakshatras' in claim['scope']
    assert 'Chara Lagna' in claim['scope']
    assert 'unoccupied 8th' in claim['scope']
    assert 'does not authorize a universal company-founding election' in \
        claim['scope']


def test_mcp_and_browser_expose_the_same_verified_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='business', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['business']
    for field in (
        'label', 'source_claim', 'manual_prerequisites',
        'allowed_nakshatras', 'required_lagna_class', 'manual_checks',
    ):
        assert exported[field] == ACTIVITY_RULES['business'][field]
