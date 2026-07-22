"""Homahuti must implement Muhurta Chintamani 35-36 exactly."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.homa import (
    agnivasa_remainder, homa_election, homahuti_group,
)


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.homahuti'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_three_nakshatra_groups_cycle_from_surya():
    assert homahuti_group('Ashvini', 'Ashvini') == ('Surya', 1)
    assert homahuti_group('Ashvini', 'Ardra') == ('Budha', 2)
    assert homahuti_group('Revati', 'Bharani') == ('Surya', 1)
    assert homahuti_group('Revati', 'Krittika') == ('Budha', 2)


def test_agnivasa_uses_full_tithi_ordinal_and_sunday_based_vara():
    assert agnivasa_remainder('Shukla Pratipat', 'Adivaram') == 3
    assert agnivasa_remainder('Pournami', 'Adivaram') == 1
    assert agnivasa_remainder('Krishna Pratipat', 'Adivaram') == 2
    assert agnivasa_remainder('Amavasya', 'Shanivaram') == 2


def test_both_homa_conditions_are_hard_gates():
    admitted, reasons = homa_election(
        'Shukla Pratipat', 'Adivaram', 'Ardra', 'Ashvini')
    assert admitted
    assert any('Budha' in reason for reason in reasons)
    assert any('remainder 3' in reason for reason in reasons)
    assert not homa_election(
        'Shukla Pratipat', 'Adivaram', 'Ashvini', 'Ashvini')[0]
    assert not homa_election(
        'Shukla Tritiya', 'Adivaram', 'Ardra', 'Ashvini')[0]


def test_homa_profile_and_verified_claim():
    rules = ACTIVITY_RULES['yajna']
    assert rules['label'] == 'Homa offering (Homahuti)'
    assert rules['source_claim'] == CLAIM_ID
    assert rules['require_homa_election'] is True
    assert 'audit_claim' not in rules
    assert 'prefer_tithi_class' not in rules
    assert _claim()['verification_state'] == 'verified'


def test_mcp_and_browser_expose_automated_homa_election():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='yajna', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['automated_constraints']['require_homa_election'] is True
    assert result['slots']
    for slot in result['slots']:
        match = slot['reason_groups']['activity_match']
        assert any('Homahuti group' in reason for reason in match)
        assert any('Agnivasa remainder' in reason for reason in match)

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['yajna']
    assert exported['source_claim'] == CLAIM_ID
    assert exported['require_homa_election'] is True
