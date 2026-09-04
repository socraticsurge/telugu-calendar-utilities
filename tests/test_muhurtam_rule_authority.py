"""Criterion-level Muhurtam authority and expert-scope regression tests."""

import pytest

from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from tools.export_muhurtam_rule_crosswalk import build_crosswalk


def _all_rows(crosswalk):
    return crosswalk['rows'] + crosswalk['expert_scope']['rows']


def test_browser_field_authority_is_exhaustive_and_honest():
    crosswalk = build_crosswalk()
    assert crosswalk['counts']['deterministic_by_authority_role'] == {
        'activity_source_claim': 106,
        'explicit_project_heuristic': 61,
        'shared_source_claim': 8,
    }
    rows = {row['rule_id']: row for row in crosswalk['rows']}

    for rule_id in (
        'purchase.panchangam.prefer_choghadiya',
        'vehicle.panchangam.prefer_lagna_class',
        'gold.panchangam.prefer_vara',
        'travel.panchangam.prefer_nakshatra_mukha',
        'travel.panchangam.avoid_karana',
        'pilgrimage.panchangam.avoid_karana',
        'surgery.panchangam.avoid_karana',
    ):
        assert rows[rule_id]['source_claim_id'] == (
            'muhurta.shared.project_predicates')
        assert rows[rule_id]['configured_inputs']['authority_role'] == (
            'explicit_project_heuristic')

    assert rows['purchase.panchangam.prefer_nakshatras'][
        'source_claim_id'] == 'muhurta.purchase.general'
    assert rows['ceremony.panchangam.skip_on_sankramana'][
        'source_claim_id'] == 'panchangam.sankramana_avoidance'


def test_five_python_mcp_only_profiles_have_a_separate_complete_scope():
    crosswalk = build_crosswalk()
    expert = crosswalk['expert_scope']
    assert expert['counts'] == {
        'activities': 5,
        'rows': 23,
        'deterministic_panchangam_rows': 13,
        'manual_display_rows': 10,
    }
    assert [item['activity'] for item in expert['activities']] == [
        'beginning', 'cremation', 'construction_roof', 'wood_cutting',
        'coronation',
    ]
    actual_fields = {
        (row['activity'], row['configured_inputs']['activity_rule_field'])
        for row in expert['rows']
        if row['predicate_class'].startswith('panchangam.')
    }
    expected_fields = {
        (activity, field)
        for activity in ACTIVITY_RULES
        if activity not in BROWSER_ACTIVITIES
        for field in ACTIVITY_RULES[activity]
        if field not in {
            'label', 'source_claim', 'audit_claim', 'heuristic_claim',
            'related_claims', 'manual_checks', 'manual_prerequisites',
        }
    }
    assert actual_fields == expected_fields
    rows = {row['rule_id']: row for row in expert['rows']}
    assert rows[
        'construction_roof.panchangam.skip_on_panchaka_nakshatra'
    ]['source_claim_id'] == 'muhurta.shared.project_predicates'


def test_manual_safety_and_conflict_rows_do_not_inherit_primary_claims():
    rows = {row['rule_id']: row for row in _all_rows(build_crosswalk())}
    practical = [
        row for row in rows.values()
        if row['predicate_class'] == 'manual.display-row'
        and row['configured_inputs']['display_section'] == 'practical'
    ]
    assert len(practical) == 15
    assert all(
        row['source_claim_id'] == (
            'muhurta.product_safety_and_routing_policy')
        and row['authority_role'] == 'product_policy'
        for row in practical
    )
    assert rows['purchase.manual-3']['source_claim_id'] == (
        'muhurta.product_safety_and_routing_policy')
    assert rows['wedding.manual-6']['source_claim_id'] == (
        'muhurta.wedding.drkpanchang_divergence')
    assert rows['wedding.manual-6']['authority_role'] == 'related_context'
    assert rows['seemantha.manual-1']['related_context_claims'][0][
        'id'] == 'muhurta.seemantha.chintamani_divergence'
    assert rows['wedding.manual-5']['supporting_claims'][0]['id'] == (
        'muhurta.wedding')
    assert rows['gruhapravesha.manual-5']['supporting_claims'][0]['id'] == (
        'muhurta.gruhapravesha')


def test_numeric_and_tier_policy_is_separate_from_predicate_authority():
    rows = _all_rows(build_crosswalk())
    policy_effects = ('score_bonus', 'score_penalty', 'tie_break', 'tier_cap')
    for row in rows:
        expects_policy = any(
            token in row['ranking_effect'] for token in policy_effects)
        assert ('decision_policy_claim' in row) is expects_policy
        if expects_policy:
            expected_policy = (
                'election_chart.gold_qualification_policy_v1'
                if row['ranking_effect'] == 'post_screen_tier_cap'
                else 'muhurta.scoring_policy'
            )
            assert row['decision_policy_claim_id'] == expected_policy
            assert row['decision_policy_claim']['authority_status'] == (
                'explicit_project_heuristic')


def test_new_activity_field_cannot_inherit_authority_silently(monkeypatch):
    monkeypatch.setitem(
        ACTIVITY_RULES['purchase'], 'allowed_varas', ['Somavaram'])
    with pytest.raises(
        ValueError, match='field.*stale'
    ):
        build_crosswalk()
