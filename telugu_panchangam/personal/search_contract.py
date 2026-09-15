"""Transport-independent Muhurta search inputs and results.

Raw slots retain timezone-aware instants; only a surface adapter formats them.
Ranking is pool-relative, with existing personal/day caution caps preserved.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TypedDict


class ReasonGroups(TypedDict):
    slot_quality: list[str]
    day_quality: list[str]
    group_fit: list[str]
    activity_match: list[str]
    notes: list[str]


class SlotDecision(TypedDict):
    date: str
    vaaram: str
    start: datetime
    end: datetime
    score: int
    personal_dosha: str | None
    day_dosha: str | None
    reasons: list[str]
    reason_groups: ReasonGroups
    tier: str


@dataclass(frozen=True)
class SearchPeriod:
    start: date
    days: int


@dataclass(frozen=True)
class SearchOptions:
    activity: str = "any"
    janma_nakshatras: list[str] | None = None
    janma_rasis: list[str | None] | None = None
    janma_lagnas: list[str | None] | None = None
    chandra_mode: str = "stars"
    travel_direction: str | None = None
    include_night: bool = False

    def slot_arguments(self) -> dict:
        """The established day/night APIs share these exact arguments."""
        return {
            key: value for key, value in vars(self).items() if key != "include_night"
        }


@dataclass
class SearchResult:
    slots: list[SlotDecision] = field(default_factory=list)
    dropped_days: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ScoreContribution:
    """One scorer's value and explanations, with no shared mutable buckets."""

    score: int = 0
    slot_quality: tuple[str, ...] = ()
    activity_match: tuple[str, ...] = ()
    group_fit: tuple[str, ...] = ()


@dataclass(frozen=True)
class LagnaContribution:
    contribution: ScoreContribution
    lagna: str | None
    ashtama_names: tuple[str, ...]
