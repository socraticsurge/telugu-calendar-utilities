"""Court-specific predicates built from source-neutral chart primitives."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .chart_geometry import NAVAMSA_ROUNDING_GUARD_DEGREES, navamsa_rashi
from .contracts import PrimitiveOutcome
from .event_admission import PlanetPosition
from .graha_nature import evaluate_forbidden_malefic_house_set

COURT_MESHA_D1_D9_METADATA: dict[str, Any] = {
    'source_statement': {
        'claim_id': 'muhurta.court.filing_lawsuit',
        'text': (
            'The Lagna should be Mesha, or at least the Navamsa must be Mesha.'
        ),
        'locator': (
            "B. V. Raman, Chapter XVII, 'Miscellaneous elections,' section "
            + "'Filing law-suits,' inspected in the 2020 Chistabo derivative "
            + 'at internal printed p. 67 (physical PDF p. 71)'
        ),
    },
    'convention': {
        'id': 'court-canonical-local-d1-sidecar-d9-v1',
        'method_claim_ids': [
            'election_chart.whole_sign_house_policy_v1',
            'election_chart.navamsa.bphs_6_12',
        ],
        'formula': (
            'canonical local D1 Lagna Rasi = Mesha OR BPHS-modality '
            + 'Navamsa(sidecar Lagna Rasi, degree) = Mesha'
        ),
        'd1_authority': 'canonical local Drik/Lahiri Lagna Rasi',
        'd9_authority': (
            'sidecar Lagna degree only when its Rasi agrees with canonical '
            + 'local D1'
        ),
        'navamsa_boundary_guard_degrees': NAVAMSA_ROUNDING_GUARD_DEGREES,
        'unsupported_system': 'unknown',
    },
    'event_policy': {
        'id': 'court.mesha-lagna-or-navamsa',
        'activity': 'court',
        'effect': 'reject',
        'effect_claim_id': 'muhurta.court.effect_policy_v1',
        'status': 'specified_unwired',
        'delivery_issue': 395,
    },
    'conditional_admission': {
        'id': 'court.mesha-navamsa-unresolved',
        'status': 'specified_unwired',
        'delivery_issue': 285,
        'rule': (
            'Only a valid non-Mesha D1 candidate whose D9 alternative is not '
            + 'yet resolved may be provisionally retained.'
        ),
    },
}

COURT_SIXTH_HOUSE_NATURAL_MALEFIC_METADATA: dict[str, Any] = {
    'source_statement': {
        'claim_id': 'muhurta.court.filing_lawsuit',
        'text': 'Place no malefic in the 6th.',
        'locator': (
            "B. V. Raman, Chapter XVII, 'Miscellaneous elections,' section "
            + "'Filing law-suits,' inspected in the 2020 Chistabo derivative "
            + 'at internal printed p. 67 (physical PDF p. 71)'
        ),
    },
    'convention': {
        'classifier_id': 'phaladeepika-natural-graha-nature-whole-sign-v1',
        'house_occupation_id': 'whole-sign-physical-occupation-v1',
        'method_claim_ids': [
            'election_chart.natural_graha_nature.phaladeepika_2_27',
            'election_chart.budha_same_sign_association_policy_v1',
            'election_chart.raman_180_degree_paksha_policy_v1',
            'election_chart.lunar_phase_boundary_guard_policy_v1',
            'election_chart.whole_sign_house_policy_v1',
        ],
        'formula': 'no graha p has H(p) = 6 and natural_nature(p) = malefic',
        'house_system': 'whole_sign',
        'frame': 'validated_local_lagna',
    },
    'event_policy': {
        'id': 'court.house-6-without-natural-malefic',
        'activity': 'court',
        'effect': 'reject',
        'effect_claim_id': 'muhurta.court.effect_policy_v1',
        'status': 'specified_unwired',
        'delivery_issue': 397,
    },
}


def _exact_lagna(chart: Mapping[str, Any] | None) -> tuple[str, float] | None:
    if not isinstance(chart, Mapping):
        return None
    lagna = chart.get('lagna')
    if not isinstance(lagna, Mapping):
        return None
    rashi = lagna.get('rashi')
    degree = lagna.get('degree')
    if (
        rashi not in RASHI_NAMES
        or isinstance(degree, bool)
        or not isinstance(degree, (int, float))
        or not math.isfinite(degree)
        or not 0 <= degree < 30
    ):
        return None
    return rashi, float(degree)


def evaluate_court_mesha_d1_d9(
    chart: Mapping[str, Any] | None,
    *,
    authoritative_d1_rashi: str | None,
    lagna_authority_uncertain: bool = False,
    supported_system: bool = True,
) -> PrimitiveOutcome:
    """Require authoritative Mesha D1 or a guarded authoritative Mesha D9."""
    if (
        type(supported_system) is not bool
        or type(lagna_authority_uncertain) is not bool
    ):
        return PrimitiveOutcome(
            'unknown', ('The Court D1/D9 evaluator configuration is malformed.',)
        )
    if not supported_system:
        return PrimitiveOutcome(
            'unknown',
            (
                'The Court D1/D9 predicate is supported only on the '
                +
                'authoritative Drik chart path.',
            ),
        )
    if lagna_authority_uncertain:
        return PrimitiveOutcome(
            'unknown',
            (
                'The local Lagna authority is missing, conflicting, or inside '
                +
                'its transition guard.',
            ),
        )
    if authoritative_d1_rashi not in RASHI_NAMES:
        return PrimitiveOutcome(
            'unknown',
            ('The authoritative local Drik/Lahiri D1 Lagna Rasi is unavailable.',),
        )
    if authoritative_d1_rashi == 'Mesha':
        return PrimitiveOutcome(
            'pass',
            ('The authoritative local D1 Lagna is Mesha; D9 is not needed.',),
        )

    exact_lagna = _exact_lagna(chart)
    if exact_lagna is None:
        return PrimitiveOutcome(
            'unknown',
            ('Authoritative exact Lagna facts for the D9 alternative are unavailable.',),
        )
    sidecar_rashi, sidecar_degree = exact_lagna
    if sidecar_rashi != authoritative_d1_rashi:
        return PrimitiveOutcome(
            'unknown',
            (
                f'The sidecar Lagna Rasi {sidecar_rashi} disagrees with '
                + f'authoritative local D1 {authoritative_d1_rashi}, so its '
                +
                'degree cannot determine D9.',
            ),
        )

    d9_rashi = navamsa_rashi(
        PlanetPosition(
            name='Lagna',
            rashi=sidecar_rashi,
            degree=sidecar_degree,
            house=1,
            retrograde=False,
        )
    )
    if d9_rashi is None:
        return PrimitiveOutcome(
            'unknown',
            (
                'The exact Lagna degree is inside the 0.01-degree Navamsa '
                +
                'boundary guard.',
            ),
        )
    if d9_rashi == 'Mesha':
        return PrimitiveOutcome(
            'pass',
            (
                f'The authoritative local D1 Lagna is {authoritative_d1_rashi} '
                +
                'and its guarded BPHS-modality D9 is Mesha.',
            ),
        )
    return PrimitiveOutcome(
        'fail',
        (
            f'The authoritative local D1 Lagna is {authoritative_d1_rashi} and '
            +
            f'its guarded BPHS-modality D9 is {d9_rashi}; neither is Mesha.',
        ),
    )


def court_mesha_admission_kind(
    authoritative_d1_rashi: str | None,
    d9_outcome: PrimitiveOutcome | None = None,
) -> str:
    """Classify the future #285 admission state without wiring the finder."""
    if authoritative_d1_rashi not in RASHI_NAMES:
        return 'unavailable'
    if authoritative_d1_rashi == 'Mesha':
        return 'unconditional'
    if d9_outcome is None or d9_outcome.status == 'unknown':
        return 'provisional'
    if d9_outcome.status == 'pass':
        return 'admitted'
    if d9_outcome.status == 'fail':
        return 'rejected'
    return 'unavailable'


