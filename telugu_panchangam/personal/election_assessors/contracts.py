"""Shared result contracts for source-backed election assessors."""

from dataclasses import dataclass

COMPLETE_GRAHA_FACTS_UNAVAILABLE = 'Complete graha facts are unavailable.'


@dataclass(frozen=True)
class PrimitiveOutcome:
    status: str
    evidence: tuple[str, ...] = ()
