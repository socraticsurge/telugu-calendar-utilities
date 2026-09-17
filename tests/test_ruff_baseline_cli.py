"""Exercise Ruff baseline command outcomes without altering repository debt."""

import json
import subprocess
import sys
from unittest.mock import Mock

import pytest

from tools import check_ruff_baseline as ruff


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr(ruff, "ROOT", tmp_path)
    monkeypatch.setattr(ruff, "BASELINE", tmp_path / "baseline.json")
    monkeypatch.setattr(sys, "argv", ["check_ruff_baseline.py"])
    return tmp_path


@pytest.mark.parametrize("returncode", [0, 1])
def test_scan_accepts_success_and_findings_exit_codes(monkeypatch, returncode):
    findings = [{"filename": str(ruff.ROOT / "sample.py"), "code": "F401"}]
    runner = Mock(return_value=subprocess.CompletedProcess(
        [], returncode, json.dumps(findings), ""
    ))
    monkeypatch.setattr(ruff.subprocess, "run", runner)

    assert ruff.run_ruff() == {"sample.py": {"F401": 1}}
    command = runner.call_args.args[0]
    assert command[:4] == [sys.executable, "-m", "ruff", "check"]
    assert command[4:8] == list(ruff.TARGETS)
    assert command[8:] == ["--select", "E,F,I", "--ignore", "E501", "--output-format", "json"]
    assert runner.call_args.kwargs == {
        "cwd": ruff.ROOT, "capture_output": True, "text": True,
    }


def test_scan_failure_reports_stderr_and_never_normalizes(monkeypatch, capsys):
    runner = Mock(return_value=subprocess.CompletedProcess([], 2, "[]", "scan failed\n"))
    monkeypatch.setattr(ruff.subprocess, "run", runner)

    with pytest.raises(RuntimeError, match="exit code 2"):
        ruff.run_ruff()
    assert capsys.readouterr().err == "scan failed\n"


def test_scan_rejects_malformed_json(monkeypatch):
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, "not JSON", ""))
    monkeypatch.setattr(ruff.subprocess, "run", runner)

    with pytest.raises(json.JSONDecodeError):
        ruff.run_ruff()


def test_findings_outside_repository_are_rejected(tmp_path):
    finding = {"filename": str(tmp_path.parent / "outside.py"), "code": "F401"}
    with pytest.raises(ValueError):
        ruff.count_findings([finding], root=tmp_path)


def test_missing_baseline_stops_before_scan(sandbox, monkeypatch, capsys):
    scan = Mock()
    monkeypatch.setattr(ruff, "run_ruff", scan)

    assert ruff.main() == 2
    assert "Missing Ruff debt baseline" in capsys.readouterr().err
    scan.assert_not_called()
    assert not ruff.BASELINE.exists()


def test_version_mismatch_stops_before_scan(sandbox, monkeypatch, capsys):
    ruff.BASELINE.write_text(json.dumps({"ruff_version": "wrong", "counts": {}}))
    scan = Mock()
    monkeypatch.setattr(ruff, "run_ruff", scan)

    assert ruff.main() == 2
    assert "Ruff version mismatch" in capsys.readouterr().err
    scan.assert_not_called()


@pytest.mark.parametrize("case", [({}, 0), ({"a.py": {"F401": 2}}, 2)])
def test_unchanged_baseline_passes_without_writing(sandbox, monkeypatch, capsys, case):
    counts, total = case
    ruff.write_baseline(counts)
    before = ruff.BASELINE.read_bytes()
    monkeypatch.setattr(ruff, "run_ruff", lambda: counts)

    assert ruff.main() == 0
    assert capsys.readouterr().out == f"Ruff debt baseline unchanged: {total} findings; no new debt.\n"
    assert ruff.BASELINE.read_bytes() == before


@pytest.mark.parametrize("actual", [{}, {"a.py": {"F401": 2}}])
def test_debt_change_fails_without_rewriting_baseline(sandbox, monkeypatch, capsys, actual):
    ruff.write_baseline({"a.py": {"F401": 1}})
    before = ruff.BASELINE.read_bytes()
    monkeypatch.setattr(ruff, "run_ruff", lambda: actual)

    assert ruff.main() == 1
    error = capsys.readouterr().err
    assert "Ruff debt changed:" in error
    assert "a.py F401: expected 1, found" in error
    assert "after reviewing intentional reductions" in error
    assert ruff.BASELINE.read_bytes() == before


def test_explicit_update_writes_versioned_deterministic_baseline(sandbox, monkeypatch, capsys):
    counts = {"z.py": {"I001": 1}, "a.py": {"F401": 2}}
    monkeypatch.setattr(ruff, "run_ruff", lambda: counts)
    monkeypatch.setattr(sys, "argv", ["check_ruff_baseline.py", "--update"])

    assert ruff.main() == 0
    payload = json.loads(ruff.BASELINE.read_text())
    assert payload["counts"] == counts
    assert payload["ruff_version"] == ruff.RUFF_VERSION
    assert ruff.BASELINE.read_text() == json.dumps(payload, indent=2, sort_keys=True) + "\n"
    assert capsys.readouterr().out == "Updated baseline.json\n"
