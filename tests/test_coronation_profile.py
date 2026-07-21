"""Contract tests for Raman's coronation election rules."""
import json

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


def test_coronation_profile_matches_raman_chapter_xvi():
    rules = ACTIVITY_RULES['coronation']
    assert rules['source_claim'] == 'muhurta.coronation'
    assert rules['allowed_nakshatras'] == [
        'Ashwini', 'Rohini', 'Mrigashira', 'Punarvasu', 'Pushya',
        'Uttara Phalguni', 'Hasta', 'Anuradha', 'Uttara Ashadha',
        'Shravana', 'Uttara Bhadrapada', 'Revati',
    ]
    assert rules['allowed_tithi_names'] == [
        'Shukla Pratipat', 'Shukla Dwitiya', 'Shukla Tritiya',
        'Shukla Panchami', 'Shukla Saptami', 'Shukla Dashami',
        'Shukla Ekadashi', 'Shukla Trayodashi', 'Pournami',
        'Krishna Dwitiya', 'Krishna Dashami',
    ]
    assert rules['allowed_lagnas'] == [
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Simha', 'Dhanu',
        'Kumbha', 'Meena',
    ]


def test_mcp_publishes_coronation_claim_and_exact_gates():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='coronation', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == 'muhurta.coronation'
    constraints = profile['automated_constraints']
    assert constraints['allowed_nakshatras'] == \
        ACTIVITY_RULES['coronation']['allowed_nakshatras']
    assert constraints['allowed_tithi_names'] == \
        ACTIVITY_RULES['coronation']['allowed_tithi_names']
    assert constraints['allowed_lagnas'] == \
        ACTIVITY_RULES['coronation']['allowed_lagnas']
