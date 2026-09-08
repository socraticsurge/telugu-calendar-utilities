"""Graha-nature predicates, separate from chart geometry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .contracts import COMPLETE_GRAHA_FACTS_UNAVAILABLE, PrimitiveOutcome
from .event_admission import PlanetPosition

NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES = 0.02
_BOUNDARY_EPSILON = 1e-9


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
        return PrimitiveOutcome('unknown', (COMPLETE_GRAHA_FACTS_UNAVAILABLE,))
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
