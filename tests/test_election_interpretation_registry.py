import json
import re
from pathlib import Path

from telugu_panchangam.personal.election_assessors.conventions import (
    ELECTION_CHART_CONVENTION_SCHEMA_VERSION,
    ELECTION_CHART_CONVENTIONS,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "docs/reference/election-chart-interpretations.json").read_text(
        encoding="utf-8"
    )
)
ELECTION_CHART_INTERPRETATION_SCHEMA_VERSION = REGISTRY["schema_version"]
ELECTION_CHART_INTERPRETATIONS = REGISTRY["interpretations"]
ELECTION_CHART_APPLIED_CONVENTION_INTERPRETATIONS = REGISTRY[
    "applied_convention_interpretations"
]
REQUIRED_CONCEPTS = {
    "aspect",
    "conjunction",
    "benefic_malefic",
    "dignity",
    "strength",
    "fortification",
    "affliction",
    "combustion",
    "waxing_waning_chandra",
    "lord_relationships",
    "navamsa",
    "hemming",
    "named_yoga",
}
REQUIRED_FIELDS = {
    "schema_version",
    "concept",
    "label",
    "status",
    "source_claims",
    "method_claims",
    "inputs",
    "formula",
    "thresholds",
    "precedence",
    "conflict_resolution",
    "alternatives",
    "implementation",
    "implementation_status",
    "delivery_issues",
}


def _provenance():
    ledger = json.loads(
        (ROOT / "docs/reference/provenance.json").read_text(encoding="utf-8")
    )
    return {claim["id"]: claim for claim in ledger["claims"]}


def test_registry_covers_every_foundation_concept_with_stable_ids():
    concepts = {entry["concept"] for entry in ELECTION_CHART_INTERPRETATIONS.values()}
    assert REQUIRED_CONCEPTS <= concepts
    assert len(ELECTION_CHART_INTERPRETATIONS) == len(
        set(ELECTION_CHART_INTERPRETATIONS)
    )
    for convention_id, entry in ELECTION_CHART_INTERPRETATIONS.items():
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*-v\d+", convention_id)
        assert set(entry) >= REQUIRED_FIELDS
        assert entry["schema_version"] == ELECTION_CHART_INTERPRETATION_SCHEMA_VERSION
        assert entry["status"] in {"selected", "unresolved"}
        assert entry["implementation_status"] in {
            "implemented",
            "partial",
            "specified_unwired",
            "unresolved",
        }
        assert entry["inputs"]
        assert entry["precedence"]
        assert entry["conflict_resolution"]
        assert isinstance(entry["thresholds"], dict)
        assert isinstance(entry["alternatives"], list)
        assert all(
            "id" in alternative and "status" in alternative
            for alternative in entry["alternatives"]
        )
        if entry["status"] == "selected":
            assert entry["formula"]
        else:
            assert entry["formula"] is None
            assert entry["method_claims"] == []
            assert entry["implementation"] == []
            assert entry["implementation_status"] == "unresolved"
            assert entry["unresolved_reason"]


def test_required_concepts_have_exact_textual_source_locators():
    claims = _provenance()
    for entry in ELECTION_CHART_INTERPRETATIONS.values():
        if entry["concept"] not in REQUIRED_CONCEPTS:
            continue
        assert entry["source_claims"], entry["concept"]
        for claim_id in entry["source_claims"]:
            claim = claims[claim_id]
            assert claim["evidence_class"] == "textual"
            assert claim["source_ids"]
            assert claim["locator"].strip()
            assert claim["verification_state"] in {"verified", "contradicted"}


def test_method_claims_are_separate_registered_project_conventions():
    claims = _provenance()
    for entry in ELECTION_CHART_INTERPRETATIONS.values():
        for claim_id in entry["method_claims"]:
            claim = claims[claim_id]
            assert claim["evidence_class"] == "project_heuristic"
            assert claim["locator"].strip()


def test_applied_conventions_reference_canonical_interpretations():
    registered = set(ELECTION_CHART_INTERPRETATIONS)
    assert ELECTION_CHART_CONVENTION_SCHEMA_VERSION == 3
    assert set(ELECTION_CHART_APPLIED_CONVENTION_INTERPRETATIONS) == set(
        ELECTION_CHART_CONVENTIONS
    )
    for (
        interpretation_ids
    ) in ELECTION_CHART_APPLIED_CONVENTION_INTERPRETATIONS.values():
        assert interpretation_ids
        assert set(interpretation_ids) <= registered


def test_generated_browser_contract_contains_exact_registry_parity():
    payload = json.loads(
        (ROOT / "src/data/election-chart-interpretations.generated.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["schema_version"] == ELECTION_CHART_INTERPRETATION_SCHEMA_VERSION
    assert payload["interpretations"] == ELECTION_CHART_INTERPRETATIONS
    assert payload["applied_convention_interpretations"] == (
        ELECTION_CHART_APPLIED_CONVENTION_INTERPRETATIONS
    )


def test_registry_is_in_the_published_documentation_data_contract():
    filename = "'election-chart-interpretations.json'"
    assert filename in (ROOT / "tools/compose-docs-data.mjs").read_text(
        encoding="utf-8"
    )
    assert filename in (ROOT / "tools/check-docs-output.mjs").read_text(
        encoding="utf-8"
    )
