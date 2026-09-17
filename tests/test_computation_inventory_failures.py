"""Reject incomplete inventory evidence using isolated, real source fixtures."""

import json

import pytest

from tools import check_computation_inventory as inventory


@pytest.fixture
def candidate(monkeypatch, tmp_path):
    canonical = json.loads(inventory.REGISTRY_PATH.read_text())
    record = canonical["computations"][0]
    record["id"] = "sample.work"
    record["implementations"] = [{"path": "source/work.py", "symbol": "work", "role": "owner"}]
    record["tests"] = ["test_work.py"]
    record["provenance"]["claim_ids"] = []
    record["provenance"]["note"] = "Isolated validator fixture, not an astronomy claim."
    (tmp_path / "source").mkdir()
    (tmp_path / "source/work.py").write_text("def work():\n    return 1\n")
    (tmp_path / "test_work.py").write_text("def test_work():\n    assert True\n")
    provenance = tmp_path / "provenance.json"
    provenance.write_text('{"claims": []}')
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    monkeypatch.setattr(inventory, "PROVENANCE_PATH", provenance)
    return {
        "schema_version": 1,
        "vocabularies": canonical["vocabularies"],
        "computations": [record],
        "coverage": {"roots": [{"path": "source", "extensions": [".py"]}], "exclusions": []},
    }


def validate_candidate(candidate, tmp_path):
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate))
    return inventory.validate_registry(path)


def test_complete_fixture_passes(candidate, tmp_path):
    assert validate_candidate(candidate, tmp_path) == []


@pytest.mark.parametrize("case", [
    ("schema_version", 2, "schema_version must be 1"),
    ("vocabularies", None, "vocabularies must be an object"),
    ("vocabularies", {}, "missing vocabularies:"),
    ("computations", [], "computations must be a non-empty list"),
    ("computations", [None], "computations[0] must be an object"),
    ("coverage", None, "coverage must be an object"),
    ("coverage", {}, "coverage.exclusions must be a list"),
])
def test_invalid_registry_structure(candidate, tmp_path, case):
    field, value, message = case
    candidate[field] = value
    assert any(message in error for error in validate_candidate(candidate, tmp_path))


@pytest.mark.parametrize("case", [
    ("id", "Not stable", "not a stable identifier"),
    ("title", " ", ".title must be a non-empty string"),
    ("owning_layer", "unknown", ".owning_layer is outside"),
    ("claim_kind", "unknown", ".claim_kind is outside"),
    ("inputs", [], ".inputs must be a non-empty string list"),
    ("surfaces", ["unknown"], ".surfaces contains unknown value"),
    ("method", [], ".method must be an object"),
    ("implementations", [], ".implementations must be a non-empty list"),
    ("implementations", [None], ".implementations[0] must be an object"),
    ("tests", None, ".tests must be a string list"),
    ("tests", [], "needs at least one test or a visible test_gap"),
    ("tests", ["../outside.py"], "tests path must be repository-relative"),
    ("tests", ["missing.py"], "tests path does not exist"),
    ("provenance", None, ".provenance must be an object"),
])
def test_invalid_record_fields(candidate, tmp_path, case):
    field, value, message = case
    candidate["computations"][0][field] = value
    assert any(message in error for error in validate_candidate(candidate, tmp_path))


def test_missing_field_is_reported(candidate, tmp_path):
    del candidate["computations"][0]["summary"]
    assert "sample.work: missing fields: summary" in validate_candidate(candidate, tmp_path)


def test_duplicate_identity_is_reported(candidate, tmp_path):
    candidate["computations"].append(candidate["computations"][0])
    assert "duplicate computation id: sample.work" in validate_candidate(candidate, tmp_path)


def test_empty_vocabulary_is_rejected(candidate, tmp_path):
    candidate["vocabularies"]["surfaces"] = []
    assert "vocabularies.surfaces must be a non-empty string list" in validate_candidate(candidate, tmp_path)


@pytest.mark.parametrize("case", [
    ("kind", "unknown", ".method.kind is unknown"),
    ("summary", "", ".method.summary must be a non-empty string"),
    ("steps", [], ".method.steps must be a non-empty string list"),
    ("notes", [], ".method.notes must be a non-empty string list"),
    ("formulae", None, ".method.formulae must be a list"),
    ("formulae", [None], ".method.formulae[0] must be an object"),
    ("formulae", [{}], ".method.formulae[0].name must be a non-empty string"),
    ("worked_examples", [None], ".method.worked_examples[0] must be an object"),
    ("worked_examples", [{}], ".method.worked_examples[0].label must be a non-empty string"),
])
def test_unreproducible_method_is_rejected(candidate, tmp_path, case):
    field, value, message = case
    candidate["computations"][0]["method"][field] = value
    assert any(message in error for error in validate_candidate(candidate, tmp_path))


def test_formula_method_requires_formulae(candidate, tmp_path):
    candidate["computations"][0]["method"].update(kind="formula", formulae=[])
    assert "sample.work.method.formulae is required for formula methods" in validate_candidate(candidate, tmp_path)


