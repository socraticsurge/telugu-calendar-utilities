"""Dharma-kriya commencement preserves Chintamani 30 on every surface."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.dharma_kriya.commencement'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_beginning_key_is_exact_dharma_kriya_profile():
    rules = ACTIVITY_RULES['beginning']
    assert rules['label'] == 'Dharma-kriya commencement'
    assert rules['source_claim'] == CLAIM_ID
    assert 'audit_claim' not in rules
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Adivaram', 'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram']
    assert len(rules['allowed_nakshatras']) == 13
    assert rules['allowed_lagnas'] == ['Mithuna', 'Kanya', 'Dhanu', 'Meena']
    assert 'prefer_choghadiya' not in rules
    assert 'prefer_tithi_class' not in rules


def test_claim_has_exact_scope_and_chart_boundary():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert 'Dharma-kriya commencement in verse 30' in claim['locator']
    assert 'thirteen named Nakshatras' in claim['scope']
    assert 'religious or meritorious work' in claim['scope']
    assert 'personal Guru strength' in claim['scope']


def test_mcp_keeps_expert_profile_while_browser_hides_it():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='beginning', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'beginning' not in browser['rules']
    assert all('beginning' not in group['activities']
               for group in browser['groups'])
