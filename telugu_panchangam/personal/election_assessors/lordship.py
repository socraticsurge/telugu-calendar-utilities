"""Source-neutral classical Rasi lordship and Whole Sign separation facts."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .contracts import PrimitiveOutcome
from .event_admission import planet_positions

LORD_POSITION_FACTS_UNAVAILABLE = (
    'Complete canonical nine-graha position facts are unavailable or conflicting.'
)

CLASSICAL_RASI_LORDS: Mapping[str, str] = MappingProxyType({
    'Mesha': 'Kuja',
    'Vrishabha': 'Shukra',
    'Mithuna': 'Budha',
    'Karka': 'Chandra',
    'Simha': 'Surya',
    'Kanya': 'Budha',
    'Tula': 'Shukra',
    'Vrischika': 'Kuja',
    'Dhanu': 'Guru',
    'Makara': 'Shani',
    'Kumbha': 'Shani',
    'Meena': 'Guru',
})


def derive_lagna_sixth_lords(
    lagna_rashi: object,
) -> tuple[str, str, str] | None:
    """Return Lagna lord, sixth Rasi, and sixth lord for a valid Lagna."""
    if lagna_rashi not in RASHI_NAMES:
        return None
    lagna_index = RASHI_NAMES.index(lagna_rashi)
    sixth_rashi = RASHI_NAMES[(lagna_index + 5) % 12]
    return (
        CLASSICAL_RASI_LORDS[lagna_rashi],
        sixth_rashi,
        CLASSICAL_RASI_LORDS[sixth_rashi],
    )


def whole_sign_shortest_distance(left_rashi: object, right_rashi: object) -> int | None:
    """Return the undirected shortest distance on the twelve-Rasi circle."""
    if left_rashi not in RASHI_NAMES or right_rashi not in RASHI_NAMES:
        return None
    delta = abs(RASHI_NAMES.index(left_rashi) - RASHI_NAMES.index(right_rashi))
    return min(delta, 12 - delta)


def evaluate_rasi_lord_separation(
    chart: Mapping[str, Any],
    *,
    first_rashi: str,
    second_rashi: str,
    required_shortest_distance: int,
) -> PrimitiveOutcome:
    """Compare two classical Rasi lords without applying an event effect."""
    if (
        first_rashi not in RASHI_NAMES
        or second_rashi not in RASHI_NAMES
        or type(required_shortest_distance) is not int
        or not 0 <= required_shortest_distance <= 6
    ):
        return PrimitiveOutcome(
            'unknown', ('The Rasi-lord separation configuration is incomplete.',)
        )
    if not isinstance(chart, Mapping):
        return PrimitiveOutcome('unknown', (LORD_POSITION_FACTS_UNAVAILABLE,))
    positions = planet_positions(chart)
    if positions is None:
        return PrimitiveOutcome('unknown', (LORD_POSITION_FACTS_UNAVAILABLE,))

    first_lord = CLASSICAL_RASI_LORDS[first_rashi]
    second_lord = CLASSICAL_RASI_LORDS[second_rashi]
    first_position = positions[first_lord]
    second_position = positions[second_lord]
    distance = whole_sign_shortest_distance(
        first_position.rashi, second_position.rashi
    )
    if distance is None:  # Defensive; admitted position facts guarantee Rasis.
        return PrimitiveOutcome('unknown', (LORD_POSITION_FACTS_UNAVAILABLE,))

    if first_lord == second_lord:
        evidence = (
            f'{first_rashi} and {second_rashi} share lord {first_lord} in '
            + f'{first_position.rashi}; shortest Whole Sign distance is 0 '
            + f'(required {required_shortest_distance}).'
        )
    else:
        evidence = (
            f'{first_rashi} lord {first_lord} is in {first_position.rashi}; '
            + f'{second_rashi} lord {second_lord} is in {second_position.rashi}; '
            + f'shortest Whole Sign distance is {distance} '
            + f'(required {required_shortest_distance}).'
        )
    return PrimitiveOutcome(
        'pass' if distance == required_shortest_distance else 'fail',
        (evidence,),
    )
