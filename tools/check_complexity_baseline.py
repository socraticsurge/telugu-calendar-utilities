#!/usr/bin/env python3
"""Reject unreviewed changes to the repository's complexity hotspots."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "tools/complexity_baseline.json"
TARGETS = ("telugu_panchangam", "tests", "tools", "scripts")
MAX_COMPLEXITY = 10
RUFF_VERSION = version("ruff")
SCHEMA_VERSION = 1
MESSAGE_PATTERN = re.compile(
    r"^`(?P<symbol>[^`]+)` is too complex "
    r"\((?P<complexity>\d+) > (?P<threshold>\d+)\)$"
)


class ComplexityBaselineError(ValueError):
    """The baseline or Ruff output cannot be trusted."""


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ComplexityBaselineError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def parse_json_document(text: str, source: str) -> object:
    """Parse JSON without allowing duplicate keys to hide data."""
    try:
        return json.loads(text, object_pairs_hook=_unique_json_object)
    except json.JSONDecodeError as exc:
        raise ComplexityBaselineError(f"{source} contains malformed JSON.") from exc


def _relative_filename(filename: object, root: str | Path) -> str:
    root_path = Path(root).resolve()
    try:
        relative = Path(str(filename)).resolve().relative_to(root_path)
    except ValueError as exc:
        raise ComplexityBaselineError(
            f"Ruff reported a path outside the repository: {filename}"
        ) from exc
    return relative.as_posix()


def _parse_finding(finding: Mapping[str, object], root: str | Path) -> tuple[str, str, int]:
    if finding.get("code") != "C901":
        raise ComplexityBaselineError(
            f"Unexpected Ruff rule in complexity scan: {finding.get('code')!r}"
        )
    match = MESSAGE_PATTERN.fullmatch(str(finding.get("message", "")))
    if match is None:
        raise ComplexityBaselineError(
            f"Unrecognized Ruff C901 message: {finding.get('message')!r}"
        )
    threshold = int(match.group("threshold"))
    if threshold != MAX_COMPLEXITY:
        raise ComplexityBaselineError(
            f"Ruff used complexity threshold {threshold}; expected {MAX_COMPLEXITY}."
        )
    return (
        _relative_filename(finding.get("filename"), root),
        match.group("symbol"),
        int(match.group("complexity")),
    )


def normalize_findings(
    findings: Iterable[Mapping[str, object]], root: str | Path = ROOT
) -> dict[str, dict[str, int]]:
    """Convert Ruff C901 output into stable file/symbol complexity scores."""
    hotspots: dict[str, dict[str, int]] = {}
    locations: dict[tuple[str, str], object] = {}
    for finding in findings:
        filename, symbol, complexity = _parse_finding(finding, root)
        identity = (filename, symbol)
        if identity in locations:
            current = finding.get("location")
            raise ComplexityBaselineError(
                f"Duplicate complexity identity {filename}::{symbol} at "
                f"{locations[identity]!r} and {current!r}."
            )
        locations[identity] = finding.get("location")
        hotspots.setdefault(filename, {})[symbol] = complexity
    return {
        filename: dict(sorted(symbols.items()))
        for filename, symbols in sorted(hotspots.items())
    }


def compare_hotspots(
    expected: Mapping[str, Mapping[str, int]],
    actual: Mapping[str, Mapping[str, int]],
) -> list[str]:
    """Return deterministic differences from an exact complexity baseline."""
    differences = []
    identities = {
        (filename, symbol)
        for source in (expected, actual)
        for filename, symbols in source.items()
        for symbol in symbols
    }
    for filename, symbol in sorted(identities):
        expected_score = expected.get(filename, {}).get(symbol)
        actual_score = actual.get(filename, {}).get(symbol)
        label = f"{filename}::{symbol}"
        if expected_score is None:
            differences.append(f"{label}: new hotspot at {actual_score}")
        elif actual_score is None:
            differences.append(f"{label}: expected {expected_score}, missing")
        elif expected_score != actual_score:
            differences.append(
                f"{label}: expected {expected_score}, found {actual_score}"
            )
    return differences


def ruff_command(python: str = sys.executable) -> list[str]:
    """Return the inspectable, configuration-independent Ruff command."""
    return [
        python,
        "-m",
        "ruff",
        "check",
        *TARGETS,
        "--select",
        "C901",
        "--isolated",
        "--ignore-noqa",
        "--no-respect-gitignore",
        "--config",
        f"lint.mccabe.max-complexity={MAX_COMPLEXITY}",
        "--output-format",
        "json",
    ]


def run_ruff() -> dict[str, dict[str, int]]:
    """Run an isolated, suppression-proof scan with the pinned Ruff."""
    command = ruff_command()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise ComplexityBaselineError(
            f"Ruff failed with exit code {result.returncode}."
        )
    findings = parse_json_document(result.stdout, "Ruff output")
    if not isinstance(findings, list):
        raise ComplexityBaselineError("Ruff JSON output must be a list.")
    return normalize_findings(findings)


def baseline_payload(hotspots: Mapping[str, Mapping[str, int]]) -> dict[str, object]:
    """Build the deterministic on-disk baseline document."""
    return {
        "schema_version": SCHEMA_VERSION,
        "description": (
            "Exact C901 hotspot scores; every change requires intentional review."
        ),
        "ruff_version": RUFF_VERSION,
        "max_complexity": MAX_COMPLEXITY,
        "targets": list(TARGETS),
        "hotspots": hotspots,
    }


def write_baseline(hotspots: Mapping[str, Mapping[str, int]]) -> None:
    """Write a deterministic baseline after an intentional debt review."""
    BASELINE.write_text(
        json.dumps(baseline_payload(hotspots), indent=2, sort_keys=True) + "\n"
    )


def validate_baseline(payload: object) -> dict[str, dict[str, int]]:
    """Validate baseline metadata and return normalized hotspot scores."""
    if not isinstance(payload, dict):
        raise ComplexityBaselineError("Complexity baseline must be a JSON object.")
    expected_metadata = {
        "schema_version": SCHEMA_VERSION,
        "ruff_version": RUFF_VERSION,
        "max_complexity": MAX_COMPLEXITY,
        "targets": list(TARGETS),
    }
    for key, expected in expected_metadata.items():
        if payload.get(key) != expected:
            raise ComplexityBaselineError(
                f"Complexity baseline {key} is {payload.get(key)!r}; expected {expected!r}."
            )
    hotspots = payload.get("hotspots")
    if not isinstance(hotspots, dict):
        raise ComplexityBaselineError("Complexity baseline hotspots must be an object.")
    return _validate_hotspots(hotspots)


def _validate_hotspots(hotspots: Mapping[object, object]) -> dict[str, dict[str, int]]:
    validated: dict[str, dict[str, int]] = {}
    for filename, raw_symbols in hotspots.items():
        if not isinstance(filename, str) or not _is_safe_relative_path(filename):
            raise ComplexityBaselineError(f"Invalid baseline path: {filename!r}")
        if not isinstance(raw_symbols, dict) or not raw_symbols:
            raise ComplexityBaselineError(
                f"Baseline symbols for {filename} must be a non-empty object."
            )
        validated[filename] = _validate_symbols(filename, raw_symbols)
    return {
        filename: dict(sorted(symbols.items()))
        for filename, symbols in sorted(validated.items())
    }


def _is_safe_relative_path(filename: str) -> bool:
    path = Path(filename)
    return not path.is_absolute() and ".." not in path.parts and path.as_posix() == filename


def _validate_symbols(filename: str, symbols: Mapping[object, object]) -> dict[str, int]:
    validated = {}
    for symbol, score in symbols.items():
        if not isinstance(symbol, str) or not symbol:
            raise ComplexityBaselineError(
                f"Invalid symbol in complexity baseline for {filename}: {symbol!r}"
            )
        if isinstance(score, bool) or not isinstance(score, int) or score <= MAX_COMPLEXITY:
            raise ComplexityBaselineError(
                f"Invalid complexity for {filename}::{symbol}: {score!r}"
            )
        validated[symbol] = score
    return validated


def load_baseline() -> dict[str, dict[str, int]]:
    """Load and validate the committed complexity baseline."""
    if not BASELINE.exists():
        raise ComplexityBaselineError(f"Missing complexity baseline: {BASELINE}")
    payload = parse_json_document(BASELINE.read_text(), "Complexity baseline")
    return validate_baseline(payload)


def _run(update: bool) -> int:
    actual = run_ruff()
    if update:
        write_baseline(actual)
        print(f"Updated {BASELINE.relative_to(ROOT)}")
        return 0
    differences = compare_hotspots(load_baseline(), actual)
    if differences:
        print("Complexity debt changed:", file=sys.stderr)
        for difference in differences:
            print(f"  {difference}", file=sys.stderr)
        print(
            "Review the change, then fix it or update the exact baseline.",
            file=sys.stderr,
        )
        return 1
    scores = [score for symbols in actual.values() for score in symbols.values()]
    maximum = max(scores, default=0)
    print(
        f"Complexity baseline unchanged: {len(scores)} hotspots; maximum {maximum}."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the baseline after intentionally reviewing every change",
    )
    args = parser.parse_args()
    try:
        return _run(args.update)
    except ComplexityBaselineError as exc:
        print(f"Complexity baseline error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
