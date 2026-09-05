"""Completed-house purchase follows Raman's distinct Chapter XII profile."""
import json
from datetime import date
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day

ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.house_purchase.completed'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_completed_house_profile_matches_raman_chapter_xii():
    rules = ACTIVITY_RULES['house_purchase']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == ['muhurta.purchase.general']
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == ['Guruvaram', 'Shukravaram']
    assert rules['allowed_tithi_numbers'] == [1, 6, 11]
    assert rules['allowed_nakshatras'] == [
        'Mrigashira', 'Ashlesha', 'Magha', 'Purva Phalguni',
        'Vishakha', 'Moola', 'Punarvasu', 'Revati',
    ]
    assert rules['prefer_lagnas'] == [
        'Vrishabha', 'Mithuna', 'Simha', 'Tula', 'Vrischika']


def test_source_gates_positive_fixture_and_manual_tier_cap():
    # Friday, Shukla Shashthi, Ashlesha.
    slots = day_slots(_day(2026, 5, 22), activity='house_purchase')
    assert slots
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert any(
        'lagna specifically favoured for Completed house purchase (+1)'
        in reason
        for slot in slots for reason in slot['reason_groups']['activity_match'])
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['house_purchase']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_wrong_weekday_is_rejected_and_scope_is_not_inherited():
    assert diagnose_day(_day(2026, 1, 4), 'house_purchase') == (
        'Adivaram · Completed house purchase source profile '
        'does not admit this weekday')
    assert ACTIVITY_RULES['house_purchase'] != ACTIVITY_RULES['property']
    assert ACTIVITY_RULES['house_purchase'] != ACTIVITY_RULES['purchase']


def test_claim_and_surfaces_publish_the_same_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == [
        'BVR-MUHURTHA-1993',
        'BVR-MUHURTHA-CHISTABO-2020',
    ]
    assert "Chapter XII, 'Buying Houses,' inspected" in claim['locator']
    assert 'internal printed p. 54 (physical PDF p. 58)' in claim['locator']

    result = json.loads(tool_find_muhurta(
        '2026-01-08', days=1, activity='house_purchase', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'house_purchase' in browser['groups'][2]['activities']
    exported = browser['rules']['house_purchase']
    for field in (
        'source_claim', 'related_claims', 'allowed_varas',
        'allowed_tithi_numbers', 'allowed_nakshatras', 'prefer_lagnas',
        'manual_checks', 'manual_prerequisites',
    ):
        assert exported[field] == ACTIVITY_RULES['house_purchase'][field]
