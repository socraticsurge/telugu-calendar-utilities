"""Versioned Borrowing context and non-blended source modes.

The default runtime profile is Raman.  The Chintamani and dated Drik entries
are explicit alternate lineages whose clauses are registered for comparison;
they are never inherited by the default profile without an explicit mode ID.
"""

from __future__ import annotations

from typing import Any

BORROWING_PURPOSES = (
    'quick_domestic_or_personal',
    'business',
    'other_or_unknown',
)

BORROWING_MODE_REGISTRY: dict[str, Any] = {
    'schema_version': 1,
    'default_mode_id': 'raman-borrowing-1993-v1',
    'selection_contract': {
        'default': 'raman-borrowing-1993-v1',
        'alternate_modes_require_explicit_selection': True,
        'multiple_active_modes_allowed': False,
        'duplicate_scoring_allowed': False,
    },
    'modes': {
        'raman-borrowing-1993-v1': {
            'lineage': 'raman',
            'status': 'active_default',
            'source_claim_ids': ['muhurta.borrowing_money'],
            'participant': 'exactly_one_primary_borrower',
            'purpose_enum': list(BORROWING_PURPOSES),
            'calendar_clauses': [
                'avoid Krittika, Moola, Punarvasu and Dhanishtha',
                "avoid the primary borrower's Janma Nakshatra",
                'inherit registered general Tithi, Vara, Nakshatra and Tarabala purity',
            ],
            'chart_clauses': [
                'reject same-Rasi Chandra-Kuja or Chandra-Shani conjunction',
                'manual: quick domestic/personal good aspect from Chandra to Lagna',
                'manual: business favorable Chandra relation to Budha and Lagna lord',
            ],
            'transition_inputs': ['Chandra Rasi', 'Kuja Rasi', 'Shani Rasi'],
            'effects': {'conjunction': 'reject', 'qualitative_purpose': 'manual'},
            'event_automation': 'complete_for_attributable_predicates',
            'formula_contract': {
                'universal_nakshatras': 'candidate Nakshatra not in the four-name prohibition set',
                'janma_nakshatra': 'candidate Nakshatra differs from the explicit primary borrower Janma Nakshatra',
                'conjunction': 'R(Chandra)=R(Kuja) OR R(Chandra)=R(Shani)',
                'purpose_specific': 'manual because neither qualitative phrase has an attributable formula',
            },
            'effect_contract': {
                'nakshatra': 'reject',
                'conjunction': 'reject',
                'qualitative_purpose': 'manual',
                'financial_safety': 'always_visible_non_scoring',
            },
            'completion_contract': {
                'attributable_event_predicates': 'implemented',
                'purpose_specific_qualitative_judgment': 'manual',
                'general_election_baseline': 'incomplete_pending_284',
            },
            'general_baseline': {
                'mode': 'source_inherited',
                'mode_id': 'raman-general-election-purity-v1',
                'coverage': 'incomplete_pending_284',
                'blocks_full_election_completion': True,
            },
        },
        'chintamani-borrowing-v27-v1': {
            'lineage': 'muhurta_chintamani',
            'status': 'registered_incomplete_alternate',
            'source_claim_ids': ['muhurta.borrowing.chintamani_lineage'],
            'participant': 'borrower_or_dravyaprayoga_actor_as_stated_by_commentary',
            'calendar_clauses': [
                'avoid Tuesday',
                'avoid Sankranti',
                'avoid Vriddhi Yoga',
                'avoid Hasta',
                'avoid Sunday',
                'use the twelve registered Nakshatras for Dravyaprayoga/debt-taking',
            ],
            'chart_clauses': [
                'require Chara Lagna',
                'place benefics in houses 5 and 9',
                'leave house 8 unoccupied',
            ],
            'separate_lending_clause': 'Wednesday is separately stated for lending',
            'transition_inputs': ['Lagna Rasi', 'graha houses 5, 8 and 9', 'graha nature'],
            'effects': 'not_selected_for_runtime',
            'event_automation': 'not_implemented',
            'formula_contract': 'source clauses registered; no runtime formula selected',
            'effect_contract': 'not_selected_for_runtime',
            'completion_contract': 'registered_incomplete_alternate',
            'blocks_raman_event_completion': False,
            'blocks_all_lineages_automated_claim': True,
        },
        'drik-loan-taking-2026-09-v1': {
            'lineage': 'current_published_practice',
            'status': 'registered_incomplete_alternate',
            'source_claim_ids': ['muhurta.borrowing.drik_published_practice_2026_09'],
            'participant': 'borrower',
            'calendar_clauses': [
                'avoid Tuesday',
                'avoid Sankranti',
                'avoid Vriddhi Yoga',
                'avoid Sunday plus Hasta Amrit Siddhi Yoga',
                'prefer Wednesday',
                'use published movable, sweet and named monetary Nakshatras',
            ],
            'chart_clauses': [
                'require movable Lagna',
                'prefer houses 5, 8 and 9 unoccupied',
            ],
            'transition_inputs': ['Nakshatra', 'Lagna Rasi', 'graha houses 5, 8 and 9'],
            'effects': 'not_selected_for_runtime',
            'event_automation': 'not_implemented',
            'formula_contract': 'dated published-practice clauses registered; no runtime formula selected',
            'effect_contract': 'not_selected_for_runtime',
            'completion_contract': 'registered_incomplete_alternate',
            'reviewed_on': '2026-09-12',
            'blocks_raman_event_completion': False,
            'blocks_all_lineages_automated_claim': True,
        },
    },
}


def resolve_borrowing_mode(mode_id: str | None = None) -> dict[str, Any]:
    """Resolve one mode; alternates are returned only by explicit ID."""
    selected = mode_id or BORROWING_MODE_REGISTRY['default_mode_id']
    modes = BORROWING_MODE_REGISTRY['modes']
    if selected not in modes:
        raise ValueError(f'Unknown Borrowing mode: {selected}')
    return modes[selected]
