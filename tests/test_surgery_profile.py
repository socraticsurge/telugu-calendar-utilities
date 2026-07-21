"""Contract tests for Raman's surgical-operations election."""
import json

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


def test_surgery_profile_matches_raman_chapter_xv():
    rules = ACTIVITY_RULES['surgery']
    assert rules['source_claim'] == 'muhurta.surgery'
    assert rules['allowed_varas'] == ['Mangalavaram', 'Shanivaram']
    assert rules['allowed_tithi_names'] == [
        'Shukla Chaturthi', 'Shukla Navami', 'Shukla Chaturdashi',
    ]
    assert rules['allowed_nakshatras'] == [
        'Ardra', 'Jyeshtha', 'Ashlesha', 'Moola',
    ]
    assert rules['avoid_karana'] == ['Vishti']
    assert rules['manual_checks'][0].startswith(
        'Medical urgency and the treating clinician')


def test_mcp_publishes_surgery_claim_gates_and_safety_boundary():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='surgery', city='Hyderabad'))
    profile = result['activity_profile']
    rules = ACTIVITY_RULES['surgery']
    assert profile['source_claim'] == 'muhurta.surgery'
    assert profile['automated_constraints']['allowed_varas'] == \
        rules['allowed_varas']
    assert profile['automated_constraints']['allowed_tithi_names'] == \
        rules['allowed_tithi_names']
    assert profile['automated_constraints']['allowed_nakshatras'] == \
        rules['allowed_nakshatras']
    assert profile['manual_checks'] == rules['manual_checks']