def _samples_are_well_formed(samples: object) -> bool:
    return isinstance(samples, Sequence) and all(
        isinstance(sample, PrimitiveOutcome)
        and sample.status in {'pass', 'fail', 'unknown'}
        and all(isinstance(item, str) for item in sample.evidence)
        for sample in samples
    )


def _first_sample_with_status(
    samples: Sequence[PrimitiveOutcome], status: str
) -> PrimitiveOutcome | None:
    return next((sample for sample in samples if sample.status == status), None)


def _human_join(items: Sequence[str]) -> str:
    if len(items) < 3:
        return ' and '.join(items)
    return f'{", ".join(items[:-1])}, and {items[-1]}'


def _aggregate_court_reject_window(
    samples: Sequence[PrimitiveOutcome],
    *,
    transition_coverage: Sequence[tuple[str, bool]],
    budget_exhausted: bool,
    success_evidence: str,
) -> PrimitiveOutcome:
    """Apply shared reject-first and completeness precedence."""
    if isinstance(samples, Sequence):
        failure = next(
            (
                sample
                for sample in samples
                if isinstance(sample, PrimitiveOutcome) and sample.status == 'fail'
            ),
            None,
        )
        if failure is not None:
            return failure
    if not _samples_are_well_formed(samples):
        return PrimitiveOutcome(
            'unknown', ('Represented chart states are malformed or incomplete.',)
        )
    unknown = _first_sample_with_status(samples, 'unknown')
    if unknown is not None:
        return unknown
    if not samples:
        return PrimitiveOutcome(
            'unknown', ('No represented chart states are available.',)
        )
    coverage_values = [complete for _, complete in transition_coverage]
    if any(
        type(value) is not bool
        for value in [*coverage_values, budget_exhausted]
    ):
        return PrimitiveOutcome(
            'unknown', ('Window transition metadata is malformed or incomplete.',)
        )
    if budget_exhausted:
        return PrimitiveOutcome(
            'unknown',
            (
                "The chart-request budget was exhausted before this window's "
                + 'coverage was complete.',
            ),
        )
    missing = [
        name for name, complete in transition_coverage if not complete
    ]
    if missing:
        return PrimitiveOutcome(
            'unknown',
            (
                f'All represented states pass, but {_human_join(missing)} '
                + 'transition coverage is incomplete.',
            ),
        )
    return PrimitiveOutcome('pass', (success_evidence,))


