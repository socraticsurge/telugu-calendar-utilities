#!/usr/bin/env python3
"""Export a deterministic Sonar code-smell inventory with debt overlaps."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
RUFF_BASELINE = ROOT / "tools/ruff_baseline.json"
COMPLEXITY_BASELINE = ROOT / "tools/complexity_baseline.json"
SEVERITY_ORDER = {"BLOCKER": 0, "CRITICAL": 1, "MAJOR": 2, "MINOR": 3, "INFO": 4}
OPEN_STATUSES = {"OPEN", "CONFIRMED"}
CSV_FIELDS = (
    "issue_key",
    "rule",
    "severity",
    "file",
    "line",
    "created_at",
    "age_days",
    "ruff_overlap",
    "complexity_overlap",
    "scope",
)


class InventoryError(ValueError):
    """Raised when the source data cannot support an exact inventory."""


def _reject_duplicate_keys(pairs: Iterable[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json_document(document: str, source: str) -> dict[str, object]:
    """Parse JSON while rejecting duplicate object keys at every level."""
    try:
        payload = json.loads(document, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, InventoryError) as error:
        raise InventoryError(f"Invalid {source}: {error}") from error
    if not isinstance(payload, dict):
        raise InventoryError(f"Invalid {source}: top level must be an object")
    return payload


def read_json(path: Path) -> dict[str, object]:
    return parse_json_document(path.read_text(encoding="utf-8"), str(path))


def repository_path(value: Path, label: str) -> Path:
    """Resolve a CLI path while preventing access outside the repository."""
    try:
        resolved = (ROOT / value).resolve()
        resolved.relative_to(ROOT)
    except (OSError, RuntimeError, ValueError) as error:
        raise InventoryError(f"Unsafe {label} path: {value}") from error
    return resolved


def _relative_component(component: object, project_key: str) -> str:
    prefix = f"{project_key}:"
    if not isinstance(component, str) or not component.startswith(prefix):
        raise InventoryError(f"Unexpected Sonar component: {component!r}")
    relative = component.removeprefix(prefix)
    path = PurePosixPath(relative)
    if path.is_absolute() or not relative or ".." in path.parts:
        raise InventoryError(f"Unsafe Sonar component path: {relative!r}")
    return path.as_posix()


def _created_date(value: object) -> date:
    if not isinstance(value, str):
        raise InventoryError(f"Invalid creationDate: {value!r}")
    normalized = value.replace("Z", "+00:00")
    if len(normalized) >= 5 and normalized[-5] in "+-" and normalized[-4:].isdigit():
        normalized = f"{normalized[:-2]}:{normalized[-2:]}"
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError as error:
        raise InventoryError(f"Invalid creationDate: {value!r}") from error


def format_overlap(values: Mapping[str, object]) -> str:
    return ";".join(f"{key}={values[key]}" for key in sorted(values))


def classify_scope(path: str) -> str:
    """Map a repository path to its working-agreement change boundary."""
    if path.startswith("telugu_panchangam/engines/"):
        return "frozen-engine"
    if path == "telugu_panchangam/generators/ics.py":
        return "frozen-ics"
    if path.startswith(".github/workflows/"):
        return "frozen-workflow"
    return "mutable"


def _complete_issues(payload: Mapping[str, object]) -> list[object]:
    issues = payload.get("issues")
    if not isinstance(issues, list):
        raise InventoryError("Sonar response is missing an issues list")
    if payload.get("total") != len(issues):
        raise InventoryError(
            f"Sonar total mismatch: declared {payload.get('total')!r}, received {len(issues)}"
        )
    return issues


def _issue_key(issue: Mapping[str, object], seen: set[str]) -> str:
    key = issue.get("key")
    if not isinstance(key, str) or not key:
        raise InventoryError(f"Invalid issue key: {key!r}")
    if key in seen:
        raise InventoryError(f"Duplicate Sonar issue key: {key}")
    seen.add(key)
    return key


def _severity(issue: Mapping[str, object], key: str) -> str:
    severity = issue.get("severity")
    if severity not in SEVERITY_ORDER:
        raise InventoryError(f"{key}: unexpected severity {severity!r}")
    return str(severity)


def _line(issue: Mapping[str, object], key: str) -> int | str:
    line = issue.get("line", "")
    if line != "" and (not isinstance(line, int) or line < 1):
        raise InventoryError(f"{key}: invalid line {line!r}")
    return line


def _validate_kind(issue: Mapping[str, object], key: str) -> None:
    if issue.get("type") != "CODE_SMELL":
        raise InventoryError(f"{key}: unexpected type {issue.get('type')!r}")
    status = issue.get("issueStatus", issue.get("status"))
    if status not in OPEN_STATUSES:
        raise InventoryError(f"{key}: unexpected status {status!r}")


def _normalize_issue(
    issue: object,
    *,
    seen: set[str],
    project_key: str,
    as_of: date,
    ruff_counts: Mapping[str, Mapping[str, object]],
    complexity_hotspots: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if not isinstance(issue, dict):
        raise InventoryError("Every Sonar issue must be an object")
    key = _issue_key(issue, seen)
    _validate_kind(issue, key)
    severity = _severity(issue, key)
    path = _relative_component(issue.get("component"), project_key)
    created = _created_date(issue.get("creationDate"))
    age_days = (as_of - created).days
    if age_days < 0:
        raise InventoryError(f"{key}: creation date is after the inventory date")

    return {
        "issue_key": key,
        "rule": issue.get("rule", ""),
        "severity": severity,
        "file": path,
        "line": _line(issue, key),
        "created_at": created.isoformat(),
        "age_days": age_days,
        "ruff_overlap": format_overlap(ruff_counts.get(path, {})),
        "complexity_overlap": format_overlap(complexity_hotspots.get(path, {})),
        "scope": classify_scope(path),
    }


def build_rows(
    payload: Mapping[str, object],
    *,
    project_key: str,
    as_of: date,
    ruff_counts: Mapping[str, Mapping[str, object]],
    complexity_hotspots: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    """Validate and normalize a complete Sonar issues response."""
    seen: set[str] = set()
    rows = [
        _normalize_issue(
            issue,
            seen=seen,
            project_key=project_key,
            as_of=as_of,
            ruff_counts=ruff_counts,
            complexity_hotspots=complexity_hotspots,
        )
        for issue in _complete_issues(payload)
    ]

    return sorted(
        rows,
        key=lambda row: (
            SEVERITY_ORDER[str(row["severity"])],
            str(row["file"]),
            int(row["line"]) if row["line"] != "" else 0,
            str(row["rule"]),
            str(row["issue_key"]),
        ),
    )


def write_csv(rows: Sequence[Mapping[str, object]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--project-key", default="socraticsurge_telugu-calendar-utilities")
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = repository_path(args.source, "source")
    output = repository_path(args.output, "output")
    payload = read_json(source)
    ruff_counts = read_json(RUFF_BASELINE)["counts"]
    complexity_hotspots = read_json(COMPLEXITY_BASELINE)["hotspots"]
    if not isinstance(ruff_counts, dict) or not isinstance(complexity_hotspots, dict):
        raise InventoryError("Debt baseline structure is invalid")
    rows = build_rows(
        payload,
        project_key=args.project_key,
        as_of=args.as_of,
        ruff_counts=ruff_counts,
        complexity_hotspots=complexity_hotspots,
    )
    write_csv(rows, output)
    print(f"Exported {len(rows)} unique open code smells to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
