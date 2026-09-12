import json
from copy import deepcopy
from pathlib import Path

from telugu_panchangam.personal.election_assessors.chart_geometry import (
    COURT_GURU_TRIKONA_METADATA,
    aggregate_court_guru_trikona_window,
    evaluate_court_guru_trikona,
)

ROOT = Path(__file__).resolve().parents[1]
ORACLE = json.loads(
    (
        Path(__file__).parent
        / "fixtures/election_chart_court_guru_trikona_oracle.json"
    ).read_text(encoding="utf-8")
)


def _chart(case):
    planets = deepcopy(ORACLE["base_planets"])
    guru = case.get("guru")
    if guru:
        next(item for item in planets if item["name"] == "Guru").update(guru)
    removed = set(case.get("remove", []))
    planets = [item for item in planets if item["name"] not in removed]
    duplicate = case.get("duplicate")
    if duplicate:
        planets.append(deepcopy(next(p for p in planets if p["name"] == duplicate)))
    return {"planets": planets}


def _actual(outcome):
    return {"status": outcome.status, "evidence": list(outcome.evidence)}


def test_fixture_is_explicitly_synthetic_not_a_source_golden():
    assert ORACLE["fixture_kind"] == "synthetic_contract_fixture"
    assert ORACLE["source_golden"] is False


def test_source_convention_and_integrated_preference_metadata_match_oracle():
    assert COURT_GURU_TRIKONA_METADATA == ORACLE["metadata"]
    assert COURT_GURU_TRIKONA_METADATA["source_statement"]["claim_id"] != (
        COURT_GURU_TRIKONA_METADATA["convention"]["method_claim_id"]
    )
    assert COURT_GURU_TRIKONA_METADATA["event_policy"]["status"] == (
        "implemented"
    )


def test_canonical_registry_and_provenance_support_the_metadata():
    registry = json.loads(
        (ROOT / "docs/reference/election-chart-interpretations.json").read_text(
            encoding="utf-8"
        )
    )
    convention = COURT_GURU_TRIKONA_METADATA["convention"]
    entry = registry["interpretations"][convention["id"]]
    assert convention["method_claim_id"] in entry["method_claims"]
    assert entry["implementation_status"] == "implemented"

    provenance = json.loads(
        (ROOT / "docs/reference/provenance.json").read_text(encoding="utf-8")
    )
    claims = {claim["id"] for claim in provenance["claims"]}
    assert COURT_GURU_TRIKONA_METADATA["source_statement"]["claim_id"] in claims
    assert convention["method_claim_id"] in claims


def test_snapshot_oracle_matches_python_predicate():
    for case in ORACLE["snapshot_cases"]:
        outcome = evaluate_court_guru_trikona(
            _chart(case),
            house_frame_uncertain=case.get("house_frame_uncertain", False),
        )
        assert _actual(outcome) == case["expected"], case["id"]


def test_window_oracle_matches_python_precedence():
    cases = {case["id"]: case for case in ORACLE["snapshot_cases"]}
    for window in ORACLE["window_cases"]:
        samples = [
            evaluate_court_guru_trikona(
                _chart(cases[case_id]),
                house_frame_uncertain=cases[case_id].get(
                    "house_frame_uncertain", False
                ),
            )
            for case_id in window["sample_case_ids"]
        ]
        outcome = aggregate_court_guru_trikona_window(
            samples, **window["coverage"]
        )
        assert _actual(outcome) == window["expected"], window["id"]
