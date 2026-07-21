"""Court Muhurtam's direct weekday conflict must remain visible."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.court.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(claim for claim in ledger['claims'] if claim['id'] == CLAIM_ID)


def test_court_profile_records_conflict_not_verified_authority():
    rules = ACTIVITY_RULES['court']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_vara'] == ['Mangalavaram']
    assert rules['prefer_tithi_class'] == 'Jaya'
    assert rules['avoid_tithi_class'] == ['Purna']
    assert len(rules['manual_checks']) == 2


def test_court_conflict_has_exact_locator_and_alias_boundary():
    claim = _claim()
    assert claim['surface'] == 'muhurtam'
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993']
    assert "section 'Filing law-suits,'" in claim['locator']
    assert 'printed p. 67' in claim['locator']
    assert 'Tuesday and Saturday be avoided' in claim['scope']
    assert 'litigation activity remains independently unverified' in claim['scope']


def test_mcp_and_browser_expose_court_audit_claim():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='court', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert len(profile['manual_checks']) == 2

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['court']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['court']['manual_checks']
