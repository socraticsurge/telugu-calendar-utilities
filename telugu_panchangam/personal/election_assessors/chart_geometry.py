"""Source-neutral chart geometry used by election assessors."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .contracts import COMPLETE_GRAHA_FACTS_UNAVAILABLE, PrimitiveOutcome
from .event_admission import PlanetPosition, planet_positions

COURT_GURU_TRIKONA_FACTS_UNAVAILABLE = (
    'Complete canonical nine-graha Whole Sign facts are unavailable.'
)
COURT_GURU_TRIKONA_METADATA: dict[str, Any] = {
    'source_statement': {
        'claim_id': 'muhurta.court.filing_lawsuit',
        'text': 'Strengthen Lagna with Guru in a Trikona.',
        'locator': (
            "B. V. Raman, Chapter XVII, 'Miscellaneous elections,' section "
            "'Filing law-suits,' inspected in the 2020 Chistabo derivative "
            'at internal printed p. 67 (physical PDF p. 71)'
        ),
    },
    'convention': {
        'id': 'whole-sign-physical-occupation-v1',
        'method_claim_id': 'election_chart.whole_sign_house_policy_v1',
        'formula': 'H(Guru) in {1, 5, 9}',
        'house_system': 'whole_sign',
        'frame': 'validated_local_lagna',
    },
    'event_policy': {
        'id': 'court.guru-trikona',
        'activity': 'court',
        'effect': 'prefer',
        'status': 'specified_unwired',
        'delivery_issue': 396,
    },
}

NAVAMSA_WIDTH_DEGREES = 30 / 9
NAVAMSA_ROUNDING_GUARD_DEGREES = 0.01
RASHI_ROUNDING_GUARD_DEGREES = 0.01
GOLD_MAX_SAMPLE_GAP_MINUTES = 10
GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY = 24.0
GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY = 48.0
CONTRACT_DEGREE_HALF_STEP = 0.005

FULL_ASPECT_OFFSETS: Mapping[str, frozenset[int]] = {
    'Surya': frozenset({6}),
    'Chandra': frozenset({6}),
    'Kuja': frozenset({3, 6, 7}),
    'Budha': frozenset({6}),
    'Guru': frozenset({4, 6, 8}),
    'Shukra': frozenset({6}),
    'Shani': frozenset({2, 6, 9}),
}


def _longitude(position: PlanetPosition) -> float:
    return RASHI_NAMES.index(position.rashi) * 30 + position.degree


def evaluate_court_guru_trikona(
    chart: Mapping[str, Any],
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    """Evaluate the unwired Court Guru-in-Trikona preference foundation."""
    if house_frame_uncertain:
        return PrimitiveOutcome(
            'unknown',
            (
                (
                    'The validated local-Lagna house frame is unavailable or '
                    'disagrees with sidecar facts.'
                ),
            ),
        )
    if not isinstance(chart, Mapping):
        return PrimitiveOutcome(
            'unknown', (COURT_GURU_TRIKONA_FACTS_UNAVAILABLE,)
        )
    positions = planet_positions(chart)
    if positions is None:
        return PrimitiveOutcome(
            'unknown', (COURT_GURU_TRIKONA_FACTS_UNAVAILABLE,)
        )

    guru_house = positions['Guru'].house
    if guru_house in {1, 5, 9}:
        return PrimitiveOutcome(
            'pass',
            (
                (
                    f'Guru occupies house {guru_house}, a Trikona from the '
                    'validated local Lagna.'
                ),
            ),
        )
    return PrimitiveOutcome(
        'fail',
        (
            (
                f'Guru occupies house {guru_house}; target Trikona houses: '
                '1, 5, 9.'
            ),
        ),
    )


def _court_sample_precedence(
    samples: Sequence[PrimitiveOutcome],
) -> PrimitiveOutcome | None:
    for sample in samples:
        if isinstance(sample, PrimitiveOutcome) and sample.status == 'fail':
            return sample
    if any(
        not isinstance(sample, PrimitiveOutcome)
        or sample.status not in {'pass', 'fail', 'unknown'}
        for sample in samples
    ):
        return PrimitiveOutcome(
            'unknown', ('Represented chart states are malformed or incomplete.',)
        )
    for sample in samples:
        if sample.status == 'unknown':
            return sample
    if not samples:
        return PrimitiveOutcome(
            'unknown', ('No represented chart states are available.',)
        )
    return None


def _court_transition_coverage_result(
    local_lagna_transitions_complete: bool,
    guru_rasi_transitions_complete: bool,
) -> PrimitiveOutcome | None:
    if local_lagna_transitions_complete and guru_rasi_transitions_complete:
        return None
    missing = []
    if not local_lagna_transitions_complete:
        missing.append('local-Lagna')
    if not guru_rasi_transitions_complete:
        missing.append('Guru-Rasi')
    return PrimitiveOutcome(
        'unknown',
        (
            (
                f'All represented states pass, but {" and ".join(missing)} '
                'transition coverage is incomplete.'
            ),
        ),
    )


def aggregate_court_guru_trikona_window(
    samples: Sequence[PrimitiveOutcome],
    *,
    local_lagna_transitions_complete: bool,
    guru_rasi_transitions_complete: bool,
    budget_exhausted: bool,
) -> PrimitiveOutcome:
    """Combine represented Court states with preference-only precedence."""
    if sample_result := _court_sample_precedence(samples):
        return sample_result
    coverage_values = (
        local_lagna_transitions_complete,
        guru_rasi_transitions_complete,
        budget_exhausted,
    )
    if any(type(value) is not bool for value in coverage_values):
        return PrimitiveOutcome(
            'unknown', ('Window transition metadata is malformed or incomplete.',)
        )
    if budget_exhausted:
        return PrimitiveOutcome(
            'unknown',
            (
                (
                    'The chart-request budget was exhausted before this '
                    "window's coverage was complete."
                ),
            ),
        )
    if coverage_result := _court_transition_coverage_result(
        local_lagna_transitions_complete, guru_rasi_transitions_complete
    ):
        return coverage_result
    return PrimitiveOutcome(
        'pass',
        (
            'Every represented state places Guru in Whole Sign house 1, 5 or 9.',
        ),
    )


def evaluate_all_planets_in_houses(
    rule: Mapping[str, Any],
    houses: Mapping[str, int] | None,
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    """Require every named graha to occupy one of the target houses."""
    if houses is None or house_frame_uncertain:
        return PrimitiveOutcome(
            'unknown', ('Complete Whole Sign house facts are unavailable.',)
        )
    planets = rule.get('planets')
    target_houses = rule.get('houses')
    if (
        not isinstance(planets, list)
        or not planets
        or any(not isinstance(planet, str) or not planet for planet in planets)
        or len(set(planets)) != len(planets)
        or not isinstance(target_houses, list)
        or not target_houses
        or any(
            type(house) is not int or not 1 <= house <= 12
            for house in target_houses
        )
        or any(planet not in houses for planet in planets)
    ):
        return PrimitiveOutcome(
            'unknown', ('The grouped-graha rule configuration is incomplete.',)
        )
    passed = all(houses[planet] in target_houses for planet in planets)
    target_text = ', '.join(str(house) for house in target_houses)
    observed = '; '.join(
        f'{planet} house {houses[planet]}' for planet in planets
    )
    return PrimitiveOutcome(
        'pass' if passed else 'fail',
        (f'{observed}; all must be in house {target_text}.',),
    )


def navamsa_rashi(position: PlanetPosition) -> str | None:
    """Derive planetary Navamsa, failing closed near rounded boundaries."""
    boundaries = (NAVAMSA_WIDTH_DEGREES * index for index in range(10))
    if min(abs(position.degree - edge) for edge in boundaries) <= (
        NAVAMSA_ROUNDING_GUARD_DEGREES
    ):
        return None

    rashi_index = RASHI_NAMES.index(position.rashi)
    modality = rashi_index % 3
    if modality == 0:
        start = rashi_index
    elif modality == 1:
        start = (rashi_index + 8) % 12
    else:
        start = (rashi_index + 4) % 12
    division = min(8, int(position.degree / NAVAMSA_WIDTH_DEGREES))
    return RASHI_NAMES[(start + division) % 12]


def _adverse_placement_factors(
    rule: Mapping[str, Any],
    position: PlanetPosition,
    navamsa: str | None,
    house_frame_uncertain: bool,
) -> list[str]:
    adverse = []
    if not house_frame_uncertain and position.house in rule.get('avoid_houses', ()):
        adverse.append(f'house {position.house}')
    if position.rashi in rule.get('enemy_rashis', ()):
        adverse.append(f'enemy Rasi {position.rashi}')
    if position.rashi == rule.get('debilitation_rashi'):
        adverse.append(f'debilitation Rasi {position.rashi}')
    if navamsa is not None and navamsa == rule.get('navamsa_debilitation_rashi'):
        adverse.append(f'debilitation Navamsa {navamsa}')
    return adverse


def _solar_clearance_state(
    rule: Mapping[str, Any],
    positions: Mapping[str, PlanetPosition],
    position: PlanetPosition,
) -> tuple[str | None, bool, PrimitiveOutcome | None]:
    threshold = rule.get('solar_clearance_degrees')
    if threshold is None:
        return None, False, None
    surya = positions.get('Surya')
    if surya is None:
        return None, False, PrimitiveOutcome(
            'unknown', ('Surya facts needed for solar clearance are unavailable.',)
        )
    separation = abs((_longitude(position) - _longitude(surya) + 180) % 360 - 180)
    guard = rule.get('solar_clearance_guard_degrees', 0)
    if separation < threshold - guard:
        return (
            f'solar clearance {separation:.2f}° below {threshold:g}°',
            False,
            None,
        )
    return None, separation <= threshold + guard, None


def _guard_reasons(
    navamsa: str | None,
    solar_clearance_uncertain: bool,
    house_frame_uncertain: bool,
) -> list[str]:
    reasons = []
    if navamsa is None:
        reasons.append('Navamsa boundary')
    if solar_clearance_uncertain:
        reasons.append('solar-clearance threshold')
    if house_frame_uncertain:
        reasons.append('local-Lagna house frame')
    return reasons


def evaluate_well_situated(
    rule: Mapping[str, Any],
    positions: Mapping[str, PlanetPosition] | None,
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    """Evaluate the selected Phaladeepika 2.36 placement convention."""
    planet_name = rule.get('planet')
    position = positions.get(planet_name) if positions else None
    if position is None:
        return PrimitiveOutcome('unknown', (COMPLETE_GRAHA_FACTS_UNAVAILABLE,))

    navamsa = navamsa_rashi(position)
    adverse = _adverse_placement_factors(
        rule, position, navamsa, house_frame_uncertain
    )
    solar_adverse, solar_uncertain, unavailable = _solar_clearance_state(
        rule, positions, position
    )
    if unavailable is not None:
        return unavailable
    if solar_adverse is not None:
        adverse.append(solar_adverse)
    if adverse:
        return PrimitiveOutcome(
            'fail', (f'{planet_name}: ' + '; '.join(adverse) + '.',)
        )

    reasons = _guard_reasons(navamsa, solar_uncertain, house_frame_uncertain)
    if reasons:
        return PrimitiveOutcome(
            'unknown',
            (
                (
                    f'{planet_name}: {position.rashi} {position.degree:.2f}° '
                    f'is within the rounded {" and ".join(reasons)} guard.'
                ),
            ),
        )
    return PrimitiveOutcome(
        'pass',
        (
            (
                f'{planet_name}: {position.rashi}, house {position.house}, '
                f'{navamsa} Navamsa; no v1 adverse placement factor.'
            ),
        ),
    )


def _aspect_candidate(
    source_name: str,
    target_name: str,
    target_index: int,
    positions: Mapping[str, PlanetPosition],
) -> tuple[str | None, bool, bool]:
    if source_name == target_name:
        return None, False, True
    source = positions.get(source_name)
    offsets = FULL_ASPECT_OFFSETS.get(source_name)
    if source is None or offsets is None:
        return None, False, False
    if min(source.degree, 30 - source.degree) <= RASHI_ROUNDING_GUARD_DEGREES:
        return None, True, True
    source_index = RASHI_NAMES.index(source.rashi)
    aspector = source_name if (target_index - source_index) % 12 in offsets else None
    return aspector, False, True


def evaluate_full_aspect(
    rule: Mapping[str, Any],
    positions: Mapping[str, PlanetPosition] | None,
) -> PrimitiveOutcome:
    """Require at least one full classical Graha Drishti to the target."""
    target_name = rule.get('planet')
    target = positions.get(target_name) if positions else None
    if target is None:
        return PrimitiveOutcome('unknown', (COMPLETE_GRAHA_FACTS_UNAVAILABLE,))
    if min(target.degree, 30 - target.degree) <= RASHI_ROUNDING_GUARD_DEGREES:
        return PrimitiveOutcome(
            'unknown',
            ('The target graha is within the rounded Rasi boundary guard.',),
        )

    aspectors = []
    uncertain_aspector = False
    target_index = RASHI_NAMES.index(target.rashi)
    for source_name in rule.get('aspectors', ()):
        aspector, uncertain, complete = _aspect_candidate(
            source_name, target_name, target_index, positions
        )
        if not complete:
            return PrimitiveOutcome(
                'unknown',
                ('Complete classical-graha aspect facts are unavailable.',),
            )
        if aspector is not None:
            aspectors.append(aspector)
        uncertain_aspector = uncertain_aspector or uncertain

    if aspectors:
        return PrimitiveOutcome(
            'pass',
            (f'Full Graha Drishti to {target_name}: {", ".join(aspectors)}.',),
        )
    if uncertain_aspector:
        return PrimitiveOutcome(
            'unknown',
            ('A possible aspector is within the rounded Rasi boundary guard.',),
        )
    return PrimitiveOutcome(
        'fail', (f'No v1 full Graha Drishti reaches {target_name}.',)
    )


def _near_boundary(
    degree: float,
    boundaries: tuple[float, ...],
    motion_budget: float,
) -> bool:
    return min(abs(degree - boundary) for boundary in boundaries) <= (
        motion_budget + CONTRACT_DEGREE_HALF_STEP
    )


def _rashi_transition_unrepresented(
    start: PlanetPosition,
    end: PlanetPosition,
    motion_budget: float,
) -> bool:
    if start.rashi != end.rashi:
        return False
    return any(
        _near_boundary(position.degree, (0.0, 30.0), motion_budget)
        for position in (start, end)
    )


def _navamsa_transition_unrepresented(
    start: PlanetPosition,
    end: PlanetPosition,
    motion_budget: float,
) -> bool:
    start_division = int(start.degree / NAVAMSA_WIDTH_DEGREES)
    end_division = int(end.degree / NAVAMSA_WIDTH_DEGREES)
    if start.rashi != end.rashi or start_division != end_division:
        return False
    boundaries = tuple(NAVAMSA_WIDTH_DEGREES * index for index in range(10))
    return any(
        _near_boundary(position.degree, boundaries, motion_budget)
        for position in (start, end)
    )


def _shortest_separation(left: PlanetPosition, right: PlanetPosition) -> float:
    return abs((_longitude(left) - _longitude(right) + 180) % 360 - 180)


def _motion_exceeds_envelope(
    start: PlanetPosition,
    end: PlanetPosition,
    motion_budget: float,
) -> bool:
    return _shortest_separation(start, end) > (
        motion_budget + 2 * CONTRACT_DEGREE_HALF_STEP
    )


def _full_aspect_sources(
    rule: Mapping[str, Any],
    positions: Mapping[str, PlanetPosition],
) -> set[str]:
    target_name = rule.get('planet')
    target_index = RASHI_NAMES.index(positions[target_name].rashi)
    return {
        source_name
        for source_name in rule.get('aspectors', ())
        if source_name != target_name
        and (target_index - RASHI_NAMES.index(positions[source_name].rashi)) % 12
        in FULL_ASPECT_OFFSETS[source_name]
    }


def _well_situated_transition_uncertainty(
    rule: Mapping[str, Any],
    start_positions: Mapping[str, PlanetPosition],
    end_positions: Mapping[str, PlanetPosition],
    body_budget: float,
) -> str | None:
    target_name = rule.get('planet')
    target_start = start_positions[target_name]
    target_end = end_positions[target_name]
    relevant = [target_name]
    if rule.get('solar_clearance_degrees') is not None:
        relevant.append('Surya')
    if any(
        _motion_exceeds_envelope(
            start_positions[name], end_positions[name], body_budget
        )
        for name in relevant
    ):
        return f'{target_name}: sampled motion exceeds the Gold v1 transition envelope.'
    if _rashi_transition_unrepresented(
        target_start, target_end, body_budget
    ) or _navamsa_transition_unrepresented(target_start, target_end, body_budget):
        return (
            f'{target_name}: a Rasi or Navamsa transition cannot be excluded '
            'between these rounded samples.'
        )

    threshold = rule.get('solar_clearance_degrees')
    if threshold is None:
        return None
    relative_budget = (
        GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY * body_budget
        / GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY
        + 2 * CONTRACT_DEGREE_HALF_STEP
    )
    separations = (
        _shortest_separation(target_start, start_positions['Surya']),
        _shortest_separation(target_end, end_positions['Surya']),
    )
    if min(abs(value - threshold) for value in separations) <= relative_budget:
        return (
            f'{target_name}: the {threshold:g}° solar-clearance transition '
            'cannot be excluded between samples.'
        )
    return None


def _continuous_full_aspect_proved(
    target_start: PlanetPosition,
    target_end: PlanetPosition,
    source_start: PlanetPosition,
    source_end: PlanetPosition,
    body_budget: float,
) -> bool:
    return (
        not _motion_exceeds_envelope(source_start, source_end, body_budget)
        and target_start.rashi == target_end.rashi
        and source_start.rashi == source_end.rashi
        and not _rashi_transition_unrepresented(target_start, target_end, body_budget)
        and not _rashi_transition_unrepresented(source_start, source_end, body_budget)
    )


def _full_aspect_transition_uncertainty(
    rule: Mapping[str, Any],
    start_positions: Mapping[str, PlanetPosition],
    end_positions: Mapping[str, PlanetPosition],
    body_budget: float,
) -> str | None:
    target_name = rule.get('planet')
    target_start = start_positions[target_name]
    target_end = end_positions[target_name]
    if _motion_exceeds_envelope(target_start, target_end, body_budget):
        return f'{target_name}: sampled motion exceeds the Gold v1 transition envelope.'

    shared_sources = _full_aspect_sources(
        rule, start_positions
    ) & _full_aspect_sources(rule, end_positions)
    for source_name in shared_sources:
        if _continuous_full_aspect_proved(
            target_start,
            target_end,
            start_positions[source_name],
            end_positions[source_name],
            body_budget,
        ):
            return None
    return (
        f'{target_name}: a continuously present full Graha Drishti '
        'cannot be proved between samples.'
    )


def gold_transition_uncertainty(
    rule: Mapping[str, Any],
    start_positions: Mapping[str, PlanetPosition],
    end_positions: Mapping[str, PlanetPosition],
    gap_minutes: float,
) -> str | None:
    """Find a Gold predicate transition that the cadence cannot disprove."""
    body_budget = GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY * gap_minutes / (24 * 60)
    if rule.get('kind') == 'planet_well_situated':
        return _well_situated_transition_uncertainty(
            rule, start_positions, end_positions, body_budget
        )
    if rule.get('kind') == 'planet_receives_full_aspect':
        return _full_aspect_transition_uncertainty(
            rule, start_positions, end_positions, body_budget
        )
    return None
