"""Compatibility exports for the partitioned election primitives."""

from .chart_geometry import (
    CONTRACT_DEGREE_HALF_STEP,
    FULL_ASPECT_OFFSETS,
    GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY,
    GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY,
    GOLD_MAX_SAMPLE_GAP_MINUTES,
    NAVAMSA_ROUNDING_GUARD_DEGREES,
    NAVAMSA_WIDTH_DEGREES,
    RASHI_ROUNDING_GUARD_DEGREES,
    evaluate_all_planets_in_houses,
    evaluate_full_aspect,
    evaluate_well_situated,
    gold_transition_uncertainty,
    navamsa_rashi,
)
from .contracts import PrimitiveOutcome
from .graha_nature import (
    NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES,
    evaluate_house_free_of_natural_malefics,
)

__all__ = [
    'CONTRACT_DEGREE_HALF_STEP',
    'FULL_ASPECT_OFFSETS',
    'GOLD_MAX_GRAHA_MOTION_DEGREES_PER_DAY',
    'GOLD_MAX_RELATIVE_MOTION_DEGREES_PER_DAY',
    'GOLD_MAX_SAMPLE_GAP_MINUTES',
    'NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES',
    'NAVAMSA_ROUNDING_GUARD_DEGREES',
    'NAVAMSA_WIDTH_DEGREES',
    'PrimitiveOutcome',
    'RASHI_ROUNDING_GUARD_DEGREES',
    'evaluate_all_planets_in_houses',
    'evaluate_full_aspect',
    'evaluate_house_free_of_natural_malefics',
    'evaluate_well_situated',
    'gold_transition_uncertainty',
    'navamsa_rashi',
]
