"""Yajna/Homam scoring must disclose the classical formula conflict."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.yajna.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_yajna_records_formula_and_scope_conflict():
    rules = ACTIVITY_RULES['yajna']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_tithi_class'] == 'Purna'
    assert rules['avoid_tithi_class'] == ['Jaya']
    assert len(rules['manual_checks']) == 3
    assert 'three-star groups' in rules['manual_checks'][0]
    assert 'modulo-four' in rules['manual_checks'][1]
    assert 'specific Kalpa' in rules['manual_checks'][2]


def test_yajna_claim_has_exact_verses_and_conflict_scope():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Homahuti Muhurta' and 'Agnivasa,' verses 35-36" in claim['locator']
    assert 'nine-group, three-Nakshatra cycle' in claim['scope']
    assert 'Agnivasa modulo-four test' in claim['scope']
    assert 'favorable and unfavorable Agnivasa outcomes occur within both families' in claim['scope']


def test_mcp_and_browser_expose_yajna_audit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='yajna', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['yajna']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['yajna']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['yajna']['manual_checks']
