"""Deferred Pretakriya must implement Muhurta Chintamani verse 48 exactly."""
import json
from datetime import date, timedelta
from pathlib import Path

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.models.panchangam_day import Location
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.pretakriya.deferred'
ENGINE = DrikGanitaEngine()
HYD = Location('Hyderabad', 17.385, 78.4867, 'Asia/Kolkata')
EXPECTED_STARS = {
    'Ashvini', 'Pushya', 'Hasta', 'Ashlesha', 'Moola',
    'Jyeshtha', 'Shravana', 'Ardra', 'Swati',
}
CANONICAL_STARS = (EXPECTED_STARS - {'Moola'}) | {'Mula'}


def _ledger():
    return json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))


def test_profile_is_narrowed_to_exact_deferred_rite_admission():
    rules = ACTIVITY_RULES['cremation']
    assert rules['label'] == 'Deferred funeral rites (Pretakriya)'
    assert rules['source_claim'] == CLAIM_ID
    assert set(rules['allowed_nakshatras']) == EXPECTED_STARS
    assert rules['manual_prerequisites'] is True
    assert 'skip_on_panchaka_nakshatra' not in rules
    assert 'Do not delay immediate Antyeshti' in rules['manual_checks'][0]


def test_claim_has_classical_verse_and_safety_scope():
    ledger = _ledger()
    source = next(item for item in ledger['sources'] if item['id'] == 'MC-HINDI-IA')
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert source['author'] == 'Rama Daivajna'
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Pretakriya ka muhurta,' verse 48" in claim['locator']
    assert 'nine-star positive admission list' in claim['scope']
    assert 'must never be used to delay Antyeshti' in claim['scope']


def test_every_returned_slot_uses_an_admitted_star():
    start = date(2026, 7, 1)
    found = 0
    for offset in range(45):
        day = ENGINE.calculate(start + timedelta(days=offset), HYD)
        for slot in day_slots(day, 'cremation', engine=ENGINE):
            facts = ENGINE.facts_at(slot['start'], HYD, vaaram=day.vaaram)
            assert facts.nakshatra in CANONICAL_STARS
            found += 1
    assert found


def test_mcp_keeps_expert_profile_while_browser_hides_it():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-07-01', days=14, activity='cremation', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['automated_constraints']['allowed_nakshatras'] == \
        ACTIVITY_RULES['cremation']['allowed_nakshatras']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'cremation' not in browser['rules']
    assert all('cremation' not in group['activities']
               for group in browser['groups'])
