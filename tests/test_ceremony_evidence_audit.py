"""Shantika/Paushtika rules preserve Chintamani 34 on every surface."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.shantika_paushtika'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_ceremony_key_is_the_exact_rite_profile():
    rules = ACTIVITY_RULES['ceremony']
    assert rules['label'] == 'Shantika / Paushtika rite'
    assert rules['source_claim'] == CLAIM_ID
    assert 'audit_claim' not in rules
    assert rules['manual_prerequisites'] is True
    assert rules['skip_on_sankramana'] is True
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram']
    assert rules['avoid_tithi_numbers'] == [4, 8, 9, 14, 15]
    assert len(rules['allowed_nakshatras']) == 15
    assert len(rules['manual_checks']) == 4


def test_claim_has_exact_locator_scope_and_exception():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Shantika and Paushtika Muhurta,' verse 34" in claim['locator']
    assert 'fifteen named Nakshatras' in claim['scope']
    assert 'remedial Shanti' in claim['scope']
    assert 'not a universal ceremony election' in claim['scope']


def test_mcp_and_browser_expose_the_same_verified_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='ceremony', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['ceremony']
    for field in (
        'label', 'source_claim', 'manual_prerequisites',
        'skip_on_sankramana', 'allowed_varas', 'avoid_tithi_numbers',
        'allowed_nakshatras', 'manual_checks',
    ):
        assert exported[field] == ACTIVITY_RULES['ceremony'][field]
