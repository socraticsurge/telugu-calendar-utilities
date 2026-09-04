"""Borrowing-money rules preserve debtor-side source boundaries."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.borrowing_money'
DIVERGENCE_ID = 'muhurta.borrowing.chintamani_divergence'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_borrowing_profile_matches_raman_nakshatra_prohibitions():
    rules = ACTIVITY_RULES['borrowing_money']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == [DIVERGENCE_ID]
    assert rules['manual_prerequisites'] is True
    assert rules['avoid_nakshatras'] == [
        'Krittika', 'Moola', 'Punarvasu', 'Dhanishtha']
    assert rules['avoid_janma_nakshatra'] is True
    assert 'allowed_varas' not in rules
    assert 'prefer_vara' not in rules


def test_universal_and_personal_star_gates_are_enforced():
    # Punarvasu is one of Raman's four universal prohibitions.
    assert day_slots(_day(2026, 1, 4), 'borrowing_money') == []

    rohini_day = _day(2026, 1, 1)
    assert day_slots(rohini_day, 'borrowing_money')
    # The same otherwise-admissible date is rejected for a Rohini-born borrower.
    assert day_slots(
        rohini_day, 'borrowing_money', janma_nakshatras=['Rohini']) == []


def test_manual_chart_and_financial_checks_cap_the_tier():
    slots = day_slots(_day(2026, 1, 1), 'borrowing_money')
    assert slots
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['borrowing_money']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_claims_and_product_surfaces_publish_the_same_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == [
        'BVR-MUHURTHA-1993',
        'BVR-MUHURTHA-CHISTABO-2020',
    ]
    divergence = next(
        item for item in ledger['claims'] if item['id'] == DIVERGENCE_ID)
    assert divergence['verification_state'] == 'contradicted'
    assert divergence['source_ids'] == ['MC-HINDI-IA']

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='borrowing_money', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['related_claims'] == [DIVERGENCE_ID]
    assert profile['automated_constraints']['avoid_janma_nakshatra'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'borrowing_money' in browser['groups'][2]['activities']
    exported = browser['rules']['borrowing_money']
    for field in (
        'source_claim', 'related_claims', 'avoid_nakshatras',
        'avoid_janma_nakshatra', 'manual_checks', 'manual_prerequisites',
    ):
        assert exported[field] == ACTIVITY_RULES['borrowing_money'][field]
