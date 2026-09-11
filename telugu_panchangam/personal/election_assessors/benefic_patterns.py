"""Source-neutral natural-benefic placement and aspect patterns."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .chart_geometry import (
    FULL_ASPECT_OFFSETS,
    RASHI_ROUNDING_GUARD_DEGREES,
    evaluate_full_aspect,
)
from .contracts import PrimitiveOutcome
from .event_admission import PlanetPosition, planet_positions
from .graha_nature import (
    NaturalGrahaNature,
    classify_natural_graha_natures,
    evaluate_existential_benefic_house_set,
)

MALE_RASIS = frozenset(RASHI_NAMES[::2])
KENDRA_HOUSES = (1, 4, 7, 10)
_CLASSICAL_GRAHAS = tuple(FULL_ASPECT_OFFSETS)


def _prefixed(label: str, outcome: PrimitiveOutcome) -> tuple[str, ...]:
    return tuple(f'{label}: {item}' for item in outcome.evidence)


def _male_rasi_target_state(
    target_name: str,
    positions: Mapping[str, PlanetPosition],
    natures: Mapping[str, NaturalGrahaNature],
) -> tuple[str | None, bool]:
    """Return one resolved witness and whether this target remains possible."""
    target = positions[target_name]
    target_nature = natures[target_name]
    near_boundary = min(target.degree, 30 - target.degree) <= (
        RASHI_ROUNDING_GUARD_DEGREES
    )
    if target.rashi not in MALE_RASIS:
        return None, near_boundary and target_nature in {'benefic', 'unknown'}

    benefic_sources = [
        name
        for name in _CLASSICAL_GRAHAS
        if name != target_name and natures[name] == 'benefic'
    ]
    unresolved_sources = [
        name
        for name in _CLASSICAL_GRAHAS
        if name != target_name and natures[name] == 'unknown'
    ]
    benefic_aspect = evaluate_full_aspect(
        {'planet': target_name, 'aspectors': benefic_sources}, positions
    )
    unresolved_aspect = evaluate_full_aspect(
        {'planet': target_name, 'aspectors': unresolved_sources}, positions
    )
    if target_nature == 'benefic' and benefic_aspect.status == 'pass':
        aspectors = benefic_aspect.evidence[0].split(': ', 1)[1].removesuffix('.')
        return (
            (
                f'{target_name} in {target.rashi} receives full Graha Drishti '
                f'from {aspectors}'
            ),
            False,
        )

    possible_unknown_target = target_nature == 'unknown' and (
        benefic_aspect.status != 'fail' or unresolved_aspect.status != 'fail'
    )
    possible_unknown_aspector = target_nature == 'benefic' and (
        benefic_aspect.status == 'unknown' or unresolved_aspect.status != 'fail'
    )
    return None, possible_unknown_target or possible_unknown_aspector


def _male_rasi_benefic_aspect(
    chart: Mapping[str, Any],
) -> PrimitiveOutcome:
    positions = planet_positions(chart)
    nature = classify_natural_graha_natures(chart)
    if positions is None or not nature.complete:
        return PrimitiveOutcome('unknown', nature.evidence)

    witnesses: list[str] = []
    unresolved = False
    for target_name in _CLASSICAL_GRAHAS:
        witness, target_unresolved = _male_rasi_target_state(
            target_name, positions, nature.natures
        )
        if witness is not None:
            witnesses.append(witness)
        unresolved = unresolved or target_unresolved

    if witnesses:
        return PrimitiveOutcome(
            'pass',
            ('Resolved natural-benefic witness: ' + '; '.join(witnesses) + '.',),
        )
    if unresolved:
        return PrimitiveOutcome(
            'unknown',
            ('A possible natural-benefic male-Rasi aspect witness is unresolved.',),
        )
    return PrimitiveOutcome(
        'fail',
        (
            'No resolved natural benefic in an odd Rasi receives a full '
            + 'classical aspect from another resolved natural benefic.',
        ),
    )


def evaluate_benefic_kendra_or_male_rasi_aspect(
    chart: Mapping[str, Any],
    *,
    house_frame_uncertain: bool = False,
) -> PrimitiveOutcome:
    """Evaluate the disclosed two-arm benefic pattern without an event effect."""
    if type(house_frame_uncertain) is not bool:
        return PrimitiveOutcome(
            'unknown', ('The benefic-pattern configuration is malformed.',)
        )
    if house_frame_uncertain:
        return PrimitiveOutcome(
            'unknown',
            ('The validated local-Lagna house frame is unavailable or conflicting.',),
        )
    if not isinstance(chart, Mapping):
        return PrimitiveOutcome(
            'unknown', ('Complete canonical nine-graha facts are unavailable.',)
        )

    kendra = evaluate_existential_benefic_house_set(chart, KENDRA_HOUSES)
    male_rasi_aspect = _male_rasi_benefic_aspect(chart)
    evidence = (
        *_prefixed('Kendra arm', kendra),
        *_prefixed('Male-Rasi aspect arm', male_rasi_aspect),
    )
    if 'pass' in {kendra.status, male_rasi_aspect.status}:
        return PrimitiveOutcome('pass', evidence)
    if 'unknown' in {kendra.status, male_rasi_aspect.status}:
        return PrimitiveOutcome('unknown', evidence)
    return PrimitiveOutcome('fail', evidence)
