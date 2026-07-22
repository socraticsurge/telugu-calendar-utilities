"""Gruhapravesha preserves Raman's first-entry rules on every surface."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.gruhapravesha'
DIVERGENCE_ID = 'muhurta.gruhapravesha.drkpanchang_divergence'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_gruhapravesha_profile_matches_raman_crosswalk():
    rules = ACTIVITY_RULES['gruhapravesha']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == [DIVERGENCE_ID]
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram']
    assert rules['allowed_solar_signs'] == [
        'Makara', 'Kumbha', 'Meena', 'Mesha', 'Vrishabha', 'Mithuna']
    assert rules['allowed_tithi_names'] == [
        'Krishna Pratipat', 'Shukla Dwitiya', 'Shukla Tritiya',
        'Shukla Panchami', 'Shukla Saptami', 'Shukla Dashami',
        'Shukla Ekadashi', 'Shukla Trayodashi',
    ]
    assert rules['allowed_nakshatras'] == [
        'Rohini', 'Mrigashira', 'Uttara Ashadha', 'Chitra',
        'Uttara Bhadrapada', 'Anuradha', 'Revati',
    ]
    assert rules['allowed_lagnas'] == [
        'Vrishabha', 'Simha', 'Vrischika', 'Kumbha',
        'Mithuna', 'Kanya', 'Dhanu', 'Meena',
    ]
    assert rules['prefer_lagna_class'] == 'Sthira'


def test_exact_weekday_tithi_star_and_uttarayana_gates():
    assert day_slots(_day(2026, 6, 24), 'gruhapravesha')  # Wed, Dashami, Chitra
    sunday = _day(2026, 6, 21)
    assert day_slots(sunday, 'gruhapravesha') == []
    assert diagnose_day(sunday, 'gruhapravesha') == (
        'Adivaram · Gruhapravesha (First entry into new home) source profile '
        'does not admit this weekday')

    # Thursday is admitted, but this Magha date fails the exact star gate.
    assert day_slots(_day(2026, 1, 8), 'gruhapravesha') == []
    # This otherwise valid star/Tithi/weekday is outside Uttarayana.
    dakshinayana = _day(2026, 11, 11)
    assert day_slots(dakshinayana, 'gruhapravesha') == []
    assert diagnose_day(dakshinayana, 'gruhapravesha') == (
        'Surya in Tula · Gruhapravesha (First entry into new home) source '
        'profile does not admit this solar Rasi')


def test_manual_chart_ritual_and_pregnancy_checks_cap_the_tier():
    slots = day_slots(_day(2026, 6, 24), 'gruhapravesha')
    assert slots
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)


def test_claims_have_exact_locator_scope_and_disclosed_divergence():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993']
    assert "section 'Entering a new house,'" in claim['locator']
    assert 'printed pp. 52-54' in claim['locator']
    assert 'first entry into a newly built home' in claim['scope']

    divergence = next(
        item for item in ledger['claims'] if item['id'] == DIVERGENCE_ID)
    assert divergence['verification_state'] == 'contradicted'
    assert divergence['source_ids'] == ['DP-DAY-PAGE']
    assert 'qualifying Saturdays' in divergence['scope']


def test_mcp_and_browser_expose_the_same_verified_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-24', days=1, activity='gruhapravesha', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['related_claims'] == [DIVERGENCE_ID]
    assert profile['manual_prerequisites'] is True
    for field in (
        'allowed_varas', 'allowed_solar_signs', 'allowed_tithi_names',
        'allowed_nakshatras', 'allowed_lagnas',
    ):
        assert profile['automated_constraints'][field] == \
            ACTIVITY_RULES['gruhapravesha'][field]

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['gruhapravesha']
    for field in (
        'source_claim', 'related_claims', 'manual_prerequisites',
        'allowed_varas', 'allowed_solar_signs', 'allowed_tithi_names',
        'allowed_nakshatras', 'allowed_lagnas', 'prefer_lagna_class',
        'manual_checks',
    ):
        assert exported[field] == ACTIVITY_RULES['gruhapravesha'][field]
