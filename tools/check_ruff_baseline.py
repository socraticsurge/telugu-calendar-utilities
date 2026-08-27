#!/usr/bin/env python3
"""Reject changes to the repository's explicitly recorded Ruff debt."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path
from typing import Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "tools/ruff_baseline.json"
TARGETS = ("telugu_panchangam", "tests", "tools", "scripts")
RUFF_VERSION = version("ruff")


def count_findings(
    findings: Iterable[Mapping[str, object]], root: str | Path = ROOT
) -> dict[str, dict[str, int]]:
    """Count Ruff findings by repository-relative file and rule."""
    root_path = Path(root).resolve()
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for finding in findings:
        filename = Path(str(finding["filename"])).resolve().relative_to(root_path)
        counts[filename.as_posix()][str(finding["code"])] += 1
    return {
        filename: dict(sorted(rules.items()))
        for filename, rules in sorted(counts.items())
    }


def compare_counts(
    expected: Mapping[str, Mapping[str, int]],
    actual: Mapping[str, Mapping[str, int]],
) -> list[str]:
    """Return deterministic differences between expected and actual debt."""
    differences = []
    filenames = sorted(set(expected) | set(actual))
    for filename in filenames:
        rules = sorted(set(expected.get(filename, {})) | set(actual.get(filename, {})))
        for rule in rules:
            expected_count = expected.get(filename, {}).get(rule, 0)
            actual_count = actual.get(filename, {}).get(rule, 0)
            if expected_count != actual_count:
                differences.append(
                    f"{filename} {rule}: expected {expected_count}, found {actual_count}"
                )
    return differences


def run_ruff() -> dict[str, dict[str, int]]:
    """Run the pinned Ruff rules and return normalized finding counts."""
    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        *TARGETS,
        "--select",
        "E,F,I",
        "--ignore",
        "E501",
        "--output-format",
        "json",
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        print(result.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"Ruff failed with exit code {result.returncode}")
    return count_findings(json.loads(result.stdout))


def write_baseline(counts: Mapping[str, Mapping[str, int]]) -> None:
    """Write a deterministic baseline after an intentional debt review."""
    payload = {
        "description": "Ruff E/F/I debt baseline; counts may only change intentionally.",
        "ruff_version": RUFF_VERSION,
        "counts": counts,
    }
    BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the baseline after intentionally reviewing debt changes",
    )
    args = parser.parse_args()

    baseline = json.loads(BASELINE.read_text()) if BASELINE.exists() else None
    if not args.update and baseline is None:
        print(f"Missing Ruff debt baseline: {BASELINE}", file=sys.stderr)
        return 2
    if not args.update and baseline["ruff_version"] != RUFF_VERSION:
        print(
            f"Ruff version mismatch: baseline uses {baseline['ruff_version']}, "
            f"installed version is {RUFF_VERSION}.",
            file=sys.stderr,
        )
        return 2

    actual = run_ruff()
    if args.update:
        write_baseline(actual)
        print(f"Updated {BASELINE.relative_to(ROOT)}")
        return 0

    expected = baseline["counts"]
    differences = compare_counts(expected, actual)
    if differences:
        print("Ruff debt changed:", file=sys.stderr)
        for difference in differences:
            print(f"  {difference}", file=sys.stderr)
        print(
            "Fix new findings, or run with --update after reviewing intentional reductions.",
            file=sys.stderr,
        )
        return 1

    total = sum(sum(rules.values()) for rules in actual.values())
    print(f"Ruff debt baseline unchanged: {total} findings; no new debt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
