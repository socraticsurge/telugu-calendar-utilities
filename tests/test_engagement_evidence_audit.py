"""Mutual engagement must follow Kanyavarana and Varavarana verses 10-11."""
import json
from datetime import date
from pathlib import Path

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.models.panchangam_day import Location
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.kanya_varavarana'
ENGINE = DrikGanitaEngine()
HYD = Location('Hyderabad', 17.385, 78.4867, 'Asia/Kolkata')
EXPECTED_STARS = {
    'Rohini', 'Krittika',
    'Purva Phalguni', 'Purva Ashadha', 'Purva Bhadrapada',
    'Uttara Phalguni', 'Uttara Ashadha', 'Uttara Bhadrapada',
}


def _claim():
    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    return next(claim for claim in ledger['claims'] if claim['id'] == CLAIM_ID)


def test_mutual_engagement_uses_exact_intersection():
    rules = ACTIVITY_RULES['engagement']
    assert rules['source_claim'] == CLAIM_ID
    assert set(rules['allowed_nakshatras']) == EXPECTED_STARS
    assert rules['manual_prerequisites'] is True
    assert 'prefer_tithi_class' not in rules
    assert 'prefer_vara' not in rules


def test_claim_has_direct_verse_locators_and_scope():
    claim = _claim()
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert "'Kanyavarana Muhurta' and 'Varavarana (Phaladana) Muhurta,' verses 10-11" in claim['locator']
    assert 'eight-star intersection is exact' in claim['scope']
    assert 'Shubha day, Tithi and Lagna' in claim['scope']


def test_slot_time_nakshatra_gate_is_enforced():
    for offset in range(45):
        d = date(2026, 7, 1).fromordinal(date(2026, 7, 1).toordinal() + offset)
        day = ENGINE.calculate(d, HYD)
        slots = day_slots(day, 'engagement', engine=ENGINE)
        for slot in slots:
            facts = ENGINE.facts_at(slot['start'], HYD, vaaram=day.vaaram)
            assert facts.nakshatra in EXPECTED_STARS


def test_mcp_and_browser_expose_verified_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-07-01', days=14, activity='engagement', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['automated_constraints']['allowed_nakshatras'] == \
        ACTIVITY_RULES['engagement']['allowed_nakshatras']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['engagement']
    assert exported['source_claim'] == CLAIM_ID
    assert set(exported['allowed_nakshatras']) == EXPECTED_STARS
