"""Integrated, source-bounded Borrowing event checks."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from telugu_panchangam.personal.borrowing import (
    BORROWING_MODE_REGISTRY,
    BORROWING_PURPOSES,
    resolve_borrowing_mode,
)
from telugu_panchangam.personal.activity_check_contract import (
    build_activity_check_contract,
)
from telugu_panchangam.personal.election_chart import (
    evaluate_election_chart,
    evaluate_election_snapshots,
)
from telugu_panchangam.personal.election_chart_rules import (
    ELECTION_CHART_COMPLETE_ASSESSORS,
    ELECTION_CHART_MANUAL_REMAINDERS,
    ELECTION_CHART_RULES,
)
from telugu_panchangam.personal.personal_election import (
    evaluate_personal_election,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (ROOT / 'tests/fixtures/election_chart_same_rasi_conjunction_oracle.json')
    .read_text(encoding='utf-8')
)


def _chart(*, kuja_rashi='Mithuna', shani_rashi='Tula'):
    planets = deepcopy(ORACLE['base_planets'])
    for planet in planets:
        if planet['name'] == 'Kuja':
            planet['rashi'] = kuja_rashi
        if planet['name'] == 'Shani':
            planet['rashi'] = shani_rashi
    return {
        'instant': '2026-09-12T06:00:00+00:00',
        'lagna': {'rashi': 'Mesha', 'degree': 12.0},
        'planets': planets,
    }


def test_raman_event_registers_only_the_accepted_conjunction_predicate():
    rules = ELECTION_CHART_RULES['borrowing_money']
    assert [rule['id'] for rule in rules] == [
        'borrowing.same-rasi-chandra-kuja-shani'
    ]
    assert rules[0]['effect'] == 'reject'
    assert rules[0]['convention_id'] == 'same-rasi-distributive-conjunction-v1'
    assert rules[0]['decision_policy_claim'] == (
        'election_chart.borrowing_same_rasi_conjunction_reject_policy_v1'
    )
    assert ELECTION_CHART_MANUAL_REMAINDERS['borrowing_money'] == ()
    assert 'borrowing_money' in ELECTION_CHART_COMPLETE_ASSESSORS


def test_conjunction_rejects_and_missing_or_incomplete_coverage_never_passes():
    passed = evaluate_election_chart('borrowing_money', _chart())
    assert passed['rejected'] is False
    assert passed['needs_review'] is False

    failed = evaluate_election_chart(
        'borrowing_money', _chart(kuja_rashi='Vrishabha')
    )
    assert failed['rejected'] is True
    assert failed['outcomes'][0]['status'] == 'fail'

    incomplete = evaluate_election_snapshots(
        'borrowing_money', [_chart(), _chart()],
        borrowing_transition_coverage={
            'rasi_transitions_complete': False,
            'budget_exhausted': False,
        },
    )
    assert incomplete['outcomes'][0]['status'] == 'unknown'
    assert incomplete['needs_review'] is True

    exhausted = evaluate_election_snapshots(
        'borrowing_money', [_chart(), _chart()],
        borrowing_transition_coverage={
            'rasi_transitions_complete': True,
            'budget_exhausted': True,
        },
    )
    assert exhausted['outcomes'][0]['status'] == 'unknown'

    unsupported = evaluate_election_snapshots(
        'borrowing_money', [_chart(), _chart()],
        supported_system=False,
        borrowing_transition_coverage={
            'rasi_transitions_complete': True,
            'budget_exhausted': False,
        },
    )
    assert unsupported['outcomes'][0]['status'] == 'unknown'
    assert unsupported['rejected'] is False


def test_interior_conjunction_failure_dominates_unknown_or_pass():
    result = evaluate_election_snapshots(
        'borrowing_money',
        [_chart(), _chart(shani_rashi='Vrishabha'), _chart()],
        borrowing_transition_coverage={
            'rasi_transitions_complete': True,
            'budget_exhausted': False,
        },
    )
    assert result['rejected'] is True
    assert result['outcomes'][0]['status'] == 'fail'


def test_exactly_one_primary_borrower_owns_the_janma_star_gate():
    borrower = {
        'id': 'borrower-1',
        'name': 'Primary borrower',
        'nakshatra': 'Rohini',
        'janma_rashi': None,
        'janma_lagna': None,
    }
    rejected = evaluate_personal_election(
        'borrowing_money', borrower,
        {'nakshatra': 'Rohini', 'lunar_rashi': 'Vrishabha', 'lagna': 'Mesha'},
    )
    assert rejected['rejected'] is True
    assert rejected['outcomes'][0]['inputs']['primary_borrower_id'] == 'borrower-1'

    unresolved = evaluate_personal_election(
        'borrowing_money', None,
        {'nakshatra': 'Rohini', 'lunar_rashi': 'Vrishabha', 'lagna': 'Mesha'},
    )
    assert unresolved['needs_review'] is True
    assert unresolved['rejected'] is False


def test_purpose_and_mode_contracts_fail_closed_and_never_blend():
    assert BORROWING_PURPOSES == (
        'quick_domestic_or_personal', 'business', 'other_or_unknown'
    )
    default = resolve_borrowing_mode()
    assert default['lineage'] == 'raman'
    assert default['general_baseline']['coverage'] == 'incomplete_pending_284'
    assert default['general_baseline']['blocks_full_election_completion'] is True

    chintamani = resolve_borrowing_mode('chintamani-borrowing-v27-v1')
    drik = resolve_borrowing_mode('drik-loan-taking-2026-09-v1')
    assert chintamani['lineage'] != default['lineage'] != drik['lineage']
    assert chintamani['effects'] == 'not_selected_for_runtime'
    assert drik['effects'] == 'not_selected_for_runtime'
    assert chintamani['completion_contract'] == 'registered_incomplete_alternate'
    assert drik['completion_contract'] == 'registered_incomplete_alternate'
    assert default['completion_contract'] == {
        'attributable_event_predicates': 'implemented',
        'purpose_specific_qualitative_judgment': 'manual',
        'general_election_baseline': 'incomplete_pending_284',
    }
    assert BORROWING_MODE_REGISTRY['selection_contract'] == {
        'default': 'raman-borrowing-1993-v1',
        'alternate_modes_require_explicit_selection': True,
        'multiple_active_modes_allowed': False,
        'duplicate_scoring_allowed': False,
    }
    with pytest.raises(ValueError):
        resolve_borrowing_mode('blended')


def test_generated_contract_separates_purpose_guidance_and_safety():
    activity = build_activity_check_contract()['activities']['borrowing_money']
    assert activity['personal_rule_ids'] == [
        'personal.borrowing.primary-borrower-janma-nakshatra'
    ]
    assert activity['election_chart_rule_ids'] == [
        'borrowing.same-rasi-chandra-kuja-shani'
    ]
    purpose_rows = {
        row.get('purpose'): row['text']
        for row in activity['manual_checks']
        if row.get('purpose')
    }
    assert set(purpose_rows) == {
        'quick_domestic_or_personal', 'business', 'other_or_unknown'
    }
    safety = activity['manual_checks'][-1]
    assert safety['display_section'] == 'practical'
    assert 'Repayment capacity' in safety['text']
    assert all(rule['effect'] != 'qualify' for rule in ELECTION_CHART_RULES['borrowing_money'])
