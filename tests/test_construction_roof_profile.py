"""Contract tests for Raman's roofing-stage rising-Rasi rule."""
import json

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


def test_construction_roof_profile_matches_raman_chapter_xii():
    rules = ACTIVITY_RULES['construction_roof']
    assert rules['source_claim'] == 'muhurta.construction_roof'
    assert rules['allowed_lagnas'] == ['Vrishabha', 'Tula']
    assert rules['skip_on_panchaka_nakshatra'] is True


def test_mcp_publishes_roofing_claim_and_lagna_gate():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='construction_roof', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.construction_roof'
    assert profile['automated_constraints']['allowed_lagnas'] == [
        'Vrishabha', 'Tula',
    ]
