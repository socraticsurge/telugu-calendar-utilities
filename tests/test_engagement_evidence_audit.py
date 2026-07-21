"""Engagement must not silently inherit marriage authority."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.engagement.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(claim for claim in ledger['claims'] if claim['id'] == CLAIM_ID)


def test_engagement_records_scope_and_rule_conflict():
    rules = ACTIVITY_RULES['engagement']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_tithi_class'] == 'Purna'
    assert rules['avoid_tithi_class'] == ['Jaya']
    assert len(rules['manual_checks']) == 2


def test_engagement_claim_does_not_mislabel_marriage_as_direct_authority():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993']
    assert "found no 'Betrothal,' 'Engagement,' or 'Nischayam'" in claim['locator']
    assert "nearest candidate is Chapter IX" in claim['locator']
    assert 'must not inherit marriage authority' in claim['scope']
    assert 'Shukla Tritiya and Trayodashi are admitted' in claim['scope']


def test_mcp_and_browser_expose_engagement_audit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='engagement', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['engagement']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['engagement']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['engagement']['manual_checks']
