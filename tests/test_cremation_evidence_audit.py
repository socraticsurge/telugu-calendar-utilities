"""Cremation's four-and-a-half-Nakshatra conflict remains explicit."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.cremation.profile_conflict'


def _ledger():
    return json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))


def test_cremation_records_precision_conflict_and_safety_boundary():
    rules = ACTIVITY_RULES['cremation']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['skip_on_panchaka_nakshatra'] is True
    assert len(rules['manual_checks']) == 2
    assert 'latter half of Dhanishtha' in rules['manual_checks'][0]
    assert 'officiating priest' in rules['manual_checks'][1]


def test_cremation_claim_has_classical_verse_and_exact_conflict():
    ledger = _ledger()
    source = next(item for item in ledger['sources'] if item['id'] == 'MC-HINDI-IA')
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert source['author'] == 'Rama Daivajna'
    assert 'muhurta-chintamani-hindi' in source['url']
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Pretakriya ka muhurta,' verse 48" in claim['locator']
    assert 'over-rejects the first half' in claim['scope']
    assert 'generic auspicious Choghadiya venture' in claim['scope']


def test_mcp_exposes_cremation_audit_and_browser_boundary():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='cremation', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['cremation']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'cremation' not in browser['rules']
