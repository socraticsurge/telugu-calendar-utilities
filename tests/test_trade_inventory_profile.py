"""Trade-inventory purchase preserves Raman's buyer-side formula."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.trade_inventory.purchase'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_inventory_profile_keeps_best_as_preferences():
    rules = ACTIVITY_RULES['business_inventory_purchase']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == ['muhurta.purchase.general']
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Adivaram', 'Somavaram', 'Budhavaram', 'Guruvaram',
        'Shukravaram', 'Shanivaram',
    ]
    assert rules['prefer_vara'] == ['Guruvaram']
    assert rules['prefer_tithi_numbers'] == [10]
    assert rules['prefer_nakshatras'] == ['Pushya']
    assert 'allowed_tithi_numbers' not in rules
    assert 'allowed_nakshatras' not in rules


def test_each_source_preference_scores_without_becoming_a_gate():
    # Thursday + Pushya, but Panchami: both applicable preferences score.
    slots = day_slots(_day(2026, 5, 21), 'business_inventory_purchase')
    assert slots
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)
    for slot in slots:
        matches = slot['reason_groups']['activity_match']
        assert 'Guruvaram favoured for Trade inventory purchase (+1)' in matches
        assert 'Pushya specifically favoured for Trade inventory purchase (+1)' in matches

    # Dashami independently scores on a non-Thursday, non-Pushya fixture.
    dashami = day_slots(_day(2026, 1, 28), 'business_inventory_purchase')
    assert dashami
    assert all(any(
        'Shukla Dashami specifically favoured for Trade inventory purchase (+1)'
        == reason for reason in slot['reason_groups']['activity_match'])
        for slot in dashami)


def test_tuesday_rejected_while_saturday_is_admissible_but_unpreferred():
    assert diagnose_day(_day(2026, 1, 6), 'business_inventory_purchase') == (
        'Mangalavaram · Trade inventory purchase source profile '
        'does not admit this weekday')
    saturday = day_slots(_day(2026, 1, 3), 'business_inventory_purchase')
    assert saturday
    assert all(not any('Shanivaram favoured' in reason for reason in
                       slot['reason_groups']['activity_match'])
               for slot in saturday)


def test_slot_notes_omit_weekday_guidance_that_does_not_apply():
    thursday = day_slots(
        _day(2026, 5, 21), 'business_inventory_purchase')
    assert thursday
    assert all(not any('Saturday' in note for note in slot['reason_groups']['notes'])
               for slot in thursday)

    saturday = day_slots(
        _day(2026, 1, 3), 'business_inventory_purchase')
    assert saturday
    assert all(any('Saturday is described as passable' in note
                   for note in slot['reason_groups']['notes'])
               for slot in saturday)


def test_claim_mcp_and_browser_publish_the_same_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993', 'MC-HINDI-IA']
    assert "Chapter X, 'Buying for Business,' printed p. 45" in claim['locator']
    assert 'verse 16' in claim['locator']

    result = json.loads(tool_find_muhurta(
        '2026-05-21', days=1, activity='business_inventory_purchase',
        city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'business_inventory_purchase' in browser['groups'][2]['activities']
    exported = browser['rules']['business_inventory_purchase']
    for field in (
        'source_claim', 'related_claims', 'allowed_varas', 'prefer_vara',
        'prefer_tithi_numbers', 'prefer_nakshatras', 'manual_checks',
        'manual_prerequisites',
    ):
        assert exported[field] == ACTIVITY_RULES['business_inventory_purchase'][field]
