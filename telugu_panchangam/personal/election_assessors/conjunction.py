"""Event-bounded conjunction facts, separate from event ranking policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ...panchangam_names import RASHI_NAMES
from .contracts import PrimitiveOutcome
from .event_admission import PlanetPosition

CONJUNCTION_FACTS_UNAVAILABLE = (
    "Complete canonical nine-graha Rasi facts are unavailable."
)
_CANONICAL_GRAHAS = frozenset(
    (
        "Surya",
        "Chandra",
        "Kuja",
        "Budha",
        "Guru",
        "Shukra",
        "Shani",
        "Rahu",
        "Ketu",
    )
)

SAME_RASI_CONJUNCTION_METADATA: dict[str, Any] = {
    "source_statement": {
        "claim_id": "muhurta.borrowing_money",
        "text": "Avoid Chandra conjoined with Mangala or Shani.",
        "locator": (
            "B. V. Raman, Chapter X, 'Borrowing Money,' inspected in the "
            "2020 Chistabo derivative at internal printed p. 45 "
            "(physical PDF p. 49)"
        ),
    },
    "convention": {
        "id": "same-rasi-distributive-conjunction-v1",
        "method_claim_id": (
            "election_chart.same_rasi_distributive_conjunction_policy_v1"
        ),
        "formula": "R(Chandra) = R(Kuja) OR R(Chandra) = R(Shani)",
        "degree_orb": None,
    },
    "event_policy": {
        "id": "borrowing-money.same-rasi-conjunction-reject-v1",
        "decision_claim_id": (
            "election_chart.borrowing_same_rasi_conjunction_reject_policy_v1"
        ),
        "activity": "borrowing_money",
        "effect": "reject",
        "status": "implemented",
        "delivery_issue": 271,
    },
}


def evaluate_same_rasi_chandra_conjunction(
    positions: Mapping[str, PlanetPosition] | None,
) -> PrimitiveOutcome:
    """Evaluate the accepted Chandra-Kuja/Shani same-Rasi convention."""
    if (
        positions is None
        or set(positions) != _CANONICAL_GRAHAS
        or any(
            position.name != name or position.rashi not in RASHI_NAMES
            for name, position in positions.items()
        )
    ):
        return PrimitiveOutcome("unknown", (CONJUNCTION_FACTS_UNAVAILABLE,))

    chandra = positions.get("Chandra")
    kuja = positions.get("Kuja")
    shani = positions.get("Shani")
    if chandra is None or kuja is None or shani is None:
        return PrimitiveOutcome("unknown", (CONJUNCTION_FACTS_UNAVAILABLE,))

    matches = [
        name
        for name, position in (("Kuja", kuja), ("Shani", shani))
        if position.rashi == chandra.rashi
    ]
    if matches:
        names = " and ".join(("Chandra", *matches))
        if len(matches) == 2:
            names = "Chandra, Kuja and Shani"
        return PrimitiveOutcome(
            "fail",
            (f"Same-Rasi conjunction: {names} in {chandra.rashi}.",),
        )

    return PrimitiveOutcome(
        "pass",
        (
            (
                f"Chandra: {chandra.rashi}; Kuja: {kuja.rashi}; "
                f"Shani: {shani.rashi}; no same-Rasi conjunction."
            ),
        ),
    )


def aggregate_same_rasi_conjunction_window(
    samples: Sequence[PrimitiveOutcome],
    *,
    transition_complete: bool,
    budget_exhausted: bool,
) -> PrimitiveOutcome:
    """Combine sampled conjunction states using fail-closed precedence."""
    for sample in samples:
        if sample.status == "fail":
            return sample
    for sample in samples:
        if sample.status == "unknown":
            return sample
    if not samples:
        return PrimitiveOutcome("unknown", ("No sampled chart states are available.",))
    if budget_exhausted:
        return PrimitiveOutcome(
            "unknown",
            (
                (
                    "The chart-request budget was exhausted before this window's "
                    "coverage was complete."
                ),
            ),
        )
    if not transition_complete:
        return PrimitiveOutcome(
            "unknown",
            ("All sampled states pass, but Rasi-transition coverage is incomplete.",),
        )
    return PrimitiveOutcome(
        "pass",
        (
            (
                "Every sampled state resolves Chandra in a different Rasi from "
                "Kuja and Shani."
            ),
        ),
    )
