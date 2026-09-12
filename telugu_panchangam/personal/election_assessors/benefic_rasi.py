"""Reusable benefic-Rasi interpretation with no event effect."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .contracts import PrimitiveOutcome
from .graha_nature import classify_natural_graha_natures
from .lordship import CLASSICAL_RASI_LORDS

BENEFIC_RASI_CONVENTION_ID = 'benefic-rasi-by-resolved-natural-lord-v1'


def evaluate_benefic_rasi(
    chart: Mapping[str, Any], rashi: object
) -> PrimitiveOutcome:
    """Classify a Rasi through its classical lord's resolved natural nature."""
    if rashi not in RASHI_NAMES:
        return PrimitiveOutcome('unknown', ('The target Rasi is invalid.',))
    result = classify_natural_graha_natures(chart)
    if not result.complete:
        return PrimitiveOutcome('unknown', result.evidence)
    lord = CLASSICAL_RASI_LORDS[rashi]
    nature = result.natures[lord]
    evidence = (
        f'{rashi} is owned by {lord}; the registered natural-nature '
        f'classifier resolves the lord as {nature}.',
    )
    if nature == 'unknown':
        return PrimitiveOutcome('unknown', evidence + result.evidence)
    return PrimitiveOutcome('pass' if nature == 'benefic' else 'fail', evidence)
