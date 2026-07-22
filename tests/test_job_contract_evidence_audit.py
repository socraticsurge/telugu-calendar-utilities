"""Service-entry rules preserve Chintamani 26 on every surface."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.service_entry'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_job_key_is_exact_service_entry_profile():
    rules = ACTIVITY_RULES['job']
    assert rules['label'] == 'Entering employment / starting service'
    assert rules['source_claim'] == CLAIM_ID
    assert 'audit_claim' not in rules
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Budhavaram', 'Shukravaram', 'Adivaram', 'Guruvaram']
    assert rules['allowed_nakshatras'] == [
        'Ashwini', 'Pushya', 'Hasta', 'Chitra', 'Anuradha', 'Mrigashira',
        'Revati']
    for field in (
        'prefer_choghadiya', 'prefer_tithi_class', 'prefer_vara',
        'prefer_lagna_class',
    ):
        assert field not in rules


def test_claim_has_exact_scope_and_relationship_boundary():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Entering the service of a master,' verse 26" in claim['locator']
    assert 'seven named Nakshatras' in claim['scope']
    assert 'birth-Nakshatra Yoni friendship' in claim['scope']
    assert 'does not cover offer acceptance' in claim['scope']


def test_mcp_and_browser_expose_the_same_verified_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='job', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['job']
    for field in (
        'label', 'source_claim', 'manual_prerequisites', 'allowed_varas',
        'allowed_nakshatras', 'manual_checks',
    ):
        assert exported[field] == ACTIVITY_RULES['job'][field]
