#!/usr/bin/env python3
"""Build the comprehensive, provenance-resolved Muhurtam rule crosswalk.

The crosswalk is deliberately generated from the canonical Python activity,
personal, and election-chart rules plus the structured browser check contract.
Run without arguments to refresh the JSON artefact, or with ``--check`` to
fail when the committed artefact is stale or a prerequisite loses provenance.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / 'docs' / 'reference' / 'provenance.json'
OUTPUT = ROOT / 'docs' / 'reference' / 'muhurtam-rule-crosswalk.json'
SCHEMA_VERSION = 1

ACTIVITY_METADATA_FIELDS = frozenset({
    'label',
    'source_claim',
    'source_scope',
    'audit_claim',
    'heuristic_claim',
    'related_claims',
    'manual_checks',
    'manual_prerequisites',
})

PROJECT_PREDICATE_CLAIM = 'muhurta.shared.project_predicates'
SCORING_POLICY_CLAIM = 'muhurta.scoring_policy'

# A profile's primary claim is activity-level context, not blanket authority
# for every configured field. These sets are intentionally exhaustive and
# fail closed below: a new (activity, field) pair must be classified before the
# generated crosswalk can change.
PRIMARY_ACTIVITY_CLAIM_FIELDS: Mapping[str, frozenset[str]] = {
    'any': frozenset(),
    'wedding': frozenset({
        'allowed_maasams', 'allowed_maasa_solar_pairs', 'allowed_varas',
        'prefer_vara', 'allowed_tithi_names', 'allowed_nakshatras',
        'avoid_karana', 'avoid_nitya_yogas', 'allowed_lagnas',
        'prefer_lagnas',
    }),
    'engagement': frozenset({'allowed_nakshatras'}),
    'naming': frozenset({
        'allowed_varas', 'allowed_nakshatras', 'avoid_tithi_numbers',
        'prefer_lagna_class',
    }),
    'annaprasana': frozenset({
        'allowed_varas', 'allowed_nakshatras', 'avoid_tithi_numbers',
        'allowed_lagnas',
    }),
    'karnavedha': frozenset({
        'daytime_only', 'allowed_varas', 'avoid_tithi_numbers',
        'allowed_lagnas', 'require_single_daylight_tithi',
        'require_single_daylight_nakshatra',
    }),
    'mundana': frozenset({
        'forenoon_only', 'skip_on_combust', 'allowed_pakshams',
        'allowed_varas', 'allowed_tithi_numbers', 'allowed_nakshatras',
        'prefer_nakshatras', 'allowed_lagnas',
    }),
    'upanayana': frozenset({
        'forenoon_only', 'allowed_maasams', 'allowed_solar_signs',
        'allowed_varas', 'allowed_tithi_names', 'allowed_nakshatras',
        'allowed_lagnas',
    }),
    'vidyarambha': frozenset({
        'allowed_varas', 'allowed_nakshatras', 'allowed_lagnas',
    }),
    'seemantha': frozenset({
        'allowed_varas', 'allowed_nakshatras', 'allowed_tithi_names',
        'allowed_lagnas',
    }),
    'gruhapravesha': frozenset({
        'allowed_varas', 'allowed_solar_signs', 'allowed_tithi_names',
        'allowed_nakshatras', 'allowed_lagnas', 'prefer_lagna_class',
    }),
    'vehicle': frozenset({'prefer_nakshatras'}),
    'property': frozenset({
        'allowed_varas', 'allowed_nakshatras', 'avoid_tithi_numbers',
        'prefer_vara', 'prefer_lagna_class',
    }),
    'house_purchase': frozenset({
        'allowed_varas', 'allowed_tithi_numbers', 'allowed_nakshatras',
        'prefer_lagnas',
    }),
    'gold': frozenset(),
    'business_inventory_purchase': frozenset({
        'allowed_varas', 'prefer_vara', 'prefer_tithi_numbers',
        'prefer_nakshatras',
    }),
    'purchase': frozenset({'prefer_nakshatras'}),
    'borrowing_money': frozenset({
        'avoid_nakshatras', 'avoid_janma_nakshatra',
    }),
    'lending_money': frozenset({
        'allowed_varas', 'avoid_nakshatras', 'avoid_janma_nakshatra',
        'avoid_vara_tithi_names',
    }),
    'bhumi_puja': frozenset({
        'allowed_maasams', 'allowed_varas', 'avoid_vara_paksha',
        'allowed_solar_classes', 'allowed_nakshatras',
        'prefer_nakshatras', 'allowed_tithi_numbers', 'prefer_vara',
        'required_lagna_class',
    }),
    'well_digging': frozenset({
        'allowed_nakshatras', 'allowed_lagnas', 'caution_lagna_solar',
    }),
    'home_repair': frozenset({'allowed_varas', 'prefer_vara'}),
    'business': frozenset({'allowed_nakshatras', 'required_lagna_class'}),
    'job': frozenset({'allowed_varas', 'allowed_nakshatras'}),
    'yajna': frozenset({'require_homa_election'}),
    'pilgrimage': frozenset({
        'skip_on_combust', 'avoid_tithi_numbers', 'prefer_nakshatras',
    }),
    'ceremony': frozenset({
        'allowed_varas', 'avoid_tithi_numbers', 'allowed_nakshatras',
    }),
    'court': frozenset({
        'allowed_varas', 'avoid_tithi_numbers', 'allowed_nakshatras',
        'allowed_lagnas',
    }),
    'surgery': frozenset({
        'allowed_varas', 'allowed_tithi_names', 'allowed_nakshatras',
    }),
    'travel': frozenset({'avoid_nakshatras', 'prefer_nakshatras'}),
    'beginning': frozenset({
        'allowed_varas', 'allowed_nakshatras', 'allowed_lagnas',
    }),
    'cremation': frozenset({'allowed_nakshatras'}),
    'construction_roof': frozenset({'allowed_lagnas'}),
    'wood_cutting': frozenset({'allowed_tithi_names'}),
    'coronation': frozenset({
        'allowed_nakshatras', 'allowed_tithi_names', 'allowed_lagnas',
    }),
}

SHARED_SOURCE_CLAIM_FIELDS: Mapping[tuple[str, str], str] = {
    (activity, 'skip_on_sankramana'): 'panchangam.sankramana_avoidance'
    for activity in (
        'wedding', 'naming', 'annaprasana', 'karnavedha', 'mundana',
        'upanayana', 'vidyarambha', 'ceremony',
    )
}

PROJECT_HEURISTIC_FIELDS: Mapping[str, frozenset[str]] = {
    'any': frozenset(),
    'wedding': frozenset({
        'skip_on_yoga', 'skip_on_adhika', 'skip_on_pitru_paksha',
        'skip_on_simha_stha_guru', 'penalty_on_simha_stha_shukra',
        'skip_on_combust',
    }),
    'engagement': frozenset(),
    'naming': frozenset({
        'skip_on_yoga', 'skip_on_khar_maasa', 'skip_on_adhika',
        'skip_on_pitru_paksha', 'prefer_choghadiya',
        'prefer_tithi_class', 'avoid_tithi_class',
    }),
    'annaprasana': frozenset({
        'skip_on_yoga', 'skip_on_khar_maasa', 'skip_on_adhika',
        'skip_on_pitru_paksha', 'prefer_choghadiya',
        'prefer_tithi_class', 'avoid_tithi_class',
    }),
    'karnavedha': frozenset({
        'skip_on_yoga', 'skip_on_khar_maasa', 'skip_on_adhika',
        'skip_on_pitru_paksha', 'prefer_tithi_class',
        'avoid_tithi_class',
    }),
    'mundana': frozenset({
        'skip_on_yoga', 'skip_on_khar_maasa', 'skip_on_adhika',
        'skip_on_pitru_paksha', 'prefer_tithi_class',
        'avoid_tithi_class',
    }),
    'upanayana': frozenset({
        'skip_on_yoga', 'skip_on_khar_maasa', 'skip_on_adhika',
        'skip_on_pitru_paksha', 'prefer_tithi_class',
        'avoid_tithi_class',
    }),
    'vidyarambha': frozenset({
        'skip_on_yoga', 'skip_on_khar_maasa', 'skip_on_adhika',
        'skip_on_pitru_paksha', 'prefer_choghadiya',
        'prefer_tithi_class', 'avoid_tithi_class',
    }),
    'seemantha': frozenset(),
    'gruhapravesha': frozenset(),
    'vehicle': frozenset({
        'prefer_choghadiya', 'prefer_tithi_class', 'prefer_vara',
        'prefer_lagna_class',
    }),
    'property': frozenset(),
    'house_purchase': frozenset(),
    'gold': frozenset({
        'prefer_choghadiya', 'prefer_tithi_class', 'prefer_vara',
        'prefer_lagna_class',
    }),
    'business_inventory_purchase': frozenset(),
    'purchase': frozenset({'prefer_choghadiya'}),
    'borrowing_money': frozenset(),
    'lending_money': frozenset(),
    'bhumi_puja': frozenset({'skip_on_yoga'}),
    'well_digging': frozenset(),
    'home_repair': frozenset(),
    'business': frozenset(),
    'job': frozenset(),
    'yajna': frozenset(),
    'pilgrimage': frozenset({'avoid_karana', 'prefer_lagna_class'}),
    'ceremony': frozenset(),
    'court': frozenset(),
    'surgery': frozenset({'avoid_karana'}),
    'travel': frozenset({
        'avoid_karana', 'prefer_lagna_class', 'prefer_nakshatra_mukha',
    }),
    'beginning': frozenset(),
    'cremation': frozenset(),
    'construction_roof': frozenset({'skip_on_panchaka_nakshatra'}),
    'wood_cutting': frozenset({'skip_on_panchaka_nakshatra'}),
    'coronation': frozenset({'skip_on_yoga', 'prefer_nakshatra_mukha'}),
}

EXPERT_ACTIVITY_MANUAL_SECTIONS: Mapping[str, tuple[str, ...]] = {
    'beginning': ('information', 'chart', 'chart'),
    'cremation': ('information', 'practical', 'information'),
    'construction_roof': (),
    'wood_cutting': ('chart',),
    'coronation': ('chart', 'chart', 'chart'),
}

MANUAL_ROW_CLAIM_OVERRIDES: Mapping[str, str] = {
    'wedding.manual-6': 'muhurta.wedding.drkpanchang_divergence',
    'gruhapravesha.manual-6': (
        'muhurta.gruhapravesha.drkpanchang_divergence'),
    'lending_money.manual-5': 'muhurta.lending.drkpanchang_divergence',
}

MANUAL_RELATED_CONTEXT_CLAIMS: Mapping[str, tuple[str, ...]] = {
    'seemantha.manual-1': ('muhurta.seemantha.chintamani_divergence',),
}

MANUAL_SUPPORTING_CLAIMS: Mapping[str, tuple[str, ...]] = {
    'wedding.manual-5': ('muhurta.wedding',),
    'gruhapravesha.manual-5': ('muhurta.gruhapravesha',),
}

# These rows preserve source guidance for Python/MCP, non-Drik, and service-
# unavailable fallbacks. Their clauses are replaced by explicit automated
# election-chart predicates in the supported browser path.
ANNAPRASANA_AUTOMATED_FALLBACK_NOTE = (
    'Not displayed as a residual manual Annaprasana chart check after a '
    'successful exact-chart screen.'
)
AUTOMATED_CHART_FALLBACK_MANUAL_NOTES = {
    'gold.manual-1': (
        'Not displayed as a residual manual Gold check after a successful '
        'exact-chart screen.'
    ),
    'annaprasana.manual-2': ANNAPRASANA_AUTOMATED_FALLBACK_NOTE,
    'annaprasana.manual-3': ANNAPRASANA_AUTOMATED_FALLBACK_NOTE,
    'annaprasana.manual-4': ANNAPRASANA_AUTOMATED_FALLBACK_NOTE,
    'karnavedha.manual-2': (
        'Not displayed as a residual manual Karnavedha chart check after a '
        'successful exact-chart screen.'
    ),
    'vidyarambha.manual-3': (
        'Not displayed as a residual vacant-8th check after a successful '
        'exact Aksharabhyasa chart screen.'
    ),
    'vidyarambha.manual-4': (
        'Not displayed as a residual grouped-Graha check after a successful '
        'exact Aksharabhyasa chart screen.'
    ),
}
AUTOMATED_CHART_FALLBACK_MANUAL_IDS = frozenset(
    AUTOMATED_CHART_FALLBACK_MANUAL_NOTES
)

PRODUCT_POLICY_MANUAL_IDS = frozenset({
    'wedding.manual-5', 'engagement.manual-3', 'seemantha.manual-7',
    'gruhapravesha.manual-5', 'house_purchase.manual-4',
    'business_inventory_purchase.manual-5', 'borrowing_money.manual-5',
    'lending_money.manual-6', 'home_repair.manual-5',
    'business.manual-3', 'job.manual-4', 'yajna.manual-2',
    'court.manual-6', 'surgery.manual-1', 'purchase.manual-3',
    'cremation.manual-2',
})


def _field(
    predicate_class: str,
    ranking_effect: str,
    rationale: str,
    *,
    implementation_note: str | None = None,
    rule_id: str | None = None,
    implementation_owner: str | None = None,
    interpretation_policy_claim_id: str | None = None,
) -> dict[str, str]:
    result = {
        'predicate_class': predicate_class,
        'ranking_effect': ranking_effect,
        'automation_rationale': rationale,
    }
    if implementation_note:
        result['implementation_note'] = implementation_note
    if rule_id:
        result['rule_id'] = rule_id
    if implementation_owner:
        result['implementation_owner'] = implementation_owner
    if interpretation_policy_claim_id:
        result['interpretation_policy_claim_id'] = (
            interpretation_policy_claim_id)
    return result


# The values remain in ACTIVITY_RULES. This table classifies how each value is
# consumed so a new field cannot silently appear in the crosswalk as an
# apparently verified or automated prerequisite.
PANCHANGAM_FIELD_SEMANTICS: Mapping[str, dict[str, str]] = {
    'avoid_karana': _field(
        'panchangam.slot-exclusion', 'candidate_exclusion',
        'Configured Karana spans are removed deterministically.'),
    'prefer_lagna_class': _field(
        'panchangam.ranking-preference', 'score_bonus_plus_one',
        'The active Lagna class is known from the generated Lagna timeline.'),
    'prefer_choghadiya': _field(
        'panchangam.ranking-preference', 'configured_score_bonus',
        'The dominant Choghadiya block and configured bonus are exact.'),
    'skip_on_yoga': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'A configured special Yoga match rejects the day deterministically.'),
    'skip_on_sankramana': _field(
        'panchangam.window-exclusion', 'candidate_exclusion',
        'Known Sankramana avoidance is applied without chart judgement.',
        implementation_note=(
            'Python clips the configured avoidance window; the browser '
            'rejects a feed day carrying the Sankramana marker.')),
    'prefer_vara': _field(
        'panchangam.ranking-preference',
        'score_bonus_plus_one_for_day_and_matching_hora',
        'The sunrise weekday and Hora ruler are deterministic.'),
    'prefer_tithi_class': _field(
        'panchangam.ranking-preference', 'score_bonus_plus_one',
        'The active Tithi family is computed at the candidate instant.'),
    'avoid_tithi_class': _field(
        'panchangam.ranking-penalty', 'score_penalty_minus_one',
        'The active Tithi family is computed at the candidate instant.'),
    'required_lagna_class': _field(
        'panchangam.slot-admission', 'candidate_exclusion',
        'A candidate without the required Lagna class is rejected.'),
    'allowed_maasams': _field(
        'panchangam.day-admission', 'candidate_exclusion',
        'The normalized lunar month is tested against the configured list.'),
    'allowed_maasa_solar_pairs': _field(
        'panchangam.day-admission-exception', 'candidate_admission',
        'Configured lunar-month and Surya-Rasi pairs extend month admission.'),
    'allowed_varas': _field(
        'panchangam.day-admission', 'candidate_exclusion',
        'The sunrise weekday is tested against the configured list.'),
    'avoid_vara_paksha': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'Exact configured weekday and Paksha pairs reject the day.'),
    'allowed_solar_classes': _field(
        'panchangam.day-admission', 'candidate_exclusion',
        'Surya Rasi class is computed and tested against the configured list.'),
    'allowed_nakshatras': _field(
        'panchangam.slot-admission', 'candidate_exclusion',
        'The active Nakshatra is tested against the configured list.'),
    'avoid_nakshatras': _field(
        'panchangam.slot-exclusion', 'candidate_exclusion',
        'A configured active Nakshatra rejects the candidate.'),
    'prefer_nakshatras': _field(
        'panchangam.ranking-preference', 'score_bonus_plus_one',
        'A configured active Nakshatra receives a deterministic bonus.'),
    'allowed_tithi_numbers': _field(
        'panchangam.slot-admission', 'candidate_exclusion',
        'The active Tithi number is tested against the configured list.'),
    'prefer_tithi_numbers': _field(
        'panchangam.ranking-preference', 'score_bonus_plus_one',
        'A configured active Tithi number receives a deterministic bonus.'),
    'avoid_tithi_numbers': _field(
        'panchangam.slot-exclusion', 'candidate_exclusion',
        'A configured active Tithi number rejects the candidate.'),
    'avoid_janma_nakshatra': _field(
        'panchangam.personal-slot-exclusion', 'candidate_exclusion',
        'Supplied Janma Nakshatras are compared with the active Nakshatra.'),
    'avoid_vara_tithi_names': _field(
        'panchangam.slot-exclusion', 'candidate_exclusion',
        'Exact configured weekday and Paksha-qualified Tithi pairs reject.'),
    'avoid_nitya_yogas': _field(
        'panchangam.slot-exclusion', 'candidate_exclusion',
        'A configured active Nitya Yoga rejects the candidate.'),
    'allowed_lagnas': _field(
        'panchangam.slot-admission', 'candidate_exclusion',
        'The active Lagna is tested against the configured list.'),
    'prefer_lagnas': _field(
        'panchangam.ranking-preference', 'score_bonus_plus_one',
        'A configured active Lagna receives a deterministic bonus.'),
    'caution_lagna_solar': _field(
        'panchangam.disclosure', 'disclosure_only',
        'A known equality between active Lagna and Surya Rasi is disclosed.'),
    'daytime_only': _field(
        'panchangam.time-admission', 'candidate_exclusion',
        'Night candidates are not generated for this activity.'),
    'require_single_daylight_tithi': _field(
        'panchangam.daylight-single-limb', 'candidate_exclusion',
        'The exact Tithi transition span is evaluated once over the half-open '
        'interval [local sunrise, local sunset); missing or uncertain '
        'boundaries reject admission.',
        rule_id='karnavedha.daylight-tithi-single',
        implementation_owner=(
            'telugu_panchangam/personal/election_assessors/karnavedha.py'),
        interpretation_policy_claim_id=(
            'election_day.karnavedha_daylight_policy_v1'),
    ),
    'require_single_daylight_nakshatra': _field(
        'panchangam.daylight-single-limb', 'candidate_exclusion',
        'The exact Nakshatra transition span is evaluated once over the '
        'half-open interval [local sunrise, local sunset); missing or '
        'uncertain boundaries reject admission.',
        rule_id='karnavedha.daylight-nakshatra-single',
        implementation_owner=(
            'telugu_panchangam/personal/election_assessors/karnavedha.py'),
        interpretation_policy_claim_id=(
            'election_day.karnavedha_daylight_policy_v1'),
    ),
    'forenoon_only': _field(
        'panchangam.time-admission', 'candidate_exclusion',
        'Candidates ending after local solar noon are rejected.'),
    'allowed_pakshams': _field(
        'panchangam.day-admission', 'candidate_exclusion',
        'The active Paksha is tested against the configured list.'),
    'require_homa_election': _field(
        'panchangam.specialized-admission', 'candidate_exclusion',
        'The deterministic Homahuti and Agnivasa predicate must admit.'),
    'allowed_solar_signs': _field(
        'panchangam.day-admission', 'candidate_exclusion',
        'The Surya Rasi is tested against the configured list.'),
    'allowed_tithi_names': _field(
        'panchangam.slot-admission', 'candidate_exclusion',
        'The exact Paksha-qualified Tithi name must be admitted.'),
    'skip_on_combust': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'Configured Graha combustion facts reject candidates.'),
    'skip_on_adhika': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'An Adhika lunar month rejects the day in the Python finder.'),
    'skip_on_khar_maasa': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'A computed Khara Maasa rejects the day in the Python finder.'),
    'skip_on_pitru_paksha': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'A computed Pitru Paksha rejects the day in the Python finder.'),
    'skip_on_simha_stha_guru': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'Simha-Stha Guru rejects the day in the Python finder.'),
    'penalty_on_simha_stha_shukra': _field(
        'panchangam.ranking-penalty', 'configured_score_penalty',
        'The configured penalty is applied when Shukra is in Simha.'),
    'prefer_nakshatra_mukha': _field(
        'panchangam.ranking-preference', 'configured_score_bonus',
        'The configured Nakshatra-Mukha classes and bonus are exact.'),
    'skip_on_panchaka_nakshatra': _field(
        'panchangam.day-exclusion', 'candidate_exclusion',
        'The active Nakshatra is tested against the configured Panchaka '
        'membership table in the Python finder.'),
}


PERSONAL_PREDICATE_CONFIG: Mapping[str, dict[str, Any]] = {
    'personal.travel.lagna-exclusions': {
        'role': 'traveller',
        'participant_inputs': ['janma_lagna'],
        'candidate_inputs': ['lagna'],
        'operator': 'inclusive_rashi_distance_not_in',
        'excluded_positions': [1, 5, 7, 9],
    },
    'personal.travel.janma-rashi-lagna': {
        'role': 'traveller',
        'participant_inputs': ['janma_rashi'],
        'candidate_inputs': ['lagna'],
        'operator': 'equals',
    },
    'personal.gruhapravesha.natal-anchor-match': {
        'role': 'homeowner',
        'participant_inputs': [
            'nakshatra', 'janma_rashi', 'janma_lagna'],
        'candidate_inputs': [
            'nakshatra', 'lunar_rashi', 'lagna'],
        'operator': 'any_corresponding_pair_equals',
    },
    'personal.seemantha.birth-star-exclusions': {
        'role': 'mother',
        'participant_inputs': ['nakshatra'],
        'candidate_inputs': ['nakshatra'],
        'operator': 'inclusive_nakshatra_distance_not_in',
        'excluded_positions': [3, 7, 8, 10, 22],
    },
    'personal.surgery.chandra-outside-janma-rashi': {
        'role': 'patient',
        'participant_inputs': ['janma_rashi'],
        'candidate_inputs': ['lunar_rashi'],
        'operator': 'not_equals',
    },
}

SAMPLED_REJECT_AGGREGATION = (
    'fail if any sampled state fails; unknown if any sampled state is '
    'unresolved; otherwise pass')
SAMPLED_PREFERENCE_AGGREGATION = (
    'pass only if every sampled state passes; fail only if every sampled '
    'state fails; otherwise unknown')
SAMPLED_QUALIFICATION_AGGREGATION = (
    'fail if any sampled state fails; unknown if any sampled state is '
    'unresolved; otherwise pass')
SAMPLED_TRANSITION_SAFE_QUALIFICATION_AGGREGATION = (
    'fail if any sampled state fails; unknown if any sampled state is '
    'unresolved or a controlling between-sample transition cannot be '
    'excluded; otherwise pass')


def _load_provenance() -> dict[str, Any]:
    return json.loads(PROVENANCE.read_text(encoding='utf-8'))


def _claim_field(rules: Mapping[str, Any]) -> tuple[str, str]:
    candidates = [
        (field, rules[field])
        for field in ('source_claim', 'audit_claim', 'heuristic_claim')
        if rules.get(field)
    ]
    if len(candidates) != 1:
        raise ValueError(
            'Each browser activity must have exactly one authority claim')
    return candidates[0]


def _authority_status(claim: Mapping[str, Any]) -> str:
    state = claim.get('verification_state')
    if state == 'verified':
        return 'source_backed'
    if state == 'heuristic':
        return 'explicit_project_heuristic'
    if state == 'contradicted':
        return 'documented_conflict'
    return 'provenance_gap'


def _resolver(provenance: Mapping[str, Any]):
    sources = {item['id']: item for item in provenance.get('sources', ())}
    claims = {item['id']: item for item in provenance.get('claims', ())}

    def resolve(claim_id: str) -> dict[str, Any]:
        if claim_id not in claims:
            raise ValueError(f'Unknown provenance claim {claim_id!r}')
        claim = claims[claim_id]
        source_ids = claim.get('source_ids')
        if not isinstance(source_ids, list):
            raise TypeError(
                f'Provenance claim {claim_id!r} has no source_ids list')
        missing_sources = [item for item in source_ids if item not in sources]
        if missing_sources:
            raise ValueError(
                f'Provenance claim {claim_id!r} has unknown sources: '
                f'{missing_sources!r}')
        locator = claim.get('locator')
        if not isinstance(locator, str) or not locator.strip():
            raise ValueError(
                f'Provenance claim {claim_id!r} has no exact locator')
        return {
            'id': claim_id,
            'surface': claim.get('surface'),
            'authority_status': _authority_status(claim),
            'evidence_class': claim.get('evidence_class'),
            'verification_state': claim.get('verification_state'),
            'source_ids': list(source_ids),
            'sources': [
                {
                    'id': sources[source_id]['id'],
                    'title': sources[source_id].get('title'),
                    'authority_type': sources[source_id].get(
                        'authority_type'),
                    'url': sources[source_id].get('url'),
                }
                for source_id in source_ids
            ],
            'locator': locator,
            'scope': claim.get('scope'),
        }

    return resolve


def _manual_effect(
    row: Mapping[str, Any],
    *,
    profile_requires_review: bool,
) -> str:
    if profile_requires_review or row['display_section'] == 'chart':
        return 'practitioner_review_tier_cap'
    return 'disclosure_only'


def _manual_rationale(row: Mapping[str, Any]) -> str:
    if row['display_section'] == 'practical':
        return (
            'Safety, legal, medical, financial, or real-world judgement '
            'cannot be reduced to a timing predicate.')
    if row['display_section'] == 'information':
        return (
            'This source-scope or lineage statement is displayed rather '
            'than converted into an unsupported machine predicate.')
    return (
        'This source-authored chart row contains qualitative or uncomputed '
        'judgement; separately automated clauses have their own rule rows.')


def _json_value(value: Any) -> Any:
    """Normalize tuples and other JSON-compatible containers to JSON types."""
    return json.loads(json.dumps(value, ensure_ascii=False))


def _row_claim(claim: Mapping[str, Any]) -> dict[str, Any]:
    """Keep every row self-contained without repeating long source metadata."""
    return {
        key: deepcopy(claim[key])
        for key in (
            'id', 'surface', 'authority_status', 'evidence_class',
            'verification_state', 'source_ids', 'locator',
        )
    }


def _row(
    *,
    activity: str,
    rule_id: str,
    predicate_class: str,
    configured_inputs: Mapping[str, Any],
    source_claim_id: str,
    source_claim: Mapping[str, Any],
    implementation_status: str,
    implementation_owner: str,
    ranking_effect: str,
    automation_mode: str,
    automation_rationale: str,
    implementation_note: str | None = None,
    predicate_source_locator: str | None = None,
    decision_policy_claim: Mapping[str, Any] | None = None,
    interpretation_policy_claim: Mapping[str, Any] | None = None,
    related_context_claims: tuple[Mapping[str, Any], ...] = (),
    supporting_claims: tuple[Mapping[str, Any], ...] = (),
    authority_role: str | None = None,
    applicability: str | None = None,
) -> dict[str, Any]:
    result = {
        'activity': activity,
        'rule_id': rule_id,
        'predicate_class': predicate_class,
        'configured_inputs': _json_value(dict(configured_inputs)),
        'source_claim_id': source_claim_id,
        'source_claim': _row_claim(source_claim),
        'implementation_status': implementation_status,
        'implementation_owner': implementation_owner,
        'ranking_effect': ranking_effect,
        'automation_mode': automation_mode,
        'automation_rationale': automation_rationale,
    }
    if implementation_note:
        result['implementation_note'] = implementation_note
    if predicate_source_locator:
        result['predicate_source_locator'] = predicate_source_locator
    if decision_policy_claim:
        result['decision_policy_claim_id'] = decision_policy_claim['id']
        result['decision_policy_claim'] = _row_claim(
            decision_policy_claim)
    if interpretation_policy_claim:
        result['interpretation_policy_claim_id'] = (
            interpretation_policy_claim['id'])
        result['interpretation_policy_claim'] = _row_claim(
            interpretation_policy_claim)
    if related_context_claims:
        result['related_context_claims'] = [
            _row_claim(item) for item in related_context_claims
        ]
    if supporting_claims:
        result['supporting_claims'] = [
            _row_claim(item) for item in supporting_claims
        ]
    if authority_role:
        result['authority_role'] = authority_role
    if applicability:
        result['applicability'] = applicability
    return result


def _uses_project_decision_policy(ranking_effect: str) -> bool:
    return any(token in ranking_effect for token in (
        'score_bonus', 'score_penalty', 'tie_break', 'tier_cap'))


def _expert_manual_checks(
    activity: str,
    rules: Mapping[str, Any],
) -> list[dict[str, Any]]:
    texts = tuple(rules.get('manual_checks', ()))
    sections = EXPERT_ACTIVITY_MANUAL_SECTIONS.get(activity)
    if sections is None or len(sections) != len(texts):
        raise ValueError(
            f'{activity}: expert manual-check classification is stale')
    return [
        {
            'id': f'{activity}.manual-{index}',
            'source_index': index - 1,
            'source_text': text,
            'text': text,
            'class': 'manual-only',
            'display_section': section,
        }
        for index, (text, section) in enumerate(
            zip(texts, sections, strict=True), start=1)
    ]


def build_crosswalk(
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the validated JSON-ready comprehensive crosswalk."""
    sys.path.insert(0, str(ROOT))
    from telugu_panchangam.personal.activity_catalog import (
        BROWSER_ACTIVITIES,
    )
    from telugu_panchangam.personal.activity_check_contract import (
        DETERMINISTIC_PANCHANGAM_FIELDS,
        build_activity_check_contract,
    )
    from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
    from telugu_panchangam.personal.election_chart_rules import (
        ELECTION_CHART_HOUSE_SYSTEM,
        ELECTION_CHART_NODE_CONVENTION,
        ELECTION_CHART_PLANETS,
        ELECTION_CHART_RULES,
    )
    from telugu_panchangam.personal.personal_election import (
        PERSONAL_ELECTION_RULES,
    )

    ledger = deepcopy(dict(provenance or _load_provenance()))
    resolve = _resolver(ledger)
    project_predicate_claim = resolve(PROJECT_PREDICATE_CLAIM)
    scoring_policy_claim = resolve(SCORING_POLICY_CLAIM)
    product_policy_claim = resolve(
        'muhurta.product_safety_and_routing_policy')
    contract = build_activity_check_contract()['activities']
    expert_activities = tuple(
        activity for activity in ACTIVITY_RULES
        if activity not in set(BROWSER_ACTIVITIES)
    )
    all_activities = BROWSER_ACTIVITIES + expert_activities
    if set(expert_activities) != set(EXPERT_ACTIVITY_MANUAL_SECTIONS):
        raise ValueError('Expert activity manual-check map is stale')
    browser_field_set = set(DETERMINISTIC_PANCHANGAM_FIELDS)
    canonical_field_set = set().union(*(
        set(ACTIVITY_RULES[activity]) - ACTIVITY_METADATA_FIELDS
        for activity in all_activities
    ))
    semantic_field_set = set(PANCHANGAM_FIELD_SEMANTICS)
    if canonical_field_set != semantic_field_set:
        missing = sorted(canonical_field_set - semantic_field_set)
        stale = sorted(semantic_field_set - canonical_field_set)
        raise ValueError(
            'Panchangam field classification is stale: '
            f'missing={missing!r}; unused={stale!r}')

    if set(PRIMARY_ACTIVITY_CLAIM_FIELDS) != set(all_activities):
        raise ValueError('Primary activity field-authority map is stale')
    if set(PROJECT_HEURISTIC_FIELDS) != set(all_activities):
        raise ValueError('Project heuristic field-authority map is stale')
    classified_pairs: set[tuple[str, str]] = set()
    actual_pairs: set[tuple[str, str]] = set()
    for activity in all_activities:
        actual_fields = (
            set(ACTIVITY_RULES[activity]) - ACTIVITY_METADATA_FIELDS)
        actual_pairs.update((activity, field) for field in actual_fields)
        primary = set(PRIMARY_ACTIVITY_CLAIM_FIELDS[activity])
        heuristic = set(PROJECT_HEURISTIC_FIELDS[activity])
        shared = {
            field for mapped_activity, field in SHARED_SOURCE_CLAIM_FIELDS
            if mapped_activity == activity
        }
        overlaps = (
            (primary & heuristic) | (primary & shared) | (heuristic & shared))
        if overlaps:
            raise ValueError(
                f'{activity}: duplicate field-authority classifications: '
                f'{sorted(overlaps)!r}')
        classified_pairs.update(
            (activity, field) for field in primary | heuristic | shared)
    if classified_pairs != actual_pairs:
        missing = sorted(actual_pairs - classified_pairs)
        stale = sorted(classified_pairs - actual_pairs)
        raise ValueError(
            'Panchangam field-authority map is stale: '
            f'missing={missing!r}; unused={stale!r}')

    canonical_personal_ids = {
        item[0]
        for rules in PERSONAL_ELECTION_RULES.values()
        for item in rules
    }
    if canonical_personal_ids != set(PERSONAL_PREDICATE_CONFIG):
        raise ValueError('Personal predicate configuration is stale')

    rows: list[dict[str, Any]] = []
    activities: list[dict[str, Any]] = []
    seen_rule_ids: set[str] = set()
    expected_manual_ids: set[str] = set()

    def append(row: dict[str, Any]) -> None:
        rule_id = row['rule_id']
        if rule_id in seen_rule_ids:
            raise ValueError(f'Duplicate crosswalk rule ID {rule_id!r}')
        seen_rule_ids.add(rule_id)
        rows.append(row)

    for activity in BROWSER_ACTIVITIES:
        activity_rules = ACTIVITY_RULES[activity]
        claim_field, claim_id = _claim_field(activity_rules)
        claim = resolve(claim_id)
        related_claims = [
            resolve(item)
            for item in activity_rules.get('related_claims', ())
        ]
        activity_row_ids: list[str] = []

        for field, semantics in PANCHANGAM_FIELD_SEMANTICS.items():
            if field not in activity_rules:
                continue
            rule_id = semantics.get(
                'rule_id', f'{activity}.panchangam.{field}')
            status = (
                'automated_browser_and_python'
                if field in browser_field_set
                else 'automated_python_only_not_browser'
            )
            if field in PRIMARY_ACTIVITY_CLAIM_FIELDS[activity]:
                field_claim_id = claim_id
                field_claim = claim
                authority_role = 'activity_source_claim'
            elif (activity, field) in SHARED_SOURCE_CLAIM_FIELDS:
                field_claim_id = SHARED_SOURCE_CLAIM_FIELDS[(activity, field)]
                field_claim = resolve(field_claim_id)
                authority_role = 'shared_source_claim'
            else:
                field_claim_id = PROJECT_PREDICATE_CLAIM
                field_claim = project_predicate_claim
                authority_role = 'explicit_project_heuristic'
            append(_row(
                activity=activity,
                rule_id=rule_id,
                predicate_class=semantics['predicate_class'],
                configured_inputs={
                    'activity_rule_field': field,
                    'configured_value': activity_rules[field],
                    'authority_role': authority_role,
                },
                source_claim_id=field_claim_id,
                source_claim=field_claim,
                implementation_status=status,
                implementation_owner=semantics.get(
                    'implementation_owner',
                    'telugu_panchangam/personal/activity_rules.py'),
                ranking_effect=semantics['ranking_effect'],
                automation_mode='automated',
                automation_rationale=semantics['automation_rationale'],
                implementation_note=semantics.get('implementation_note'),
                decision_policy_claim=(
                    scoring_policy_claim
                    if _uses_project_decision_policy(semantics['ranking_effect'])
                    else None
                ),
                interpretation_policy_claim=(
                    resolve(semantics['interpretation_policy_claim_id'])
                    if semantics.get('interpretation_policy_claim_id')
                    else None
                ),
            ))
            activity_row_ids.append(rule_id)

        for item in PERSONAL_ELECTION_RULES.get(activity, ()):
            rule_id, effect, personal_claim_id, predicate_locator = item
            if not predicate_locator:
                raise ValueError(
                    f'Personal rule {rule_id!r} has no predicate locator')
            personal_claim = resolve(personal_claim_id)
            config = deepcopy(PERSONAL_PREDICATE_CONFIG[rule_id])
            config['sample_aggregation'] = (
                SAMPLED_REJECT_AGGREGATION
                if effect == 'reject'
                else SAMPLED_PREFERENCE_AGGREGATION
            )
            append(_row(
                activity=activity,
                rule_id=rule_id,
                predicate_class='personal.exact-election-fact',
                configured_inputs=config,
                source_claim_id=personal_claim_id,
                source_claim=personal_claim,
                implementation_status=(
                    'automated_exact_chart_browser_with_python_parity'),
                implementation_owner=(
                    'telugu_panchangam/personal/personal_election.py'),
                ranking_effect=(
                    'candidate_exclusion'
                    if effect == 'reject'
                    else 'post_screen_tie_break_preference'),
                automation_mode='automated',
                automation_rationale=(
                    'The named natal and exact candidate facts support a '
                    'bounded equality or cyclic-position predicate.'),
                predicate_source_locator=predicate_locator,
                decision_policy_claim=(
                    scoring_policy_claim
                    if effect != 'reject'
                    else None
                ),
            ))
            activity_row_ids.append(rule_id)

        for rule in ELECTION_CHART_RULES.get(activity, ()):
            rule_id = rule['id']
            predicate_locator = rule.get('source_locator')
            if not predicate_locator:
                raise ValueError(
                    f'Election-chart rule {rule_id!r} has no locator')
            chart_claim_id = rule['source_claim']
            chart_claim = resolve(chart_claim_id)
            method_claims = tuple(
                resolve(claim_id)
                for claim_id in rule.get('method_claims', ())
            )
            source_backed_methods = tuple(
                claim for claim in method_claims
                if claim['authority_status'] == 'source_backed'
            )
            decision_policy = (
                resolve(rule['decision_policy_claim'])
                if rule.get('decision_policy_claim')
                else scoring_policy_claim
                if rule['effect'] == 'prefer'
                else None
            )
            predicate_inputs = {
                key: value
                for key, value in rule.items()
                if key not in {
                    'id', 'label', 'kind', 'effect', 'source_claim',
                    'source_locator',
                }
            }
            append(_row(
                activity=activity,
                rule_id=rule_id,
                predicate_class=f'election-chart.{rule["kind"]}',
                configured_inputs={
                    'house_system': ELECTION_CHART_HOUSE_SYSTEM,
                    'node_convention': ELECTION_CHART_NODE_CONVENTION,
                    'planet_set': list(ELECTION_CHART_PLANETS),
                    'predicate': rule['kind'],
                    'predicate_inputs': predicate_inputs,
                    'sample_aggregation': (
                        SAMPLED_REJECT_AGGREGATION
                        if rule['effect'] == 'reject'
                        else SAMPLED_TRANSITION_SAFE_QUALIFICATION_AGGREGATION
                        if (
                            rule['effect'] == 'qualify'
                            and 'election_chart.gold_transition_envelope_v1'
                            in rule.get('method_claims', ())
                        )
                        else SAMPLED_QUALIFICATION_AGGREGATION
                        if rule['effect'] == 'qualify'
                        else SAMPLED_PREFERENCE_AGGREGATION
                    ),
                },
                source_claim_id=chart_claim_id,
                source_claim=chart_claim,
                implementation_status=(
                    'automated_exact_chart_browser_with_python_parity'),
                implementation_owner=(
                    'telugu_panchangam/personal/'
                    'election_chart_rules.py'),
                ranking_effect=(
                    'candidate_exclusion'
                    if rule['effect'] == 'reject'
                    else 'post_screen_tier_cap'
                    if rule['effect'] == 'qualify'
                    else 'post_screen_tie_break_preference'),
                automation_mode='automated',
                automation_rationale=(
                    'The named, versioned interpretation convention is a '
                    'bounded predicate over the exact nine-Graha election '
                    'chart.'
                    if rule.get('convention_id')
                    else 'Whole Sign house occupancy is a bounded predicate '
                    'over the exact nine-Graha election chart.'
                ),
                predicate_source_locator=predicate_locator,
                decision_policy_claim=decision_policy,
                supporting_claims=source_backed_methods,
            ))
            activity_row_ids.append(rule_id)

        manual_checks = contract[activity]['manual_checks']
        expected_manual_ids.update(item['id'] for item in manual_checks)
        for manual in manual_checks:
            rule_id = manual['id']
            fallback_only = rule_id in AUTOMATED_CHART_FALLBACK_MANUAL_IDS
            if rule_id in PRODUCT_POLICY_MANUAL_IDS:
                manual_claim_id = (
                    'muhurta.product_safety_and_routing_policy')
                manual_claim = product_policy_claim
                manual_authority_role = 'product_policy'
            elif rule_id in MANUAL_ROW_CLAIM_OVERRIDES:
                manual_claim_id = MANUAL_ROW_CLAIM_OVERRIDES[rule_id]
                manual_claim = resolve(manual_claim_id)
                manual_authority_role = 'related_context'
            else:
                manual_claim_id = claim_id
                manual_claim = claim
                manual_authority_role = 'activity_source_claim'
            configured_manual = {
                key: value
                for key, value in manual.items()
                if key != 'id'
            }
            manual_effect = _manual_effect(
                manual,
                profile_requires_review=bool(
                    activity_rules.get('manual_prerequisites')),
            )
            append(_row(
                activity=activity,
                rule_id=rule_id,
                predicate_class='manual.display-row',
                configured_inputs=configured_manual,
                source_claim_id=manual_claim_id,
                source_claim=manual_claim,
                implementation_status='manual_displayed_not_computed',
                implementation_owner=(
                    'telugu_panchangam/personal/'
                    'activity_check_contract.py'),
                ranking_effect=(
                    f'fallback_only_{manual_effect}'
                    if fallback_only else manual_effect
                ),
                automation_mode='manual',
                automation_rationale=(
                    'Fallback source guidance only. In the supported Drik '
                    'browser path, separately provenance-linked automated '
                    'rules replace this broad clause.'
                    if fallback_only else _manual_rationale(manual)
                ),
                implementation_note=(
                    AUTOMATED_CHART_FALLBACK_MANUAL_NOTES.get(rule_id)
                ),
                applicability=(
                    'python_or_mcp_or_non_drik_or_exact_chart_unavailable'
                    if fallback_only else None
                ),
                decision_policy_claim=(
                    scoring_policy_claim
                    if _uses_project_decision_policy(manual_effect)
                    else None
                ),
                related_context_claims=tuple(
                    resolve(item)
                    for item in MANUAL_RELATED_CONTEXT_CLAIMS.get(
                        rule_id, ())
                ),
                supporting_claims=tuple(
                    resolve(item)
                    for item in MANUAL_SUPPORTING_CLAIMS.get(rule_id, ())
                ),
                authority_role=manual_authority_role,
            ))
            activity_row_ids.append(rule_id)

        activities.append({
            'activity': activity,
            'label': activity_rules['label'],
            'authority_claim_field': claim_field,
            'source_claim_id': claim_id,
            'source_claim': claim,
            'related_claims': related_claims,
            'source_scope': activity_rules.get('source_scope'),
            'manual_prerequisites': bool(
                activity_rules.get('manual_prerequisites')),
            'surface_availability': 'browser_and_python',
            'row_ids': activity_row_ids,
            'row_count': len(activity_row_ids),
        })

    expert_rows: list[dict[str, Any]] = []
    expert_activity_rows: list[dict[str, Any]] = []
    expected_expert_ids: set[str] = set()
    for activity in expert_activities:
        activity_rules = ACTIVITY_RULES[activity]
        claim_field, claim_id = _claim_field(activity_rules)
        claim = resolve(claim_id)
        related_claims = [
            resolve(item)
            for item in activity_rules.get('related_claims', ())
        ]
        activity_row_ids: list[str] = []

        for field, semantics in PANCHANGAM_FIELD_SEMANTICS.items():
            if field not in activity_rules:
                continue
            rule_id = f'{activity}.panchangam.{field}'
            if field in PRIMARY_ACTIVITY_CLAIM_FIELDS[activity]:
                field_claim_id = claim_id
                field_claim = claim
                authority_role = 'activity_source_claim'
            elif (activity, field) in SHARED_SOURCE_CLAIM_FIELDS:
                field_claim_id = SHARED_SOURCE_CLAIM_FIELDS[(activity, field)]
                field_claim = resolve(field_claim_id)
                authority_role = 'shared_source_claim'
            else:
                field_claim_id = PROJECT_PREDICATE_CLAIM
                field_claim = project_predicate_claim
                authority_role = 'explicit_project_heuristic'
            expert_rows.append(_row(
                activity=activity,
                rule_id=rule_id,
                predicate_class=semantics['predicate_class'],
                configured_inputs={
                    'activity_rule_field': field,
                    'configured_value': activity_rules[field],
                    'authority_role': authority_role,
                },
                source_claim_id=field_claim_id,
                source_claim=field_claim,
                implementation_status='automated_python_only_not_browser',
                implementation_owner=(
                    'telugu_panchangam/personal/activity_rules.py'),
                ranking_effect=semantics['ranking_effect'],
                automation_mode='automated',
                automation_rationale=semantics['automation_rationale'],
                implementation_note=semantics.get('implementation_note'),
                decision_policy_claim=(
                    scoring_policy_claim
                    if _uses_project_decision_policy(
                        semantics['ranking_effect'])
                    else None
                ),
            ))
            activity_row_ids.append(rule_id)
            expected_expert_ids.add(rule_id)

        if PERSONAL_ELECTION_RULES.get(activity) or ELECTION_CHART_RULES.get(
            activity
        ):
            raise ValueError(
                f'{activity}: expert exact-chart rules require exporter '
                'classification')

        for manual in _expert_manual_checks(activity, activity_rules):
            rule_id = manual['id']
            if rule_id in PRODUCT_POLICY_MANUAL_IDS:
                manual_claim_id = (
                    'muhurta.product_safety_and_routing_policy')
                manual_claim = product_policy_claim
                manual_authority_role = 'product_policy'
            else:
                manual_claim_id = claim_id
                manual_claim = claim
                manual_authority_role = 'activity_source_claim'
            expert_rows.append(_row(
                activity=activity,
                rule_id=rule_id,
                predicate_class='manual.display-row',
                configured_inputs={
                    key: value
                    for key, value in manual.items()
                    if key != 'id'
                },
                source_claim_id=manual_claim_id,
                source_claim=manual_claim,
                implementation_status='manual_python_mcp_not_computed',
                implementation_owner=(
                    'telugu_panchangam/personal/activity_rules.py'),
                ranking_effect=_manual_effect(
                    manual,
                    profile_requires_review=bool(
                        activity_rules.get('manual_prerequisites')),
                ),
                automation_mode='manual',
                automation_rationale=_manual_rationale(manual),
                decision_policy_claim=(
                    scoring_policy_claim
                    if _uses_project_decision_policy(_manual_effect(
                        manual,
                        profile_requires_review=bool(
                            activity_rules.get('manual_prerequisites')),
                    ))
                    else None
                ),
                authority_role=manual_authority_role,
            ))
            activity_row_ids.append(rule_id)
            expected_expert_ids.add(rule_id)

        expert_activity_rows.append({
            'activity': activity,
            'label': activity_rules['label'],
            'authority_claim_field': claim_field,
            'source_claim_id': claim_id,
            'source_claim': claim,
            'related_claims': related_claims,
            'manual_prerequisites': bool(
                activity_rules.get('manual_prerequisites')),
            'surface_availability': 'python_and_mcp_only',
            'row_ids': activity_row_ids,
            'row_count': len(activity_row_ids),
        })

    expert_ids = [row['rule_id'] for row in expert_rows]
    if len(expert_ids) != len(set(expert_ids)):
        raise ValueError('Expert crosswalk rule IDs are not unique')
    if set(expert_ids) != expected_expert_ids:
        raise ValueError('Expert crosswalk coverage is incomplete')
    if set(expert_ids) & seen_rule_ids:
        raise ValueError('Browser and expert crosswalk rule IDs overlap')

    counts_by_class: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    counts_by_authority_status: dict[str, int] = {}
    deterministic_by_authority_role: dict[str, int] = {}
    for row in rows:
        counts_by_class[row['predicate_class']] = (
            counts_by_class.get(row['predicate_class'], 0) + 1)
        status = row['implementation_status']
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
        authority_status = row['source_claim']['authority_status']
        counts_by_authority_status[authority_status] = (
            counts_by_authority_status.get(authority_status, 0) + 1)
        if row['predicate_class'].startswith('panchangam.'):
            role = row['configured_inputs']['authority_role']
            deterministic_by_authority_role[role] = (
                deterministic_by_authority_role.get(role, 0) + 1)

    result = {
        'schema_version': SCHEMA_VERSION,
        'generated_from': [
            'telugu_panchangam.personal.activity_rules.ACTIVITY_RULES',
            'telugu_panchangam.personal.activity_check_contract',
            (
                'telugu_panchangam.personal.personal_election.'
                'PERSONAL_ELECTION_RULES'
            ),
            (
                'telugu_panchangam.personal.election_chart_rules.'
                'ELECTION_CHART_RULES'
            ),
            'docs/reference/provenance.json',
        ],
        'counts': {
            'activities': len(activities),
            'browser_activities': len(BROWSER_ACTIVITIES),
            'python_mcp_only_activities': len(expert_activities),
            'rows': len(rows),
            'deterministic_panchangam_rows': sum(
                row['predicate_class'].startswith('panchangam.')
                for row in rows),
            'personal_rule_rows': sum(
                row['predicate_class'].startswith('personal.')
                for row in rows),
            'election_chart_rule_rows': sum(
                row['predicate_class'].startswith('election-chart.')
                for row in rows),
            'manual_display_rows': sum(
                row['predicate_class'] == 'manual.display-row'
                for row in rows),
            'by_predicate_class': counts_by_class,
            'by_implementation_status': counts_by_status,
            'by_authority_status': counts_by_authority_status,
            'deterministic_by_authority_role': (
                deterministic_by_authority_role),
        },
        'activities': activities,
        'rows': rows,
        'expert_scope': {
            'description': (
                'Canonical Python/MCP activity profiles that are not '
                'currently offered by the browser selector.'),
            'counts': {
                'activities': len(expert_activity_rows),
                'rows': len(expert_rows),
                'deterministic_panchangam_rows': sum(
                    row['predicate_class'].startswith('panchangam.')
                    for row in expert_rows),
                'manual_display_rows': sum(
                    row['predicate_class'] == 'manual.display-row'
                    for row in expert_rows),
            },
            'activities': expert_activity_rows,
            'rows': expert_rows,
        },
    }
    _validate_complete(
        result, BROWSER_ACTIVITIES, expected_manual_ids)
    return result


