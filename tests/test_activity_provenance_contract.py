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
        'annaprasana': 'muhurta.annaprasana',
        'karnavedha': 'muhurta.karnavedha',
        'mundana': 'muhurta.mundana',
        'vidyarambha': 'muhurta.vidyarambha',
        'upanayana': 'muhurta.upanayana',
        'vehicle': 'muhurta.vehicle.acquisition',
        'naming': 'muhurta.namakarana',
        'property': 'muhurta.land_purchase.building',
        'bhumi_puja': 'muhurta.bhumi_puja.foundation',
        'construction_roof': 'muhurta.construction_roof',
        'coronation': 'muhurta.coronation',
        'wood_cutting': 'muhurta.wood_cutting',
        'surgery': 'muhurta.surgery',
        'gold': 'muhurta.gold_jewelry.purchase',
        'pilgrimage': 'muhurta.pilgrimage',
        'travel': 'muhurta.travel',
        'well_digging': 'muhurta.well_digging',
    }
    assert result['known_conflicts'] == {
        'court': {
            'claim': 'muhurta.court.profile_conflict',
            'state': 'contradicted',
        },
        'cremation': {
            'claim': 'muhurta.cremation.profile_conflict',
            'state': 'contradicted',
        },
        'engagement': {
            'claim': 'muhurta.engagement.profile_conflict',
            'state': 'contradicted',
        },
        'gruhapravesha': {
            'claim': 'muhurta.gruhapravesha.profile_conflict',
            'state': 'contradicted',
        },
        'litigation': {
            'claim': 'muhurta.litigation.profile_conflict',
            'state': 'contradicted',
        },
        'wedding': {
            'claim': 'muhurta.wedding.profile_conflict',
            'state': 'contradicted',
        },
        'yajna': {
            'claim': 'muhurta.yajna.profile_conflict',
            'state': 'contradicted',
        },
    }
    assert 'court' not in result['needs_rule_locators']
    assert 'cremation' not in result['needs_rule_locators']
    assert 'engagement' not in result['needs_rule_locators']
    assert 'gruhapravesha' not in result['needs_rule_locators']
    assert 'litigation' not in result['needs_rule_locators']
    assert 'wedding' not in result['needs_rule_locators']
    assert 'yajna' not in result['needs_rule_locators']


def test_generated_browser_contract_keeps_source_claims():
    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    for activity, rules in ACTIVITY_RULES.items():
        if activity not in browser['rules'] or 'source_claim' not in rules:
            continue
        assert browser['rules'][activity]['source_claim'] == rules['source_claim']


def test_generated_browser_contract_keeps_audit_claims():
    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    for activity, rules in ACTIVITY_RULES.items():
        if activity not in browser['rules'] or 'audit_claim' not in rules:
            continue
        assert browser['rules'][activity]['audit_claim'] == rules['audit_claim']
