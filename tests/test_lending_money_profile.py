"""Lending-money rules preserve creditor-side source conditions."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.lending_money'
DIVERGENCE_ID = 'muhurta.lending.drkpanchang_divergence'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_lending_profile_matches_raman_conditions():
    rules = ACTIVITY_RULES['lending_money']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == [DIVERGENCE_ID]
    assert rules['allowed_varas'] == [
        'Adivaram', 'Somavaram', 'Budhavaram', 'Guruvaram', 'Shanivaram']
    assert rules['avoid_nakshatras'] == [
        'Krittika', 'Magha', 'Moola', 'Shatabhisha',
        'Uttara Phalguni', 'Punarvasu',
    ]
    assert rules['avoid_janma_nakshatra'] is True
    assert rules['avoid_vara_tithi_names'] == [['Shanivaram', 'Amavasya']]


def test_weekday_star_and_personal_star_gates():
    assert diagnose_day(_day(2026, 1, 2), 'lending_money') == (
        'Shukravaram · Lending money / giving a loan source profile '
        'does not admit this weekday')
    assert diagnose_day(_day(2026, 1, 6), 'lending_money') == (
        'Mangalavaram · Lending money / giving a loan source profile '
        'does not admit this weekday')
    assert day_slots(_day(2026, 1, 4), 'lending_money') == []  # Punarvasu

    rohini_day = _day(2026, 1, 1)
    assert day_slots(rohini_day, 'lending_money')
    assert day_slots(
        rohini_day, 'lending_money', janma_nakshatras=['Rohini']) == []

    # Raman admits Wednesday; the disclosed Drik Panchang divergence must not
    # silently become an additional hard gate.
    assert day_slots(_day(2026, 1, 14), 'lending_money')


def test_saturday_amavasya_is_exact_conditional_not_two_broad_bans():
    # Bharani is not in the fixed star exclusions, so this isolates the pair.
    assert day_slots(_day(2026, 5, 16), 'lending_money') == []
    # Ordinary Saturday remains admissible.
    assert day_slots(_day(2026, 1, 3), 'lending_money')


def test_manual_chart_and_financial_checks_cap_the_tier():
    slots = day_slots(_day(2026, 1, 1), 'lending_money')
    assert slots
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)


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
    assert divergence['source_ids'] == ['DP-DAY-PAGE']

    result = json.loads(tool_find_muhurta(
        '2026-01-01', days=1, activity='lending_money', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['automated_constraints']['avoid_vara_tithi_names'] == [
        ['Shanivaram', 'Amavasya']]

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'lending_money' in browser['groups'][2]['activities']
    exported = browser['rules']['lending_money']
    for field in (
        'source_claim', 'related_claims', 'allowed_varas',
        'avoid_nakshatras', 'avoid_janma_nakshatra',
        'avoid_vara_tithi_names', 'manual_checks', 'manual_prerequisites',
    ):
        assert exported[field] == ACTIVITY_RULES['lending_money'][field]
