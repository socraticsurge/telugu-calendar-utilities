"""Strict normalization of the chart facts consumed by local assessors."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ...panchangam_names import RASHI_NAMES
from ..election_chart_rules import ELECTION_CHART_PLANETS


@dataclass(frozen=True)
class PlanetPosition:
    """One canonical graha position in the local Whole Sign frame."""

    name: str
    rashi: str
    degree: float
    house: int
    retrograde: bool


def _planet_items(chart: Mapping[str, Any]) -> list[Any] | None:
    planets = chart.get('planets')
    if not isinstance(planets, list) or len(planets) != len(ELECTION_CHART_PLANETS):
        return None
    return planets


def planet_houses(chart: Mapping[str, Any]) -> dict[str, int] | None:
    """Return houses only when every canonical position fact is complete."""
    positions = planet_positions(chart)
    if positions is None:
        return None
    return {name: position.house for name, position in positions.items()}


def planet_positions(
    chart: Mapping[str, Any],
) -> dict[str, PlanetPosition] | None:
    """Return all exact facts or ``None`` when any required fact is invalid."""
    planets = _planet_items(chart)
    if planets is None:
        return None
    result: dict[str, PlanetPosition] = {}
    for item in planets:
        if not isinstance(item, Mapping):
            return None
        name = item.get('name')
        rashi = item.get('rashi')
        degree = item.get('degree')
        house = item.get('house')
        retrograde = item.get('retrograde')
        if (
            name not in ELECTION_CHART_PLANETS
            or name in result
            or rashi not in RASHI_NAMES
            or isinstance(degree, bool)
            or not isinstance(degree, (int, float))
            or not math.isfinite(degree)
            or not 0 <= degree < 30
            or type(house) is not int
            or not 1 <= house <= 12
            or type(retrograde) is not bool
        ):
            return None
        result[name] = PlanetPosition(
            name=name,
            rashi=rashi,
            degree=float(degree),
            house=house,
            retrograde=retrograde,
        )
    return result if set(result) == set(ELECTION_CHART_PLANETS) else None
