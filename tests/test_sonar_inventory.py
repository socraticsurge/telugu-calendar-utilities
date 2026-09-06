"""Tests for the deterministic Sonar code-smell inventory exporter."""

import csv
import io
from collections import Counter
from datetime import date

import pytest

from tools import export_sonar_inventory as inventory


def issue(key="one", **changes):
    payload = {
        "key": key,
        "rule": "python:S100",
        "severity": "CRITICAL",
        "component": "project:tools/example.py",
        "line": 12,
        "creationDate": "2026-09-01T10:00:00+0000",
        "type": "CODE_SMELL",
        "issueStatus": "OPEN",
    }
    payload.update(changes)
    return payload


def rows(*issues):
    return inventory.build_rows(
        {"total": len(issues), "issues": list(issues)},
        project_key="project",
        as_of=date(2026, 9, 6),
        ruff_counts={"tools/example.py": {"I001": 2}},
        complexity_hotspots={"tools/example.py": {"build": 14}},
    )


def test_build_rows_records_age_overlaps_scope_and_deterministic_order():
    actual = rows(
        issue("later", line=20, severity="MAJOR"),
        issue("first", line=12),
    )

    assert [row["issue_key"] for row in actual] == ["first", "later"]
    assert actual[0] == {
        "issue_key": "first",
        "rule": "python:S100",
        "severity": "CRITICAL",
        "file": "tools/example.py",
        "line": 12,
        "created_at": "2026-09-01",
        "age_days": 5,
        "ruff_overlap": "I001=2",
        "complexity_overlap": "build=14",
        "scope": "mutable",
    }


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"total": 2, "issues": [issue()]}, "total mismatch"),
        ({"total": 2, "issues": [issue(), issue()]}, "Duplicate Sonar issue"),
        (
            {"total": 1, "issues": [issue(component="project:../escape.py")]},
            "Unsafe Sonar component",
        ),
        ({"total": 1, "issues": [issue(issueStatus="CLOSED")]}, "unexpected status"),
        ({"total": 1, "issues": [issue(severity="UNKNOWN")]}, "unexpected severity"),
    ],
)
def test_build_rows_fails_closed_on_incomplete_or_unsafe_data(payload, message):
    with pytest.raises(inventory.InventoryError, match=message):
        inventory.build_rows(
            payload,
            project_key="project",
            as_of=date(2026, 9, 6),
            ruff_counts={},
            complexity_hotspots={},
        )


def test_parse_json_document_rejects_duplicate_keys_at_every_level():
    document = '{"total": 0, "issues": [], "issues": []}'

    with pytest.raises(inventory.InventoryError, match="Duplicate JSON key: issues"):
        inventory.parse_json_document(document, "test response")


def test_write_csv_uses_a_stable_schema_and_lf_line_endings(tmp_path):
    destination = tmp_path / "inventory.csv"
    inventory.write_csv(rows(issue()), destination)

    document = destination.read_text()
    parsed = list(csv.DictReader(io.StringIO(document)))
    assert tuple(parsed[0]) == inventory.CSV_FIELDS
    assert parsed[0]["issue_key"] == "one"
    assert "\r" not in document


def test_committed_snapshot_reconciles_counts_and_debt_overlaps():
    snapshot = (
        inventory.ROOT
        / "docs/tracking/2026-09-06-sonar-code-smell-inventory.csv"
    )
    with snapshot.open(encoding="utf-8", newline="") as stream:
        actual = list(csv.DictReader(stream))

    assert len(actual) == 455
    assert len({row["issue_key"] for row in actual}) == 455
    assert Counter(row["severity"] for row in actual) == {
        "CRITICAL": 125,
        "MAJOR": 221,
        "MINOR": 109,
    }
    assert Counter(row["scope"] for row in actual) == {
        "mutable": 447,
        "frozen-engine": 6,
        "frozen-ics": 2,
    }

    ruff_counts = inventory.read_json(inventory.RUFF_BASELINE)["counts"]
    complexity_hotspots = inventory.read_json(
        inventory.COMPLEXITY_BASELINE
    )["hotspots"]
    for row in actual:
        path = row["file"]
        assert row["ruff_overlap"] == inventory.format_overlap(
            ruff_counts.get(path, {})
        )
        assert row["complexity_overlap"] == inventory.format_overlap(
            complexity_hotspots.get(path, {})
        )


@pytest.mark.parametrize(
    "path, expected",
    [
        ("telugu_panchangam/engines/base.py", "frozen-engine"),
        ("telugu_panchangam/generators/ics.py", "frozen-ics"),
        (".github/workflows/ci.yml", "frozen-workflow"),
        ("src/main.ts", "mutable"),
    ],
)
def test_classify_scope_matches_the_working_agreement(path, expected):
    assert inventory.classify_scope(path) == expected
