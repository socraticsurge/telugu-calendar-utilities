"""Graha-nature predicates, separate from chart geometry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import floor
from typing import Any, Literal

from ...panchangam_names import RASHI_NAMES
from ..election_chart_rules import ELECTION_CHART_PLANETS
from .contracts import COMPLETE_GRAHA_FACTS_UNAVAILABLE, PrimitiveOutcome
from .conventions import ELECTION_CHART_CONVENTIONS
from .event_admission import PlanetPosition, planet_positions

NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES = 0.02
_BOUNDARY_EPSILON = 1e-9

NATURAL_GRAHA_NATURE_CONVENTION_ID = (
    'phaladeepika-natural-graha-nature-whole-sign-v1'
)
_NATURAL_GRAHA_NATURE_CONVENTION = ELECTION_CHART_CONVENTIONS[
    NATURAL_GRAHA_NATURE_CONVENTION_ID
]
_FIXED_MALEFICS = frozenset(
    _NATURAL_GRAHA_NATURE_CONVENTION['fixed_malefics']
)
_FIXED_BENEFICS = frozenset(
    _NATURAL_GRAHA_NATURE_CONVENTION['fixed_benefics']
)
_PHASE_QUANTIZATION_SCALE = 10 ** int(
    _NATURAL_GRAHA_NATURE_CONVENTION['phase_quantization_decimal_places']
)
_PHASE_GUARD_UNITS = floor(
    NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES
    * _PHASE_QUANTIZATION_SCALE
    + 0.5
)
_HALF_CIRCLE_UNITS = 180 * _PHASE_QUANTIZATION_SCALE
_FULL_CIRCLE_UNITS = 360 * _PHASE_QUANTIZATION_SCALE

NaturalGrahaNature = Literal['benefic', 'malefic', 'unknown']


@dataclass(frozen=True)
class NaturalGrahaNatureResult:
    """Resolved natural natures for one complete canonical chart."""

    complete: bool
    natures: Mapping[str, NaturalGrahaNature]
    evidence: tuple[str, ...] = ()


def _longitude(position: PlanetPosition) -> float:
    return RASHI_NAMES.index(position.rashi) * 30 + position.degree


def _unknown_natures() -> dict[str, NaturalGrahaNature]:
    return {name: 'unknown' for name in ELECTION_CHART_PLANETS}


def _resolved_chandra_nature(
    positions: Mapping[str, PlanetPosition],
) -> tuple[NaturalGrahaNature, float]:
    raw_elongation = (
        _longitude(positions['Chandra']) - _longitude(positions['Surya'])
    ) % 360
    elongation_units = floor(
        raw_elongation * _PHASE_QUANTIZATION_SCALE + 0.5
    )
    elongation = elongation_units / _PHASE_QUANTIZATION_SCALE
    boundary_distance_units = min(
        elongation_units,
        abs(elongation_units - _HALF_CIRCLE_UNITS),
        abs(_FULL_CIRCLE_UNITS - elongation_units),
    )
    if boundary_distance_units <= _PHASE_GUARD_UNITS:
        return 'unknown', elongation
    if elongation_units < _HALF_CIRCLE_UNITS:
        return 'benefic', elongation
    return 'malefic', elongation


def classify_natural_graha_natures(
    chart: Mapping[str, Any],
) -> NaturalGrahaNatureResult:
    """Classify all nine grahas under the disclosed natural-nature v1."""
    positions = planet_positions(chart) if isinstance(chart, Mapping) else None
    if positions is None:
        return NaturalGrahaNatureResult(
            complete=False,
            natures=_unknown_natures(),
            evidence=(
                'Complete canonical nine-graha facts are unavailable or invalid.',
            ),
        )

    natures: dict[str, NaturalGrahaNature] = _unknown_natures()
    for name in _FIXED_MALEFICS:
        natures[name] = 'malefic'
    for name in _FIXED_BENEFICS:
        natures[name] = 'benefic'

    chandra_nature, elongation = _resolved_chandra_nature(positions)
    natures['Chandra'] = chandra_nature
    if chandra_nature == 'unknown':
        chandra_evidence = (
            f'Chandra elongation {elongation:.4f}° is inside the inclusive '
            f'{NATURAL_MALEFIC_LUNAR_PHASE_GUARD_DEGREES:.2f}° '
            'phase-boundary guard.'
        )
    else:
        chandra_evidence = (
            f'Chandra elongation {elongation:.4f}° resolves {chandra_nature}.'
        )

    budha = positions['Budha']
    companions = [
        name
        for name in ELECTION_CHART_PLANETS
        if name != 'Budha' and positions[name].rashi == budha.rashi
    ]
    malefic_witnesses = [
        name for name in companions if natures[name] == 'malefic'
    ]
    if malefic_witnesses:
        natures['Budha'] = 'malefic'
        budha_evidence = (
            f'Budha shares {budha.rashi} with resolved malefic '
            f'{", ".join(malefic_witnesses)}.'
        )
    elif 'Chandra' in companions and natures['Chandra'] == 'unknown':
        natures['Budha'] = 'unknown'
        budha_evidence = (
            f'Budha shares {budha.rashi} only with phase-unknown Chandra '
            'as a possible malefic witness.'
        )
    else:
        natures['Budha'] = 'benefic'
        budha_evidence = (
            f"No resolved malefic shares Budha's sidereal Rasi {budha.rashi}."
        )

    return NaturalGrahaNatureResult(
        complete=True,
        natures={name: natures[name] for name in ELECTION_CHART_PLANETS},
        evidence=(chandra_evidence, budha_evidence),
    )


def _house_set(houses: Any) -> frozenset[int] | None:
    if isinstance(houses, (str, bytes)):
        return None
    try:
        values = tuple(houses)
    except TypeError:
        return None
    if not values or any(
        type(house) is not int or not 1 <= house <= 12 for house in values
    ):
        return None
    return frozenset(values)


def _house_witnesses(
    chart: Mapping[str, Any], houses: Any
) -> tuple[NaturalGrahaNatureResult, list[tuple[str, int]]] | None:
    target_houses = _house_set(houses)
    if target_houses is None:
        return None
    result = classify_natural_graha_natures(chart)
    if not result.complete:
        return result, []
    positions = planet_positions(chart)
    if positions is None:
        return NaturalGrahaNatureResult(False, _unknown_natures()), []
    occupants = [
        (name, positions[name].house)
        for name in ELECTION_CHART_PLANETS
        if positions[name].house in target_houses
    ]
    return result, occupants


def evaluate_existential_benefic_house_set(
    chart: Mapping[str, Any], houses: Any
) -> PrimitiveOutcome:
    """Pass when any target house has a resolved natural benefic witness."""
    witnesses = _house_witnesses(chart, houses)
    if witnesses is None:
        return PrimitiveOutcome('unknown', ('The required house set is invalid.',))
    result, occupants = witnesses
    if not result.complete:
        return PrimitiveOutcome('unknown', result.evidence)
    benefics = [
        (name, house)
        for name, house in occupants
        if result.natures[name] == 'benefic'
    ]
    if benefics:
        detail = ', '.join(f'{name} (house {house})' for name, house in benefics)
        return PrimitiveOutcome(
            'pass', (f'Resolved natural-benefic witness: {detail}.',)
        )
    unresolved = [
        (name, house)
        for name, house in occupants
        if result.natures[name] == 'unknown'
    ]
    if unresolved:
        detail = ', '.join(f'{name} (house {house})' for name, house in unresolved)
        return PrimitiveOutcome(
            'unknown', (f'Natural-benefic witness remains unresolved: {detail}.',)
        )
    return PrimitiveOutcome(
        'fail', ('No resolved natural benefic occupies the required house set.',)
    )


def evaluate_forbidden_malefic_house_set(
    chart: Mapping[str, Any], houses: Any
) -> PrimitiveOutcome:
    """Pass only when no target house has a natural-malefic witness."""
    witnesses = _house_witnesses(chart, houses)
    if witnesses is None:
        return PrimitiveOutcome('unknown', ('The forbidden house set is invalid.',))
    result, occupants = witnesses
    if not result.complete:
        return PrimitiveOutcome('unknown', result.evidence)
    malefics = [
        (name, house)
        for name, house in occupants
        if result.natures[name] == 'malefic'
    ]
    if malefics:
        detail = ', '.join(f'{name} (house {house})' for name, house in malefics)
        return PrimitiveOutcome(
            'fail', (f'Forbidden natural-malefic witness: {detail}.',)
        )
    unresolved = [
        (name, house)
        for name, house in occupants
        if result.natures[name] == 'unknown'
    ]
    if unresolved:
        detail = ', '.join(f'{name} (house {house})' for name, house in unresolved)
        return PrimitiveOutcome(
            'unknown', (f'Forbidden-malefic check remains unresolved: {detail}.',)
        )
    return PrimitiveOutcome(
        'pass', ('No resolved natural malefic occupies the forbidden house set.',)
    )


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
