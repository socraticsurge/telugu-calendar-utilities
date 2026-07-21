"""Job start and contract signing must not share silent authority."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.job_contract.profile_conflict'


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_job_contract_profile_records_taxonomy_conflict():
    rules = ACTIVITY_RULES['job']
    assert rules['audit_claim'] == CLAIM_ID
    assert 'source_claim' not in rules
    assert rules['prefer_choghadiya'] == ('Amrit', 1)
    assert rules['prefer_tithi_class'] == 'Nanda'
    assert rules['prefer_lagna_class'] == 'Sthira'
    assert len(rules['manual_checks']) == 3
    assert 'entering service' in rules['manual_checks'][0]
    assert 'Employer/employee check' in rules['manual_checks'][1]
    assert 'not a modern' in rules['manual_checks'][2]


def test_job_contract_claim_has_both_exact_source_boundaries():
    claim = _claim()
    assert claim['verification_state'] == 'contradicted'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Entering the service of a master,' verse 26" in claim['locator']
    assert "'Sandhana Muhurta,' verse 42" in claim['locator']
    assert 'does not equate Sandhana' in claim['scope']
    assert 'substitutes Amrit Choghadiya, Nanda Tithi' in claim['scope']


def test_mcp_and_browser_expose_job_contract_audit():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='job', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] is None
    assert profile['audit_claim'] == CLAIM_ID
    assert profile['manual_checks'] == ACTIVITY_RULES['job']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['job']
    assert exported['audit_claim'] == CLAIM_ID
    assert exported['manual_checks'] == ACTIVITY_RULES['job']['manual_checks']
