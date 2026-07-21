"""The activity source of truth and provenance ledger must not drift."""
import json
from pathlib import Path

from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from tools.check_activity_provenance import audit


ROOT = Path(__file__).resolve().parents[1]


def test_activity_source_claims_resolve_to_verified_muhurtam_claims():
    result = audit()
    assert result['errors'] == []
    assert result['activity_count'] == len(ACTIVITY_RULES)
    assert result['verified_profiles'] == {
        'property': 'muhurta.land_purchase.building',
        'bhumi_puja': 'muhurta.bhumi_puja.foundation',
        'well_digging': 'muhurta.well_digging',
    }


def test_generated_browser_contract_keeps_source_claims():
    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    for activity, rules in ACTIVITY_RULES.items():
        if activity not in browser['rules'] or 'source_claim' not in rules:
            continue
        assert browser['rules'][activity]['source_claim'] == rules['source_claim']
