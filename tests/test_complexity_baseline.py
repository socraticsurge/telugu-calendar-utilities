"""Tests for the exact Ruff C901 complexity baseline."""

import json
from pathlib import Path

import pytest

from tools import check_complexity_baseline as complexity


def finding(
    root: Path,
    filename: str = "example.py",
    symbol: str = "evaluate",
    score: int = 12,
    threshold: int = 10,
    row: int = 5,
) -> dict[str, object]:
    return {
        "code": "C901",
        "filename": str(root / filename),
        "location": {"row": row, "column": 1},
        "message": f"`{symbol}` is too complex ({score} > {threshold})",
    }


def test_normalize_findings_extracts_scores_and_relative_posix_paths(tmp_path):
    actual = complexity.normalize_findings(
        [finding(tmp_path, "package/module.py", score=14)], root=tmp_path
    )

    assert actual == {"package/module.py": {"evaluate": 14}}


@pytest.mark.parametrize(
    "change, message",
    [
        ({"message": "complexity changed"}, "Unrecognized Ruff C901 message"),
        ({"message": "`evaluate` is too complex (12 > 9)"}, "threshold 9"),
        ({"code": "F401"}, "Unexpected Ruff rule"),
    ],
)
def test_normalize_findings_fails_closed_on_unexpected_output(tmp_path, change, message):
    raw_finding = finding(tmp_path)
    raw_finding.update(change)

    with pytest.raises(complexity.ComplexityBaselineError, match=message):
        complexity.normalize_findings([raw_finding], root=tmp_path)


def test_normalize_findings_rejects_paths_outside_repository(tmp_path):
    outside = tmp_path.parent / "outside.py"
    raw_finding = finding(tmp_path)
    raw_finding["filename"] = str(outside)

    with pytest.raises(complexity.ComplexityBaselineError, match="outside"):
        complexity.normalize_findings([raw_finding], root=tmp_path)


def test_normalize_findings_rejects_duplicate_file_symbol_identity(tmp_path):
    findings = [finding(tmp_path, row=5), finding(tmp_path, score=13, row=20)]

    with pytest.raises(complexity.ComplexityBaselineError, match="Duplicate") as exc:
        complexity.normalize_findings(findings, root=tmp_path)

    assert "'row': 5" in str(exc.value)
    assert "'row': 20" in str(exc.value)


def test_ruff_command_cannot_be_bypassed_by_config_noqa_or_gitignore():
    command = complexity.ruff_command("PYTHON")

    assert command[:4] == ["PYTHON", "-m", "ruff", "check"]
    assert "--isolated" in command
    assert "--ignore-noqa" in command
    assert "--no-respect-gitignore" in command
    assert "lint.mccabe.max-complexity=10" in command


def test_compare_hotspots_accepts_an_exact_baseline():
    baseline = {"example.py": {"evaluate": 12}}

    assert complexity.compare_hotspots(baseline, baseline) == []


def test_compare_hotspots_reports_every_kind_of_drift_deterministically():
    expected = {
        "changed.py": {"reduced": 15, "raised": 12},
        "missing.py": {"gone": 20},
    }
    actual = {
        "changed.py": {"reduced": 11, "raised": 13},
        "new.py": {"added": 14},
    }

    assert complexity.compare_hotspots(expected, actual) == [
        "changed.py::raised: expected 12, found 13",
        "changed.py::reduced: expected 15, found 11",
        "missing.py::gone: expected 20, missing",
        "new.py::added: new hotspot at 14",
    ]


@pytest.mark.parametrize(
    "change, message",
    [
        ({"ruff_version": "0.0.0"}, "ruff_version"),
        ({"max_complexity": 11}, "max_complexity"),
        ({"targets": ["elsewhere"]}, "targets"),
        ({"schema_version": 2}, "schema_version"),
        ({"hotspots": {"../escape.py": {"bad": 12}}}, "Invalid baseline path"),
    ],
)
def test_validate_baseline_rejects_incompatible_or_unsafe_data(change, message):
    payload = complexity.baseline_payload({"example.py": {"evaluate": 12}})
    payload.update(change)

    with pytest.raises(complexity.ComplexityBaselineError, match=message):
        complexity.validate_baseline(payload)


@pytest.mark.parametrize(
    "document, duplicate",
    [
        ('{"schema_version": 1, "schema_version": 1}', "schema_version"),
        ('{"hotspots": {"a.py": {}, "a.py": {}}}', "a.py"),
        ('{"hotspots": {"a.py": {"work": 11, "work": 12}}}', "work"),
    ],
)
def test_parse_json_document_rejects_duplicate_keys_at_every_level(
    document, duplicate
):
    with pytest.raises(complexity.ComplexityBaselineError, match="Duplicate") as exc:
        complexity.parse_json_document(document, "test document")

    assert duplicate in str(exc.value)


def test_baseline_serialization_is_deterministic(monkeypatch, tmp_path):
    destination = tmp_path / "complexity.json"
    monkeypatch.setattr(complexity, "BASELINE", destination)
    hotspots = {
        "z.py": {"second": 12},
        "a.py": {"first": 11},
    }

    complexity.write_baseline(hotspots)

    payload = json.loads(destination.read_text())
    assert payload == complexity.baseline_payload(hotspots)
    assert destination.read_text().endswith("\n")


def test_frozen_core_hotspots_remain_governed():
    payload = json.loads(complexity.BASELINE.read_text())

    assert payload["hotspots"]["telugu_panchangam/engines/base.py"] == {
        "_festivals": 22
    }
    assert payload["hotspots"]["telugu_panchangam/generators/ics.py"] == {
        "_description": 24
    }
