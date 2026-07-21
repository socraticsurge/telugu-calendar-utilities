"""General purchase uses the exact buyer-side Kraya Nakshatras."""
import json
from datetime import date
from pathlib import Path

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.muhurta import day_slots


ROOT = Path(__file__).parents[1]
CLAIM_ID = 'muhurta.purchase.general'
PREFERRED = [
    'Revati', 'Shatabhisha', 'Ashwini', 'Swati', 'Shravana', 'Chitra',
]


def _city(name):
    return next(city for city in CITIES if city.name == name)


def test_purchase_profile_matches_verse_16_and_scopes_heuristics():
    rules = ACTIVITY_RULES['purchase']
    assert rules['source_claim'] == CLAIM_ID
    assert 'audit_claim' not in rules
    assert rules['prefer_nakshatras'] == PREFERRED
    assert rules['prefer_choghadiya'] == ('Labh', 1)
    assert len(rules['manual_checks']) == 3

    ledger = json.loads(
        (ROOT / 'docs/reference/provenance.json').read_text(encoding='utf-8'))
    claim = next(item for item in ledger['claims'] if item['id'] == CLAIM_ID)
    assert claim['verification_state'] == 'verified'
    assert claim['source_ids'] == ['MC-HINDI-IA']
    assert 'verse 16' in claim['locator']
    assert 'verse 17' in claim['locator']
    assert 'Labh-Choghadiya bonus is a separate project heuristic' in claim['scope']


@pytest.mark.parametrize(
    ('city_name', 'target', 'canonical_name'),
    [
        ('Hyderabad', date(2026, 6, 8), 'Shatabhisha'),
        ('Vijayawada', date(2026, 6, 12), 'Ashvini'),
        ('Hyderabad', date(2026, 6, 24), 'Chitra'),
    ],
)
def test_purchase_preference_fires_across_dates_and_cities(
        city_name, target, canonical_name):
    day = DrikGanitaEngine().calculate(target, _city(city_name))
    assert day.nakshatra.name == canonical_name
    slots = day_slots(day, activity='purchase')
    assert slots
    assert any(
        f'{canonical_name} specifically favoured for Purchase (general) (+1)'
        in reason
        for slot in slots
        for reason in slot['reasons']
    )


def test_mcp_and_browser_expose_purchase_source_profile():
    from telugu_panchangam.mcp.tools import tool_find_muhurta

    result = json.loads(tool_find_muhurta(
        '2026-06-08', days=1, activity='purchase', city='Hyderabad'))
    profile = result['activity_profile']
    assert profile['source_claim'] == CLAIM_ID
    assert profile['audit_claim'] is None
    assert profile['manual_checks'] == ACTIVITY_RULES['purchase']['manual_checks']

    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    exported = browser['rules']['purchase']
    assert exported['source_claim'] == CLAIM_ID
    assert exported['prefer_nakshatras'] == PREFERRED
    assert exported['manual_checks'] == ACTIVITY_RULES['purchase']['manual_checks']
