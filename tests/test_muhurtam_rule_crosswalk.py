"""Coverage, provenance, and freshness tests for the Muhurtam crosswalk."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES
from telugu_panchangam.personal.activity_check_contract import (
    DETERMINISTIC_PANCHANGAM_FIELDS,
    build_activity_check_contract,
)
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_RULES,
)
from telugu_panchangam.personal.personal_election import (
    PERSONAL_ELECTION_RULES,
)
from tools.export_muhurtam_rule_crosswalk import (
    ACTIVITY_METADATA_FIELDS,
    build_crosswalk,
)

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / 'docs/reference/muhurtam-rule-crosswalk.json'
PROVENANCE = ROOT / 'docs/reference/provenance.json'


def _rows_by_class(crosswalk, prefix):
    return [
        row for row in crosswalk['rows']
        if row['predicate_class'].startswith(prefix)
    ]


def test_crosswalk_covers_every_browser_prerequisite_exactly():
    crosswalk = build_crosswalk()
    assert [
        activity['activity'] for activity in crosswalk['activities']
    ] == list(BROWSER_ACTIVITIES)

    deterministic = _rows_by_class(crosswalk, 'panchangam.')
    expected_deterministic = {
        (activity, field)
        for activity in BROWSER_ACTIVITIES
        for field in set(ACTIVITY_RULES[activity]) - ACTIVITY_METADATA_FIELDS
    }
    actual_deterministic = {
        (
            row['activity'],
            row['configured_inputs']['activity_rule_field'],
        )
        for row in deterministic
    }
    assert actual_deterministic == expected_deterministic
    for row in deterministic:
        field = row['configured_inputs']['activity_rule_field']
        assert row['configured_inputs']['configured_value'] == (
            json.loads(json.dumps(ACTIVITY_RULES[row['activity']][field])))

    personal_ids = {
        item[0]
        for rules in PERSONAL_ELECTION_RULES.values()
        for item in rules
    }
    assert {
        row['rule_id']
        for row in _rows_by_class(crosswalk, 'personal.')
    } == personal_ids

    election_ids = {
        rule['id']
        for rules in ELECTION_CHART_RULES.values()
        for rule in rules
    }
    assert {
        row['rule_id']
        for row in _rows_by_class(crosswalk, 'election-chart.')
    } == election_ids

    contract = build_activity_check_contract()['activities']
    manual_ids = {
        row['id']
        for activity in BROWSER_ACTIVITIES
        for row in contract[activity]['manual_checks']
    }
    assert {
        row['rule_id']
        for row in crosswalk['rows']
        if row['predicate_class'] == 'manual.display-row'
    } == manual_ids


def test_crosswalk_counts_and_rule_ids_are_stable_and_unique():
    crosswalk = build_crosswalk()
    assert crosswalk['counts']['activities'] == 30
    assert crosswalk['counts']['rows'] == 328
    assert crosswalk['counts']['deterministic_panchangam_rows'] == 177
    assert crosswalk['counts']['personal_rule_rows'] == 5
    assert crosswalk['counts']['election_chart_rule_rows'] == 32
    assert crosswalk['counts']['manual_display_rows'] == 114
    ids = [row['rule_id'] for row in crosswalk['rows']]
    assert len(ids) == len(set(ids))
    assert set(ids) == {
        rule_id
        for activity in crosswalk['activities']
        for rule_id in activity['row_ids']
    }


def test_browser_and_python_only_implementation_status_is_honest():
    crosswalk = build_crosswalk()
    deterministic = _rows_by_class(crosswalk, 'panchangam.')
    browser_fields = set(DETERMINISTIC_PANCHANGAM_FIELDS)
    for row in deterministic:
        field = row['configured_inputs']['activity_rule_field']
        expected = (
            'automated_browser_and_python'
            if field in browser_fields
            else 'automated_python_only_not_browser'
        )
        assert row['implementation_status'] == expected

    assert {
        row['configured_inputs']['activity_rule_field']
        for row in deterministic
        if row['implementation_status'] == (
            'automated_python_only_not_browser')
    } == {
        'penalty_on_simha_stha_shukra',
        'prefer_nakshatra_mukha',
        'skip_on_adhika',
        'skip_on_khar_maasa',
        'skip_on_pitru_paksha',
        'skip_on_simha_stha_guru',
    }


def test_every_row_contains_resolved_authority_and_automation_boundary():
    crosswalk = build_crosswalk()
    for row in crosswalk['rows']:
        assert row['activity'] in BROWSER_ACTIVITIES
        assert row['configured_inputs']
        assert row['source_claim_id'] == row['source_claim']['id']
        assert row['source_claim']['locator']
        assert row['source_claim']['authority_status'] != 'provenance_gap'
        assert row['source_claim']['evidence_class']
        assert row['source_claim']['verification_state']
        assert row['implementation_status']
        assert row['ranking_effect']
        assert row['automation_mode'] in {'automated', 'manual'}
        assert row['automation_rationale']

    any_activity = next(
        item for item in crosswalk['activities']
        if item['activity'] == 'any'
    )
    assert any_activity['row_count'] == 0
    assert any_activity['source_claim']['authority_status'] == (
        'explicit_project_heuristic')
    assert any_activity['source_claim']['verification_state'] == 'heuristic'
    assert any_activity['source_claim']['source_ids'] == []
    assert any_activity['source_claim']['locator']


def test_exact_personal_and_chart_predicate_values_are_exposed():
    rows = {row['rule_id']: row for row in build_crosswalk()['rows']}
    travel = rows['personal.travel.lagna-exclusions']
    assert travel['configured_inputs']['operator'] == (
        'inclusive_rashi_distance_not_in')
    assert travel['configured_inputs']['excluded_positions'] == [1, 5, 7, 9]
    assert travel['ranking_effect'] == 'candidate_exclusion'
    assert 'any sampled state fails' in (
        travel['configured_inputs']['sample_aggregation'])

    property_rule = rows['property.guru-kendra-trikona']
    assert property_rule['configured_inputs'] == {
        'house_system': 'whole_sign',
        'node_convention': 'mean',
        'planet_set': [
            'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru',
            'Shukra', 'Shani', 'Rahu', 'Ketu',
        ],
        'predicate': 'planet_in_houses',
        'predicate_inputs': {
            'planet': 'Guru',
            'houses': [1, 4, 5, 7, 9, 10],
        },
        'sample_aggregation': (
            'pass only if every sampled state passes; fail only if every '
            'sampled state fails; otherwise unknown'),
    }
    assert property_rule['ranking_effect'] == (
        'post_screen_tie_break_preference')
    assert property_rule['automation_rationale'] == (
        'Whole Sign house occupancy is a bounded predicate over the exact '
        'nine-Graha election chart.')

    gold_rule = rows['gold.surya-well-situated']
    assert gold_rule['automation_rationale'] == (
        'The named, versioned interpretation convention is a bounded '
        'predicate over the exact nine-Graha election chart.')
    assert 'between-sample transition' in (
        gold_rule['configured_inputs']['sample_aggregation'])

    non_gold_chart_rows = [
        row for row in rows.values()
        if row['predicate_class'].startswith('election-chart.')
        and row['activity'] != 'gold'
    ]
    assert len(non_gold_chart_rows) == 28
    assert all(
        'between-sample transition'
        not in row['configured_inputs']['sample_aggregation']
        for row in non_gold_chart_rows
    )

    karnavedha_tithi = rows['karnavedha.daylight-tithi-single']
    assert karnavedha_tithi['predicate_class'] == (
        'panchangam.daylight-single-limb')
    assert karnavedha_tithi['configured_inputs'] == {
        'activity_rule_field': 'require_single_daylight_tithi',
        'configured_value': 'raman-karnavedha-daylight-v1',
        'authority_role': 'activity_source_claim',
    }
    assert karnavedha_tithi['implementation_owner'].endswith(
        'election_assessors/karnavedha.py')
    assert karnavedha_tithi['interpretation_policy_claim_id'] == (
        'election_day.karnavedha_daylight_policy_v1')

    karnavedha = next(
        item for item in build_crosswalk()['activities']
        if item['activity'] == 'karnavedha'
    )
    assert karnavedha['source_scope'] == ACTIVITY_RULES['karnavedha'][
        'source_scope']


def test_manual_display_rows_preserve_exact_contract_values():
    crosswalk = build_crosswalk()
    rows = {row['rule_id']: row for row in crosswalk['rows']}
    contract = build_activity_check_contract()['activities']
    for activity in BROWSER_ACTIVITIES:
        for source in contract[activity]['manual_checks']:
            row = rows[source['id']]
            assert row['configured_inputs'] == {
                key: value for key, value in source.items() if key != 'id'
            }
            assert row['automation_mode'] == 'manual'
            assert row['implementation_status'] == (
                'manual_displayed_not_computed')


def test_gold_manual_clause_is_explicitly_fallback_only():
    rows = {
        row['rule_id']: row
        for row in build_crosswalk()['rows']
    }
    gold = rows['gold.manual-1']
    assert gold['applicability'] == (
        'python_or_mcp_or_non_drik_or_exact_chart_unavailable')
    assert gold['ranking_effect'] == (
        'fallback_only_practitioner_review_tier_cap')
    assert gold['implementation_note'] == (
        'Not displayed as a residual manual Gold check after a successful '
        'exact-chart screen.')


def test_annaprasana_chart_manual_rows_are_fallback_only():
    rows = {
        row['rule_id']: row
        for row in build_crosswalk()['rows']
    }
    for rule_id in (
        'annaprasana.manual-2',
        'annaprasana.manual-3',
        'annaprasana.manual-4',
    ):
        row = rows[rule_id]
        assert row['applicability'] == (
            'python_or_mcp_or_non_drik_or_exact_chart_unavailable')
        assert row['ranking_effect'] == (
            'fallback_only_practitioner_review_tier_cap')
        assert row['implementation_note'] == (
            'Not displayed as a residual manual Annaprasana chart check '
            'after a successful exact-chart screen.')


def test_karnavedha_chart_manual_row_is_fallback_only():
    rows = {
        row['rule_id']: row
        for row in build_crosswalk()['rows']
    }
    row = rows['karnavedha.manual-2']
    assert row['applicability'] == (
        'python_or_mcp_or_non_drik_or_exact_chart_unavailable')
    assert row['ranking_effect'] == (
        'fallback_only_practitioner_review_tier_cap')
    assert row['implementation_note'] == (
        'Not displayed as a residual manual Karnavedha chart check after a '
        'successful exact-chart screen.')


def test_missing_claim_locator_fails_instead_of_inventing_authority():
    provenance = json.loads(PROVENANCE.read_text(encoding='utf-8'))
    broken = deepcopy(provenance)
    claim = next(
        item for item in broken['claims']
        if item['id'] == 'muhurta.wedding'
    )
    claim['locator'] = None
    with pytest.raises(ValueError, match='has no exact locator'):
        build_crosswalk(broken)


def test_generated_crosswalk_is_fresh():
    assert json.loads(GENERATED.read_text(encoding='utf-8')) == (
        build_crosswalk())