@pytest.mark.parametrize("case", [
    ("role", "unknown", ".role is unknown"),
    ("path", "", ".path must be a non-empty string"),
    ("path", "../outside.py", ".path must be repository-relative"),
    ("path", "/outside.py", ".path must be repository-relative"),
    ("path", "missing.py", ".path does not exist"),
    ("symbol", "", ".symbol must be a non-empty string"),
    ("symbol", "missing", ".symbol not found"),
])
def test_invalid_implementation_location(candidate, tmp_path, case):
    field, value, message = case
    candidate["computations"][0]["implementations"][0][field] = value
    assert any(message in error for error in validate_candidate(candidate, tmp_path))


def test_missing_owner_is_reported(candidate, tmp_path):
    candidate["computations"][0]["implementations"][0]["role"] = "mirror"
    assert "sample.work must have at least one owner implementation" in validate_candidate(candidate, tmp_path)


@pytest.mark.parametrize("case", [
    ("evidence_classes", [], ".evidence_classes must be non-empty"),
    ("verification_states", ["unknown"], ".verification_states contains unknown values"),
    ("claim_ids", None, ".claim_ids must be a string list"),
    ("claim_ids", ["unknown"], "unknown provenance claim id: unknown"),
    ("note", "", "provenance without claim_ids needs a note"),
])
def test_missing_or_unknown_evidence(candidate, tmp_path, case):
    field, value, message = case
    candidate["computations"][0]["provenance"][field] = value
    assert any(message in error for error in validate_candidate(candidate, tmp_path))


def test_explicit_test_gap_is_accepted(candidate, tmp_path):
    candidate["computations"][0].update(tests=[], test_gap="Missing independent reference fixture.")
    assert validate_candidate(candidate, tmp_path) == []


@pytest.mark.parametrize("text", ["[]", "not JSON"])
def test_unreadable_provenance_is_not_silently_ignored(candidate, tmp_path, text):
    inventory.PROVENANCE_PATH.write_text(text)
    assert any("cannot load provenance registry" in error for error in validate_candidate(candidate, tmp_path))


@pytest.mark.parametrize("text", ["[]", "not JSON"])
def test_invalid_registry_document_returns_errors(candidate, tmp_path, text):
    path = tmp_path / "invalid.json"
    path.write_text(text)
    assert inventory.validate_registry(path)


def test_missing_registry_returns_errors(candidate, tmp_path):
    errors = inventory.validate_registry(tmp_path / "absent.json")
    assert len(errors) == 1
    assert "absent.json" in errors[0]


@pytest.mark.parametrize("exclusion,message", [
    (None, "must be an object"),
    ({"path": ""}, ".path must be a non-empty string"),
    ({"path": "missing.py", "kind": "unknown", "reason": ""}, ".kind is unknown"),
    ({"path": "source/work.py", "kind": "unknown", "reason": ""}, "both implemented and excluded"),
])
def test_invalid_coverage_exclusion(candidate, tmp_path, exclusion, message):
    candidate["coverage"]["exclusions"] = [exclusion]
    assert any(message in error for error in validate_candidate(candidate, tmp_path))


def test_exclusion_diagnostics_are_accumulated(candidate, tmp_path):
    exclusion = {"path": "missing.py", "kind": "unknown", "reason": ""}
    candidate["coverage"]["exclusions"] = [exclusion, exclusion]
    errors = validate_candidate(candidate, tmp_path)
    assert "duplicate coverage exclusion: missing.py" in errors
    assert "coverage.exclusions[0].reason must be a non-empty string" in errors
    assert "coverage.exclusions[0].path does not exist: missing.py" in errors
    assert "exclusions outside coverage roots: missing.py" in errors


def test_unclassified_source_is_reported(candidate, tmp_path):
    (tmp_path / "source/new.py").write_text("value = 1\n")
    assert "unclassified production source paths: source/new.py" in validate_candidate(candidate, tmp_path)


@pytest.mark.parametrize("root", [None, {}, {"path": "missing", "extensions": [".py"]}])
def test_invalid_or_absent_coverage_roots_yield_no_files(root):
    assert inventory._coverage_root_paths(root) == set()


def test_python_symbol_collection_handles_classes_and_annotations(tmp_path):
    path = tmp_path / "example.py"
    path.write_text("VALUE: int = 1\nclass Example:\n    async def work(self):\n        pass\n")
    assert inventory._source_symbols(path) == {"VALUE", "Example", "Example.work"}


def test_unsupported_source_has_no_symbols(tmp_path):
    path = tmp_path / "example.txt"
    path.write_text("not executable code")
    assert inventory._source_symbols(path) == set()


def test_cli_prints_each_validation_error(monkeypatch, capsys):
    monkeypatch.setattr(inventory, "validate_registry", lambda: ["first failure", "second failure"])
    assert inventory.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "ERROR: first failure\nERROR: second failure\n"


def test_cli_reports_valid_inventory_counts(candidate, tmp_path, monkeypatch, capsys):
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate))
    validate = inventory.validate_registry
    monkeypatch.setattr(inventory, "REGISTRY_PATH", path)
    monkeypatch.setattr(inventory, "validate_registry", lambda: validate(path))
    assert inventory.main() == 0
    assert capsys.readouterr().out == (
        "Computation inventory valid: 1 records, 1 implementations, "
        "1 audited source files, 1/1 methods documented.\n"
    )
