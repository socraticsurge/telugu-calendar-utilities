"""Generic Ceremony must disclose its Shantika/Paushtika mismatch."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.ceremony.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_ceremony_profile_records_tithi_and_scope_conflict():
    rules = ACTIVITY_RULES['ceremony']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['avoid_tithi_class'] == ['Jaya']
    assert len(rules['manual_checks']) == 3
    assert 'Rikta Tithis' in rules['manual_checks'][0]
    assert 'configured Jaya family' in rules['manual_checks'][0]
    assert 'Surya in the 10th' in rules['manual_checks'][1]
    assert 'emergency Shanti' in rules['manual_checks'][2]


def test_ceremony_claim_has_exact_rite_boundary():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Shantika and Paushtika Muhurta,' verse 34" in claim['locator']
    assert 'does not match the configured whole-Jaya-family penalty' in claim['scope']
    assert 'fifteen Nakshatras' in claim['scope']
    assert 'emergency Shanti' in claim['scope']


def test_mcp_and_browser_expose_ceremony_audit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='ceremony', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['ceremony']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['ceremony']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['ceremony']['manual_checks']