def aggregate_court_mesha_d1_d9_window(
    samples: Sequence[PrimitiveOutcome],
    *,
    local_lagna_transitions_complete: bool,
    lagna_navamsa_transitions_complete: bool,
    budget_exhausted: bool,
) -> PrimitiveOutcome:
    """Combine sampled reject outcomes without hiding an interior failure."""
    return _aggregate_court_reject_window(
        samples,
        transition_coverage=(
            ('local-Lagna', local_lagna_transitions_complete),
            ('Lagna-Navamsa', lagna_navamsa_transitions_complete),
        ),
        budget_exhausted=budget_exhausted,
        success_evidence=(
            'Every represented state resolves the Court Mesha D1-or-D9 '
            + 'condition as satisfied.'
        ),
    )


def evaluate_court_sixth_house_natural_malefic(
    chart: Mapping[str, Any],
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    """Apply the Court H6 exclusion through the shared nature classifier."""
    if type(house_frame_uncertain) is not bool:
        return PrimitiveOutcome(
            'unknown', ('The Court sixth-house evaluator configuration is malformed.',)
        )
    if house_frame_uncertain:
        return PrimitiveOutcome(
            'unknown',
            (
                'The validated local-Lagna house frame is unavailable or '
                + 'disagrees with sidecar facts.',
            ),
        )
    return evaluate_forbidden_malefic_house_set(chart, [6])


def court_sixth_house_candidate_disposition(outcome: PrimitiveOutcome) -> str:
    """Project the accepted reject policy without wiring candidate generation."""
    if not isinstance(outcome, PrimitiveOutcome):
        return 'review'
    if outcome.status == 'fail':
        return 'reject'
    if outcome.status == 'pass':
        return 'retain'
    return 'review'


def aggregate_court_sixth_house_natural_malefic_window(
    samples: Sequence[PrimitiveOutcome],
    *,
    local_lagna_transitions_complete: bool,
    graha_rasi_transitions_complete: bool,
    chandra_phase_transitions_complete: bool,
    budha_association_transitions_complete: bool,
    budget_exhausted: bool,
) -> PrimitiveOutcome:
    """Aggregate the Court reject predicate across represented chart states."""
    return _aggregate_court_reject_window(
        samples,
        transition_coverage=(
            ('local-Lagna', local_lagna_transitions_complete),
            ('graha-Rasi', graha_rasi_transitions_complete),
            ('Chandra-phase', chandra_phase_transitions_complete),
            ('Budha-association', budha_association_transitions_complete),
        ),
        budget_exhausted=budget_exhausted,
        success_evidence=(
            'Every represented state keeps Whole Sign house 6 free of '
            + 'resolved natural malefics.'
        ),
    )
