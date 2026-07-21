"""Wedding's known source conflict must remain visible across contracts."""
import json

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


def test_wedding_profile_is_audited_but_not_claimed_as_verified():
    rules = ACTIVITY_RULES['wedding']
    assert rules['audit_claim'] == 'muhurta.wedding.profile_conflict'
    assert 'source_claim' not in rules


def test_mcp_exposes_wedding_audit_claim():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-15', days=1, activity='wedding', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == 'muhurta.wedding.profile_conflict'
