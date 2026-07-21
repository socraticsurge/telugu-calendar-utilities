"""Litigation Muhurtam's source conflict and Bhadra debt stay explicit."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.litigation.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(claim for claim in ledger['claims'] if claim['id'] == CLAIM_ID)


def test_litigation_records_conflict_without_inheriting_court_claim():
    rules = ACTIVITY_RULES['litigation']
    assert rules['audit_claim'] == CLAIM_ID
    assert rules['audit_claim'] != ACTIVITY_RULES['court']['audit_claim']
    assert 'source_claim' not in rules
    assert rules['prefer_vara'] == ['Mangalavaram']
    assert rules['prefer_bhadra_puchha'] == 2
    assert len(rules['manual_checks']) == 2


def test_litigation_claim_has_exact_conflict_and_bhadra_boundaries():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993']
    assert "section 'Filing law-suits,'" in claim['locator']
    assert 'printed p. 67' in claim['locator']
    assert 'Tuesday and Saturday be avoided' in claim['scope']
    assert 'lack edition-specific verse or page locators' in claim['scope']


def test_mcp_exposes_litigation_audit_and_browser_boundary_is_explicit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='litigation', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['litigation']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'litigation' not in browser['rules']
