"""Wedding preserves Raman's complete election profile across surfaces."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.wedding'
DIVERGENCE_ID = 'muhurta.wedding.drkpanchang_divergence'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_wedding_profile_matches_complete_raman_crosswalk():
    rules = ACTIVITY_RULES['wedding']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == [DIVERGENCE_ID]
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_maasams'] == [
        'Magha', 'Phalguna', 'Vaishakha', 'Jyeshtha',
        'Kartika', 'Margashira']
    assert rules['allowed_maasa_solar_pairs'] == [
        ['Pushya', 'Makara'], ['Chaitra', 'Mesha']]
    assert rules['allowed_varas'] == [
        'Adivaram', 'Somavaram', 'Budhavaram', 'Guruvaram',
        'Shukravaram', 'Shanivaram']
    assert rules['prefer_vara'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram']
    assert rules['allowed_tithi_names'] == [
        'Shukla Pratipat', 'Shukla Dwitiya', 'Shukla Tritiya',
        'Shukla Panchami', 'Shukla Saptami', 'Shukla Dashami',
        'Shukla Ekadashi', 'Shukla Trayodashi', 'Krishna Pratipat',
        'Krishna Dwitiya', 'Krishna Tritiya', 'Krishna Panchami',
        'Krishna Saptami', 'Krishna Dashami']
    assert len(rules['allowed_nakshatras']) == 11
    assert rules['avoid_karana'] == ['Vishti']
    assert rules['avoid_nitya_yogas'] == [
        'Vyatipata', 'Dhruva', 'Ganda', 'Vajra', 'Shoola',
        'Vishkambha', 'Atiganda', 'Vyaghata', 'Parigha']
    assert rules['allowed_lagnas'] == [
        'Mithuna', 'Kanya', 'Tula', 'Vrishabha',
        'Karka', 'Simha', 'Dhanu', 'Kumbha']
    assert rules['prefer_lagnas'] == ['Mithuna', 'Kanya', 'Tula']
    assert 'prefer_tithi_class' not in rules
    assert 'avoid_tithi_class' not in rules


def test_exact_month_weekday_tithi_star_yoga_and_lagna_gates():
    assert day_slots(_day(2026, 4, 20), 'wedding')  # Mon, Tritiya, Rohini
    tuesday = _day(2026, 4, 21)
    assert day_slots(tuesday, 'wedding') == []
    assert diagnose_day(tuesday, 'wedding') == (
        'Mangalavaram · Wedding (Vivaha) source profile does not admit this '
        'weekday')
    assert day_slots(_day(2026, 6, 29), 'wedding') == []  # Pournami
    assert day_slots(_day(2026, 6, 21), 'wedding') == []  # Purva Phalguni
    assert day_slots(_day(2025, 2, 23), 'wedding') == []  # Vajra Yoga


def test_conditional_month_exceptions_are_pair_scoped():
    # Pushya is rejected before Surya enters Makara, then admitted by the
    # exact pair (other gates may still reject the resulting day/slots).
    rejected = _day(2026, 1, 1)
    assert 'Pushya Maasa' in diagnose_day(rejected, 'wedding')
    assert 'lunar month' in diagnose_day(rejected, 'wedding')
    assert diagnose_day(_day(2026, 1, 16), 'wedding') != (
        'Pushya Maasa · Wedding (Vivaha) source profile does not admit this '
        'lunar month')
    assert diagnose_day(_day(2026, 4, 15), 'wedding') != (
        'Chaitra Maasa · Wedding (Vivaha) source profile does not admit this '
        'lunar month')


def test_manual_pada_chart_and_couple_checks_cap_the_tier():
    slots = day_slots(_day(2026, 4, 20), 'wedding')
    assert slots
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)


def test_verified_claim_and_current_practice_divergence_are_explicit():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == [
        'BVR-MUHURTHA-1993',
        'BVR-MUHURTHA-CHISTABO-2020',
    ]
    assert "'Electing a time for marriage,'" in claim['locator']
    assert 'internal printed pp. 41-42 (physical PDF pp. 45-46)' in claim['locator']

    divergence = next(
        item for item in ledger['claims'] if item['id'] == DIVERGENCE_ID)
    assert divergence['verification_state'] == 'contradicted'
    assert divergence['source_ids'] == ['DP-DAY-PAGE']
    assert 'Tuesdays' in divergence['scope']


def test_mcp_and_browser_publish_identical_decisive_rules():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-04-20', days=1, activity='wedding', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['related_claims'] == [DIVERGENCE_ID]
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['wedding']
    for field in (
        'source_claim', 'related_claims', 'manual_prerequisites',
        'allowed_maasams', 'allowed_maasa_solar_pairs', 'allowed_varas',
        'prefer_vara', 'allowed_tithi_names', 'allowed_nakshatras',
        'avoid_karana', 'avoid_nitya_yogas', 'allowed_lagnas',
        'prefer_lagnas', 'manual_checks',
    ):
        assert exported[field] == ACTIVITY_RULES['wedding'][field]
        if field in profile['automated_constraints']:
            assert profile['automated_constraints'][field] == exported[field]
