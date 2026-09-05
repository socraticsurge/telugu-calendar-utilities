"""Home-repair commencement follows Raman without broadening conditionals."""
import json
from datetime import date
from pathlib import Path

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots, diagnose_day

ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.home_repair.commencement'
HYDERABAD = next(city for city in CITIES if city.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day(year: int, month: int, day: int):
    return ENGINE.calculate(date(year, month, day), HYDERABAD)


def test_home_repair_profile_preserves_source_semantics():
    rules = ACTIVITY_RULES['home_repair']
    assert rules['source_claim'] == CLAIM_ID
    assert rules['manual_prerequisites'] is True
    assert rules['allowed_varas'] == [
        'Adivaram', 'Somavaram', 'Budhavaram', 'Guruvaram',
        'Shukravaram', 'Shanivaram',
    ]
    assert rules['prefer_vara'] == [
        'Somavaram', 'Budhavaram', 'Guruvaram']
    # The seven stars are conditional on Mangala sharing the star, not an
    # unconditional Nakshatra ban.
    assert 'avoid_nakshatras' not in rules
    assert any('Mangala transit' in item for item in rules['manual_checks'])
    assert any('painting/whitewashing' in item for item in rules['manual_checks'])


def test_preferred_weekday_fixture_and_manual_tier_cap():
    slots = day_slots(_day(2026, 1, 5), activity='home_repair')
    assert slots
    assert all(slot['tier'] != 'Excellent' for slot in slots)
    assert all(slot['day_dosha'] == 'practitioner_review' for slot in slots)
    assert all(
        'Somavaram favoured for Home repair / renovation start (+1)'
        in slot['reason_groups']['activity_match'] for slot in slots)
    expected = {
        f'Manual check required · {item}'
        for item in ACTIVITY_RULES['home_repair']['manual_checks']
    }
    assert all(expected <= set(slot['reason_groups']['notes']) for slot in slots)


def test_tuesday_is_the_only_automated_weekday_prohibition():
    assert diagnose_day(_day(2026, 1, 6), 'home_repair') == (
        'Mangalavaram · Home repair / renovation start source profile '
        'does not admit this weekday')
    # Raman does not prohibit Saturday or Sunday in this repair paragraph.
    assert day_slots(_day(2026, 1, 3), 'home_repair')
    assert day_slots(_day(2026, 1, 4), 'home_repair')


def test_claim_mcp_and_browser_publish_the_same_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == [
        'BVR-MUHURTHA-1993',
        'BVR-MUHURTHA-CHISTABO-2020',
    ]
    assert "Chapter XII, 'Repairing Houses,' inspected" in claim['locator']
    assert 'internal printed pp. 54-55 (physical PDF pp. 58-59)' in claim['locator']

    result = json.loads(tool_find_muhurta(
        '2026-01-05', days=1, activity='home_repair', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['manual_prerequisites'] is True

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    assert 'home_repair' in browser['groups'][3]['activities']
    exported = browser['rules']['home_repair']
    for field in (
        'source_claim', 'allowed_varas', 'prefer_vara', 'manual_checks',
        'manual_prerequisites',
    ):
        assert exported[field] == ACTIVITY_RULES['home_repair'][field]
