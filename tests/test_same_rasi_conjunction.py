import json
from copy import deepcopy
from pathlib import Path

from telugu_panchangam.personal.election_assessors.conjunction import (
    SAME_RASI_CONJUNCTION_METADATA,
    aggregate_same_rasi_conjunction_window,
    evaluate_same_rasi_chandra_conjunction,
)
from telugu_panchangam.personal.election_assessors.event_admission import (
    planet_positions,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (
        Path(__file__).parent
        / "fixtures/election_chart_same_rasi_conjunction_oracle.json"
    ).read_text(encoding="utf-8")
)


def _chart(case):
    planets = deepcopy(ORACLE["base_planets"])
    overrides = case.get("overrides", {})
    for planet in planets:
        planet.update(overrides.get(planet["name"], {}))
    removed = set(case.get("remove", []))
    planets = [planet for planet in planets if planet["name"] not in removed]
    duplicate = case.get("duplicate")
    if duplicate:
        planets.append(deepcopy(next(p for p in planets if p["name"] == duplicate)))
    conflict = case.get("conflict")
    if conflict:
        replaced = next(p for p in planets if p["name"] == conflict["replace"])
        replaced.update(name=conflict["name"], rashi=conflict["rashi"])
    return {"planets": planets}


def _actual(outcome):
    return {"status": outcome.status, "evidence": list(outcome.evidence)}


def test_source_convention_and_unwired_event_policy_metadata_match_oracle():
    assert SAME_RASI_CONJUNCTION_METADATA == ORACLE["metadata"]
    assert (
        SAME_RASI_CONJUNCTION_METADATA["source_statement"]["claim_id"]
        != (SAME_RASI_CONJUNCTION_METADATA["convention"]["method_claim_id"])
    )
    assert SAME_RASI_CONJUNCTION_METADATA["event_policy"]["status"] == (
        "specified_unwired"
    )


def test_registry_and_provenance_record_implemented_but_unwired_boundary():
    registry = json.loads(
        (ROOT / "docs/reference/election-chart-interpretations.json").read_text(
            encoding="utf-8"
        )
    )
    entry = registry["interpretations"][
        SAME_RASI_CONJUNCTION_METADATA["convention"]["id"]
    ]
    assert entry["source_claims"] == [
        SAME_RASI_CONJUNCTION_METADATA["source_statement"]["claim_id"]
    ]
    assert entry["method_claims"] == [
        SAME_RASI_CONJUNCTION_METADATA["convention"]["method_claim_id"]
    ]
    assert entry["event_policy_claims"] == [
        SAME_RASI_CONJUNCTION_METADATA["event_policy"]["decision_claim_id"]
    ]
    assert entry["implementation_status"] == "implemented"
    assert entry["event_wiring_status"] == "specified_unwired"
    assert set(entry["implementation"]) == {
        "telugu_panchangam/personal/election_assessors/conjunction.py",
        "src/scorer/election-assessors/conjunction.ts",
    }

    provenance = json.loads(
        (ROOT / "docs/reference/provenance.json").read_text(encoding="utf-8")
    )
    claims = {claim["id"] for claim in provenance["claims"]}
    assert {
        SAME_RASI_CONJUNCTION_METADATA["source_statement"]["claim_id"],
        SAME_RASI_CONJUNCTION_METADATA["convention"]["method_claim_id"],
        SAME_RASI_CONJUNCTION_METADATA["event_policy"]["decision_claim_id"],
    } <= claims


def test_snapshot_oracle_matches_python_primitive():
    for case in ORACLE["snapshot_cases"]:
        outcome = evaluate_same_rasi_chandra_conjunction(planet_positions(_chart(case)))
        assert _actual(outcome) == case["expected"], case["id"]


def test_window_oracle_matches_python_precedence():
    cases = {case["id"]: case for case in ORACLE["snapshot_cases"]}
    for window in ORACLE["window_cases"]:
        samples = [
            evaluate_same_rasi_chandra_conjunction(
                planet_positions(_chart(cases[case_id]))
            )
            for case_id in window["sample_case_ids"]
        ]
        outcome = aggregate_same_rasi_conjunction_window(
            samples,
            transition_complete=window["transition_complete"],
            budget_exhausted=window["budget_exhausted"],
        )
        assert _actual(outcome) == window["expected"], window["id"]
