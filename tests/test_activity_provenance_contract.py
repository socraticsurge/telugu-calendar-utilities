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
        'seemantha': 'muhurta.seemantha',
        'vehicle': 'muhurta.vehicle.acquisition',
        'naming': 'muhurta.namakarana',
        'property': 'muhurta.land_purchase.building',
        'house_purchase': 'muhurta.house_purchase.completed',
        'bhumi_puja': 'muhurta.bhumi_puja.foundation',
        'home_repair': 'muhurta.home_repair.commencement',
        'construction_roof': 'muhurta.construction_roof',
        'coronation': 'muhurta.coronation',
        'wood_cutting': 'muhurta.wood_cutting',
        'surgery': 'muhurta.surgery',
        'gold': 'muhurta.gold_jewelry.purchase',
        'pilgrimage': 'muhurta.pilgrimage',
        'purchase': 'muhurta.purchase.general',
        'business_inventory_purchase': 'muhurta.trade_inventory.purchase',
        'borrowing_money': 'muhurta.borrowing_money',
        'lending_money': 'muhurta.lending_money',
        'gruhapravesha': 'muhurta.gruhapravesha',
        'wedding': 'muhurta.wedding',
        'travel': 'muhurta.travel',
        'well_digging': 'muhurta.well_digging',
        'court': 'muhurta.court.filing_lawsuit',
        'ceremony': 'muhurta.shantika_paushtika',
        'beginning': 'muhurta.dharma_kriya.commencement',
        'business': 'muhurta.capital_deployment',
        'job': 'muhurta.service_entry',
        'yajna': 'muhurta.homahuti',
    }
    assert result['known_conflicts'] == {
        'cremation': {
            'claim': 'muhurta.cremation.profile_conflict',
            'state': 'contradicted',
        },
        'engagement': {
            'claim': 'muhurta.engagement.profile_conflict',
            'state': 'contradicted',
        },
    }
    assert result['heuristic_profiles'] == {
        'any': {
            'claim': 'muhurta.any.shared_scoring',
            'state': 'heuristic',
        },
    }
    assert result['needs_rule_locators'] == []
    assert 'court' not in result['needs_rule_locators']
    assert 'cremation' not in result['needs_rule_locators']
    assert 'engagement' not in result['needs_rule_locators']
    assert 'gruhapravesha' not in result['needs_rule_locators']
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


def test_generated_browser_contract_keeps_heuristic_claims():
    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    for activity, rules in ACTIVITY_RULES.items():
        if activity not in browser['rules'] or 'heuristic_claim' not in rules:
            continue
        assert browser['rules'][activity]['heuristic_claim'] == rules['heuristic_claim']


def test_generated_browser_contract_keeps_related_claims():
    browser = json.loads(
        (ROOT / 'src/data/activity-rules.generated.json').read_text(encoding='utf-8'))
    for activity, rules in ACTIVITY_RULES.items():
        if activity not in browser['rules'] or 'related_claims' not in rules:
            continue
        assert browser['rules'][activity]['related_claims'] == rules['related_claims']
