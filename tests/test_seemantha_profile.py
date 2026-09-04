"""Seemantha rules must match the inspected Chapter VII passage."""
from datetime import date
import json
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.seemantha'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)


def test_seemantha_profile_matches_primary_source_gates():
    rules = ACTIVITY_RULES['seemantha']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['related_claims'] == [
        'muhurta.seemantha.chintamani_divergence']
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram', 'Shukravaram']
    assert rules['allowed_nakshatras'] == [
        'Rohini', 'Mrigashira', 'Punarvasu', 'Pushya',
        'Uttara Phalguni', 'Uttara Ashadha', 'Hasta', 'Shravana', 'Revati',
    ]
    assert rules['allowed_lagnas'] == [
        'Mesha', 'Vrishabha', 'Mithuna', 'Karka', 'Kanya', 'Tula',
        'Dhanu', 'Makara', 'Kumbha', 'Meena',
    ]
    assert len(rules['allowed_tithi_names']) == 18
    for name in rules['allowed_tithi_names']:
        assert not name.endswith(
            ('Chaturthi', 'Shashthi', 'Ashtami', 'Navami', 'Chaturdashi'))
        assert name not in {'Pournami', 'Amavasya'}


def test_seemantha_profile_does_not_invent_generic_samskara_gates():
    rules = ACTIVITY_RULES['seemantha']
    for field in (
        'skip_on_yoga', 'skip_on_sankramana', 'skip_on_khar_maasa',
        'skip_on_adhika', 'skip_on_pitru_paksha', 'skip_on_combust',
        'prefer_choghadiya', 'prefer_tithi_class', 'prefer_lagna_class',
    ):
        assert field not in rules
    assert any('first pregnancy' in check for check in rules['manual_checks'])
    assert any('Pournami' in check for check in rules['manual_checks'])
    assert any('medical care always take precedence' in check
               for check in rules['manual_checks'])


def test_seemantha_source_gates_and_positive_fixture():
    # Thursday, Shukla Trayodashi, Rohini: all automated source gates admit it.
    slots = day_slots(
        ENGINE.calculate(date(2026, 1, 1), HYDERABAD),
        activity='seemantha')
    assert slots
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['seemantha']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)

    # Sunday is rejected at day level before slot ranking.
    reason = diagnose_day(
        ENGINE.calculate(date(2026, 1, 4), HYDERABAD),
        activity='seemantha')
    assert reason == (
        'Adivaram · Seemantha (Prenatal ceremony) source profile '
        'does not admit this weekday')


def test_seemantha_claim_records_conservative_boundaries():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == [
        'BVR-MUHURTHA-1993',
        'BVR-MUHURTHA-CHISTABO-2020',
    ]
    assert "'Seemantha,' inspected in the 2020 Chistabo derivative" in claim['locator']
    assert 'internal printed pp. 21-22 (physical PDF pp. 24-25)' in claim['locator']
    assert 'conservatively omits Pournami' in claim['scope']
    assert 'combustion exception remain manual checks' in claim['scope']
    assert 'medical care always take precedence' in claim['scope']

    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    divergence = next(item for item in ledger['claims']
                      if item['id'] == rules_related_claim())
    assert divergence['verification_state'] == 'contradicted'
    assert divergence['source_ids'] == ['MC-HINDI-IA']
    assert "'Seemantonnayana Muhurta,' verse 8" in divergence['locator']
    assert "6th or 8th month rather than Raman's 5th or 7th" in divergence['scope']


def test_mcp_and_browser_expose_same_seemantha_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-17', days=1, activity='seemantha', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['related_claims'] == ACTIVITY_RULES['seemantha']['related_claims']
    assert profile['manual_prerequisites'] is True
    assert profile['manual_checks'] == ACTIVITY_RULES['seemantha']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'seemantha' in browser['groups'][1]['activities']
    exported = browser['rules']['seemantha']
    for field in (
        'source_claim', 'allowed_varas', 'allowed_nakshatras',
        'allowed_tithi_names', 'allowed_lagnas', 'manual_checks',
        'manual_prerequisites', 'related_claims',
    ):
        assert exported[field] == ACTIVITY_RULES['seemantha'][field]


def rules_related_claim():
    return ACTIVITY_RULES['seemantha']['related_claims'][0]
