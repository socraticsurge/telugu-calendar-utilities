"""Lawsuit-filing rules preserve Raman's passage on every surface."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.court.filing_lawsuit'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(claim for claim in ledger['claims'] if claim['id'] == CLAIM_ID)


def test_court_profile_matches_raman_crosswalk():
    rules = ACTIVITY_RULES['court']
    assert rules['label'] == 'Filing a lawsuit / court action'
    assert rules['source_claim'] == CLAIM_ID
    assert 'audit_claim' not in rules
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Adivaram', 'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram']
    assert rules['avoid_tithi_numbers'] == [4, 6, 8, 9, 12, 14, 15]
    assert rules['allowed_nakshatras'] == [
        'Ashwini', 'Rohini', 'Mrigashira', 'Pushya', 'Uttara Phalguni',
        'Hasta', 'Chitra', 'Anuradha', 'Dhanishtha', 'Revati',
    ]
    assert rules['allowed_lagnas'] == ['Mesha']
    assert len(rules['manual_checks']) == 6


def test_tuesday_and_saturday_are_hard_rejected():
    assert day_slots(_day(2026, 6, 16), 'court') == []
    assert diagnose_day(_day(2026, 6, 16), 'court') == (
        'Mangalavaram · Filing a lawsuit / court action source profile does '
        'not admit this weekday')
    assert day_slots(_day(2026, 6, 20), 'court') == []


def test_claim_has_exact_locator_scope_and_tithi_disclosure():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['BVR-MUHURTHA-1993']
    assert "section 'Filing law-suits,'" in claim['locator']
    assert 'printed p. 67' in claim['locator']
    assert 'recurring explicit list in the same edition' in claim['scope']
    assert 'filing or initiating a lawsuit' in claim['scope']
    assert 'Litigation / contest activity retains' in claim['scope']


def test_mcp_and_browser_expose_the_same_verified_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='court', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['manual_prerequisites'] is True
    for field in (
        'allowed_varas', 'avoid_tithi_numbers', 'allowed_nakshatras',
        'allowed_lagnas',
    ):
        assert profile['automated_constraints'][field] == \
            ACTIVITY_RULES['court'][field]

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['court']
    for field in (
        'label', 'source_claim', 'manual_prerequisites', 'allowed_varas',
        'avoid_tithi_numbers', 'allowed_nakshatras', 'allowed_lagnas',
        'manual_checks',
    ):
        assert exported[field] == ACTIVITY_RULES['court'][field]
