"""Tests for the ratcheted Ruff debt baseline."""

from tools.check_ruff_baseline import compare_counts, count_findings


def test_count_findings_groups_by_file_and_rule():
    findings = [
        {"code": "I001", "filename": "/repo/example.py"},
        {"code": "I001", "filename": "/repo/example.py"},
        {"code": "F401", "filename": "/repo/example.py"},
    ]

    assert count_findings(findings, root="/repo") == {
        "example.py": {"F401": 1, "I001": 2}
    }


def test_compare_counts_accepts_an_exact_baseline():
    baseline = {"example.py": {"I001": 2}}

    assert compare_counts(baseline, baseline) == []


def test_compare_counts_rejects_new_or_stale_debt():
    expected = {"example.py": {"I001": 1}, "fixed.py": {"F401": 1}}
    actual = {"example.py": {"I001": 2}, "new.py": {"E701": 1}}

    assert compare_counts(expected, actual) == [
        "example.py I001: expected 1, found 2",
        "fixed.py F401: expected 1, found 0",
        "new.py E701: expected 0, found 1",
    ]
