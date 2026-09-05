"""Pure, source-versioned primitives shared by event assessors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .facts import PlanetPosition

NAVAMSA_WIDTH_DEGREES = 30 / 9
NAVAMSA_ROUNDING_GUARD_DEGREES = 0.01
RASHI_ROUNDING_GUARD_DEGREES = 0.01

# Safety-envelope values for the ten-minute browser sampling contract.  Their
# astronomical derivation and product-policy boundary are registered under
# ``election_chart.gold_transition_envelope_v1``; they are not jyotisha rules.
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

NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES = 0.02
_BOUNDARY_EPSILON = 1e-9


@dataclass(frozen=True)
class PrimitiveOutcome:
    status: str
    evidence: tuple[str, ...] = ()


def _longitude(position: PlanetPosition) -> float:
    return RASHI_NAMES.index(position.rashi) * 30 + position.degree


def evaluate_house_free_of_natural_malefics(
    rule: Mapping[str, Any],
    positions: Mapping[str, PlanetPosition] | None,
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    """Apply the disclosed Annaprasana natural-malefic convention."""
    if positions is None:
        return PrimitiveOutcome(
            'unknown', ('Complete graha facts are unavailable.',))
    if house_frame_uncertain:
        return PrimitiveOutcome(
            'unknown', ('The local-Lagna house frame is uncertain.',))

    house = rule.get('house')
    fixed = [
        name for name in rule.get('fixed_malefics', ())
        if positions[name].house == house
    ]
    if fixed:
        return PrimitiveOutcome(
            'fail',
            (f'Natural malefics in Lagna: {", ".join(fixed)}.',),
        )

    chandra = positions['Chandra']
    if chandra.house != house:
        return PrimitiveOutcome(
            'pass',
            ('Natural malefics in Lagna: none; Chandra is outside Lagna.',),
        )

    surya = positions['Surya']
    elongation = (_longitude(chandra) - _longitude(surya)) % 360
    guard = rule.get(
        'lunar_phase_guard_degrees',
        NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES,
    )
    boundary_distance = min(
        elongation, 360 - elongation, abs(elongation - 180))
    if boundary_distance <= guard + _BOUNDARY_EPSILON:
        return PrimitiveOutcome(
            'unknown',
            (
                f'Chandra occupies Lagna at {elongation:.2f}\N{DEGREE SIGN} '
                f'solar elongation, inside the disclosed ±{guard:.2f}° '
                'phase boundary guard.',
            ),
        )
    if elongation > 180:
        return PrimitiveOutcome(
            'fail',
            (
                f'Natural malefics in Lagna: waning Chandra '
                f'({elongation:.2f}\N{DEGREE SIGN} solar elongation).',
            ),
        )
    return PrimitiveOutcome(
        'pass',
        (
            f'Natural malefics in Lagna: none; waxing Chandra '
            f'({elongation:.2f}\N{DEGREE SIGN} solar elongation) is not '
            'malefic under this convention.',
        ),
    )


def navamsa_rashi(position: PlanetPosition) -> str | None:
    """Derive planetary Navamsa, failing closed near rounded boundaries."""
    internal_boundaries = (
        NAVAMSA_WIDTH_DEGREES * index for index in range(10)
    )
    if min(abs(position.degree - edge) for edge in internal_boundaries) <= (
        NAVAMSA_ROUNDING_GUARD_DEGREES
    ):
        return None

    rashi_index = RASHI_NAMES.index(position.rashi)
    modality = rashi_index % 3
    if modality == 0:  # movable: begin from the Rasi itself
        start = rashi_index
    elif modality == 1:  # fixed: begin from the ninth Rasi inclusively
        start = (rashi_index + 8) % 12
    else:  # dual: begin from the fifth Rasi inclusively
        start = (rashi_index + 4) % 12
    division = min(8, int(position.degree / NAVAMSA_WIDTH_DEGREES))
    return RASHI_NAMES[(start + division) % 12]


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
        return PrimitiveOutcome('unknown', ('Complete graha facts are unavailable.',))

    navamsa = navamsa_rashi(position)
    adverse: list[str] = []
    solar_clearance_uncertain = False
    if not house_frame_uncertain and position.house in rule.get('avoid_houses', ()):
        adverse.append(f'house {position.house}')
    if position.rashi in rule.get('enemy_rashis', ()):
        adverse.append(f'enemy Rasi {position.rashi}')
    if position.rashi == rule.get('debilitation_rashi'):
        adverse.append(f'debilitation Rasi {position.rashi}')
    if navamsa is not None and navamsa == rule.get('navamsa_debilitation_rashi'):
        adverse.append(f'debilitation Navamsa {navamsa}')
    solar_threshold = rule.get('solar_clearance_degrees')
    if solar_threshold is not None:
        surya = positions.get('Surya') if positions else None
        if surya is None:
            return PrimitiveOutcome(
                'unknown', ('Surya facts needed for solar clearance are unavailable.',)
            )
        longitude = RASHI_NAMES.index(position.rashi) * 30 + position.degree
        solar_longitude = RASHI_NAMES.index(surya.rashi) * 30 + surya.degree
        separation = abs((longitude - solar_longitude + 180) % 360 - 180)
        guard = rule.get('solar_clearance_guard_degrees', 0)
        if separation < solar_threshold - guard:
            adverse.append(
                f'solar clearance {separation:.2f}° below {solar_threshold:g}°'
            )
        elif separation <= solar_threshold + guard:
            solar_clearance_uncertain = True
    if adverse:
        return PrimitiveOutcome(
            'fail',
            (f'{planet_name}: ' + '; '.join(adverse) + '.',),
        )
    if navamsa is None or solar_clearance_uncertain or house_frame_uncertain:
        reasons = []
        if navamsa is None:
            reasons.append('Navamsa boundary')
        if solar_clearance_uncertain:
            reasons.append('solar-clearance threshold')
        if house_frame_uncertain:
            reasons.append('local-Lagna house frame')
        return PrimitiveOutcome(
            'unknown',
            (
                (
                    f'{planet_name}: {position.rashi} '
                    f'{position.degree:.2f}° is within the rounded '
                    f'{" and ".join(reasons)} guard.'
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


def evaluate_full_aspect(
    rule: Mapping[str, Any],
    positions: Mapping[str, PlanetPosition] | None,
) -> PrimitiveOutcome:
    """Require at least one full classical Graha Drishti to the target."""
    target_name = rule.get('planet')
    target = positions.get(target_name) if positions else None
    if target is None:
        return PrimitiveOutcome('unknown', ('Complete graha facts are unavailable.',))
    if min(target.degree, 30 - target.degree) <= RASHI_ROUNDING_GUARD_DEGREES:
        return PrimitiveOutcome(
            'unknown',
            ('The target graha is within the rounded Rasi boundary guard.',),
        )
    target_index = RASHI_NAMES.index(target.rashi)
    aspectors: list[str] = []
    uncertain_aspector = False
    for source_name in rule.get('aspectors', ()):
        if source_name == target_name:
            continue
        source = positions.get(source_name) if positions else None
        offsets = FULL_ASPECT_OFFSETS.get(source_name)
        if source is None or offsets is None:
            return PrimitiveOutcome(
                'unknown', ('Complete classical-graha aspect facts are unavailable.',)
            )
        if min(source.degree, 30 - source.degree) <= RASHI_ROUNDING_GUARD_DEGREES:
            uncertain_aspector = True
            continue
        source_index = RASHI_NAMES.index(source.rashi)
        if (target_index - source_index) % 12 in offsets:
            aspectors.append(source_name)
    if not aspectors:
        if uncertain_aspector:
            return PrimitiveOutcome(
                'unknown',
                ('A possible aspector is within the rounded Rasi boundary guard.',),
            )
        return PrimitiveOutcome(
            'fail',
            (f'No v1 full Graha Drishti reaches {target_name}.',),
        )
    return PrimitiveOutcome(
        'pass',
        (f'Full Graha Drishti to {target_name}: {", ".join(aspectors)}.',),
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
    boundaries = tuple(
        NAVAMSA_WIDTH_DEGREES * index for index in range(10)
    )
    return any(
        _near_boundary(position.degree, boundaries, motion_budget)
        for position in (start, end)
    )


def _shortest_separation(
    left: PlanetPosition,
    right: PlanetPosition,
) -> float:
    left_longitude = RASHI_NAMES.index(left.rashi) * 30 + left.degree
    right_longitude = RASHI_NAMES.index(right.rashi) * 30 + right.degree
    return abs((left_longitude - right_longitude + 180) % 360 - 180)


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
    target = positions[target_name]
    target_index = RASHI_NAMES.index(target.rashi)
    return {
        source_name
        for source_name in rule.get('aspectors', ())
        if source_name != target_name
        and (
            target_index - RASHI_NAMES.index(positions[source_name].rashi)
        ) % 12 in FULL_ASPECT_OFFSETS[source_name]
    }


def gold_transition_uncertainty(
    rule: Mapping[str, Any],
    start_positions: Mapping[str, PlanetPosition],
    end_positions: Mapping[str, PlanetPosition],
    gap_minutes: float,
) -> str | None:
    """Find a Gold predicate transition that the cadence cannot disprove.

    A boundary crossing with different endpoint states is represented by both
    sides.  When endpoint states match, the documented angular-motion envelope
    expands each rounded endpoint; overlap with a controlling boundary fails
    closed because a cross-and-return cannot otherwise be ruled out.
    """
    body_budget = (
        GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY * gap_minutes / (24 * 60)
    )
    kind = rule.get('kind')
    target_name = rule.get('planet')
    target_start = start_positions[target_name]
    target_end = end_positions[target_name]

    if kind == 'planet_well_situated':
        relevant = [target_name]
        if rule.get('solar_clearance_degrees') is not None:
            relevant.append('Surya')
        if any(
            _motion_exceeds_envelope(
                start_positions[name], end_positions[name], body_budget,
            )
            for name in relevant
        ):
            return (
                f'{target_name}: sampled motion exceeds the Gold v1 '
                'transition envelope.'
            )
        if _rashi_transition_unrepresented(
            target_start, target_end, body_budget,
        ) or _navamsa_transition_unrepresented(
            target_start, target_end, body_budget,
        ):
            return (
                f'{target_name}: a Rasi or Navamsa transition cannot be '
                'excluded between these rounded samples.'
            )
        threshold = rule.get('solar_clearance_degrees')
        if threshold is not None:
            relative_budget = (
                GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY
                * gap_minutes / (24 * 60)
                + 2 * CONTRACT_DEGREE_HALF_STEP
            )
            separations = (
                _shortest_separation(
                    target_start, start_positions['Surya'],
                ),
                _shortest_separation(
                    target_end, end_positions['Surya'],
                ),
            )
            if min(abs(value - threshold) for value in separations) <= (
                relative_budget
            ):
                return (
                    f'{target_name}: the {threshold:g}° solar-clearance '
                    'transition cannot be excluded between samples.'
                )
        return None

    if kind == 'planet_receives_full_aspect':
        if _motion_exceeds_envelope(
            target_start, target_end, body_budget,
        ):
            return (
                f'{target_name}: sampled motion exceeds the Gold v1 '
                'transition envelope.'
            )
        start_sources = _full_aspect_sources(rule, start_positions)
        end_sources = _full_aspect_sources(rule, end_positions)
        for source_name in start_sources & end_sources:
            source_start = start_positions[source_name]
            source_end = end_positions[source_name]
            if not _motion_exceeds_envelope(
                source_start, source_end, body_budget,
            ) and not any(
                _rashi_transition_unrepresented(left, right, body_budget)
                for left, right in (
                    (target_start, target_end),
                    (source_start, source_end),
                )
            ) and (
                target_start.rashi == target_end.rashi
                and source_start.rashi == source_end.rashi
            ):
                return None
        return (
            f'{target_name}: a continuously present full Graha Drishti '
            'cannot be proved between samples.'
        )
    return None
