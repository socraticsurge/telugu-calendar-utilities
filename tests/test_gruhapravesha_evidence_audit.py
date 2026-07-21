"""Gruhapravesha's known source conflict must stay visible on every surface."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.gruhapravesha.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(claim for claim in ledger['claims'] if claim['id'] == CLAIM_ID)


def test_gruhapravesha_profile_is_audited_not_claimed_as_verified():
    rules = ACTIVITY_RULES['gruhapravesha']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_tithi_class'] == 'Bhadra'
    assert rules['avoid_tithi_class'] == ['Jaya']
    assert rules['prefer_vara'] == ['Guruvaram', 'Somavaram']
    assert rules['prefer_lagna_class'] == 'Sthira'
    assert len(rules['manual_checks']) == 2


def test_gruhapravesha_conflict_has_exact_locator_and_scope():
    claim = _claim()
    assert claim['surface'] == 'muhurtam'
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993']
    assert "section 'Entering a new house,'" in claim['locator']
    assert 'printed pp. 52-54' in claim['locator']
    assert 'Shukla Tritiya and Trayodashi' in claim['scope']
    assert 'must not be presented as verification' in claim['scope']


def test_mcp_and_browser_expose_gruhapravesha_audit_claim():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-21', days=1, activity='gruhapravesha', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert len(profile['manual_checks']) == 2

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['gruhapravesha']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['gruhapravesha']['manual_checks']
