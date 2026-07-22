"""The legacy litigation key is an explicit alias, not a second election."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import (
    ACTIVITY_ALIASES, ACTIVITY_RULES, get_activity_rules, resolve_activity,
)


ROOT = Path(__file__).parents[1]


def _claims():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return {claim['id']: claim for claim in ledger['claims']}


def test_litigation_is_a_compatibility_alias_not_a_duplicate_profile():
    assert ACTIVITY_ALIASES['litigation'] == 'court'
    assert 'litigation' not in ACTIVITY_RULES
    assert resolve_activity('litigation') == 'court'
    assert get_activity_rules('litigation') is ACTIVITY_RULES['court']
    rules = get_activity_rules('litigation')
    assert 'prefer_bhadra_puchha' not in rules
    assert 'prefer_tithi_class' not in rules
    assert 'avoid_tithi_class' not in rules
    assert 'prefer_vara' not in rules


def test_historical_conflict_and_shared_bhadra_debt_have_exact_locators():
    claims = _claims()
    historical = claims['muhurta.litigation.profile_conflict']
    assert historical['verification_state'] == 'contradicted'
    assert 'removed standalone Litigation / contest profile' in \
        historical['scope']

    bhadra = claims['panchangam.bhadra_mukha_puchha.approximation']
    assert bhadra['verification_state'] == 'contradicted'
    assert bhadra['source_ids'] == ['MC-HINDI-IA']
    assert 'verses 43-45' in bhadra['locator']
    assert 'printed pp. 20-21' in bhadra['locator']
    assert 'Tithi-specific numbered Yamas' in bhadra['scope']
    assert 'proportionally as 5:8:3' in bhadra['scope']


def test_mcp_discloses_alias_resolution_and_exact_court_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-04-20', days=1, activity='litigation', city='Hyderabad'))
    assert result['activity'] == 'litigation'
    assert result['resolved_activity'] == 'court'
    assert result['activity_profile']['alias_of'] == 'court'
    assert result['activity_profile']['source_claim'] == \
        'muhurta.court.filing_lawsuit'
    assert result['activity_profile']['audit_claim'] is None
    assert result['activity_profile']['automated_constraints'][
        'allowed_varas'] == ACTIVITY_RULES['court']['allowed_varas']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'litigation' not in browser['rules']