def _validate_complete(
    result: Mapping[str, Any],
    crosswalk_activities: tuple[str, ...],
    expected_manual_ids: set[str],
) -> None:
    activities = result['activities']
    rows = result['rows']
    if tuple(item['activity'] for item in activities) != crosswalk_activities:
        raise ValueError('Crosswalk activities do not match canonical scope')
    ids = [row['rule_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Crosswalk rule IDs are not unique')
    indexed_ids = {
        rule_id
        for activity in activities
        for rule_id in activity['row_ids']
    }
    if indexed_ids != set(ids):
        raise ValueError('Activity row indexes do not cover every rule')
    for row in rows:
        required = {
            'activity', 'rule_id', 'predicate_class', 'configured_inputs',
            'source_claim_id', 'source_claim', 'implementation_status',
            'ranking_effect', 'automation_mode', 'automation_rationale',
        }
        missing = required - set(row)
        if missing:
            raise ValueError(
                f'{row.get("rule_id", "unknown")}: missing {sorted(missing)}')
        claim = row['source_claim']
        if claim['id'] != row['source_claim_id']:
            raise ValueError(f'{row["rule_id"]}: source claim did not resolve')
        if not claim['locator']:
            raise ValueError(f'{row["rule_id"]}: source locator is missing')
        if claim['authority_status'] == 'provenance_gap':
            raise ValueError(
                f'{row["rule_id"]}: unresolved provenance authority')
        authority_role = (
            row.get('authority_role')
            or row['configured_inputs'].get('authority_role')
        )
        if (
            claim['authority_status'] == 'documented_conflict'
            and authority_role != 'related_context'
        ):
            raise ValueError(
                f'{row["rule_id"]}: conflict cannot authorize a predicate')
        policy = row.get('decision_policy_claim')
        if policy:
            if policy['id'] != row['decision_policy_claim_id']:
                raise ValueError(
                    f'{row["rule_id"]}: decision policy did not resolve')
            if policy['authority_status'] != 'explicit_project_heuristic':
                raise ValueError(
                    f'{row["rule_id"]}: decision policy is not heuristic')
        interpretation_policy = row.get('interpretation_policy_claim')
        if interpretation_policy:
            if (
                interpretation_policy['id']
                != row['interpretation_policy_claim_id']
            ):
                raise ValueError(
                    f'{row["rule_id"]}: interpretation policy did not '
                    'resolve')
            if (
                interpretation_policy['authority_status']
                != 'explicit_project_heuristic'
            ):
                raise ValueError(
                    f'{row["rule_id"]}: interpretation policy is not '
                    'heuristic')
        for related in row.get('related_context_claims', ()):
            if related['authority_status'] != 'documented_conflict':
                raise ValueError(
                    f'{row["rule_id"]}: related context is not a conflict')
        for supporting in row.get('supporting_claims', ()):
            if supporting['authority_status'] != 'source_backed':
                raise ValueError(
                    f'{row["rule_id"]}: supporting facet is not source-backed')
        if row['automation_mode'] not in {'automated', 'manual'}:
            raise ValueError(f'{row["rule_id"]}: invalid automation mode')

    actual_manual_ids = {
        row['rule_id']
        for row in rows
        if row['predicate_class'] == 'manual.display-row'
    }
    if actual_manual_ids != expected_manual_ids:
        raise ValueError('Manual display-row coverage is incomplete')


def rendered(provenance: Mapping[str, Any] | None = None) -> str:
    return json.dumps(
        build_crosswalk(provenance),
        indent=2,
        ensure_ascii=False,
    ) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        expected = rendered()
    except (KeyError, TypeError, ValueError) as exc:
        print(f'Muhurtam crosswalk validation failed: {exc}', file=sys.stderr)
        return 1

    if args.check:
        actual = OUTPUT.read_text(encoding='utf-8') if OUTPUT.exists() else ''
        if actual != expected:
            print(
                f'{OUTPUT.relative_to(ROOT)} is stale; run '
                '`python3 tools/export_muhurtam_rule_crosswalk.py`.',
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
