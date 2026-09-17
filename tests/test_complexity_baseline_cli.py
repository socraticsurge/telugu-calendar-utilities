"""Failure-path and CLI contracts for the exact complexity baseline."""

import json
import subprocess
import sys
from unittest.mock import Mock

import pytest

from tools import check_complexity_baseline as complexity


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr(complexity, "ROOT", tmp_path)
    monkeypatch.setattr(complexity, "BASELINE", tmp_path / "baseline.json")
    monkeypatch.setattr(sys, "argv", ["check_complexity_baseline.py"])
    return tmp_path


@pytest.mark.parametrize("returncode", [0, 1])
def test_scan_accepts_supported_exit_codes(monkeypatch, returncode):
    runner = Mock(return_value=subprocess.CompletedProcess([], returncode, "[]", ""))
    monkeypatch.setattr(complexity.subprocess, "run", runner)

    assert complexity.run_ruff() == {}
    runner.assert_called_once_with(
        complexity.ruff_command(), cwd=complexity.ROOT, capture_output=True, text=True
    )


@pytest.mark.parametrize("stderr", ["", "scan failed\n"])
def test_scan_failure_cannot_be_treated_as_empty_findings(monkeypatch, capsys, stderr):
    runner = Mock(return_value=subprocess.CompletedProcess([], 2, "[]", stderr))
    monkeypatch.setattr(complexity.subprocess, "run", runner)

    with pytest.raises(complexity.ComplexityBaselineError, match="exit code 2"):
        complexity.run_ruff()
    assert capsys.readouterr().err == stderr


@pytest.mark.parametrize("output,message", [
    ("broken JSON", "malformed JSON"),
    ('{"findings": []}', "must be a list"),
])
def test_scan_rejects_untrustworthy_output(monkeypatch, output, message):
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, output, ""))
    monkeypatch.setattr(complexity.subprocess, "run", runner)

    with pytest.raises(complexity.ComplexityBaselineError, match=message):
        complexity.run_ruff()


@pytest.mark.parametrize("payload,message", [
    ([], "must be a JSON object"),
    ({"hotspots": []}, "hotspots must be an object"),
    ({"hotspots": {"a.py": {}}}, "non-empty object"),
    ({"hotspots": {"a.py": []}}, "non-empty object"),
    ({"hotspots": {"/absolute.py": {"work": 11}}}, "Invalid baseline path"),
    ({"hotspots": {"a//b.py": {"work": 11}}}, "Invalid baseline path"),
    ({"hotspots": {2: {"work": 11}}}, "Invalid baseline path"),
    ({"hotspots": {"a.py": {"": 11}}}, "Invalid symbol"),
    ({"hotspots": {"a.py": {2: 11}}}, "Invalid symbol"),
])
def test_invalid_baseline_shapes_are_rejected(payload, message):
    candidate = complexity.baseline_payload({})
    if isinstance(payload, dict):
        candidate.update(payload)
    else:
        candidate = payload
    with pytest.raises(complexity.ComplexityBaselineError, match=message):
        complexity.validate_baseline(candidate)


@pytest.mark.parametrize("score", [True, "11", 11.5, 10, -1, None])
def test_invalid_scores_cannot_enter_baseline(score):
    candidate = complexity.baseline_payload({"a.py": {"work": score}})
    with pytest.raises(complexity.ComplexityBaselineError, match="Invalid complexity"):
        complexity.validate_baseline(candidate)


def test_valid_scores_round_trip_through_disk(sandbox):
    hotspots = {"z.py": {"work": 12}, "a.py": {"other": 11}}
    complexity.write_baseline(hotspots)
    assert complexity.load_baseline() == hotspots
    assert list(complexity.load_baseline()) == ["a.py", "z.py"]


def test_missing_baseline_returns_error_not_success(sandbox, monkeypatch, capsys):
    monkeypatch.setattr(complexity, "run_ruff", lambda: {})
    assert complexity.main() == 2
    assert "Missing complexity baseline" in capsys.readouterr().err
    assert not complexity.BASELINE.exists()


def test_corrupt_baseline_returns_error_without_rewrite(sandbox, monkeypatch, capsys):
    complexity.BASELINE.write_text("not JSON")
    monkeypatch.setattr(complexity, "run_ruff", lambda: {})
    assert complexity.main() == 2
    assert "malformed JSON" in capsys.readouterr().err
    assert complexity.BASELINE.read_text() == "not JSON"


@pytest.mark.parametrize("case", [
    ({}, 0, 0), ({"a.py": {"work": 12}}, 1, 12),
])
def test_unchanged_baseline_passes(sandbox, monkeypatch, capsys, case):
    hotspots, count, maximum = case
    complexity.write_baseline(hotspots)
    before = complexity.BASELINE.read_bytes()
    monkeypatch.setattr(complexity, "run_ruff", lambda: hotspots)
    assert complexity.main() == 0
    assert capsys.readouterr().out == (
        f"Complexity baseline unchanged: {count} hotspots; maximum {maximum}.\n"
    )
    assert complexity.BASELINE.read_bytes() == before


def test_changed_debt_fails_without_rewriting_baseline(sandbox, monkeypatch, capsys):
    complexity.write_baseline({"a.py": {"work": 12}})
    before = complexity.BASELINE.read_bytes()
    monkeypatch.setattr(complexity, "run_ruff", lambda: {"a.py": {"work": 13}})
    assert complexity.main() == 1
    error = capsys.readouterr().err
    assert "a.py::work: expected 12, found 13" in error
    assert "Review the change" in error
    assert complexity.BASELINE.read_bytes() == before


def test_explicit_update_writes_reviewed_scores(sandbox, monkeypatch, capsys):
    hotspots = {"a.py": {"work": 11}}
    monkeypatch.setattr(complexity, "run_ruff", lambda: hotspots)
    monkeypatch.setattr(sys, "argv", ["check_complexity_baseline.py", "--update"])
    assert complexity.main() == 0
    assert json.loads(complexity.BASELINE.read_text()) == complexity.baseline_payload(hotspots)
    assert capsys.readouterr().out == "Updated baseline.json\n"
