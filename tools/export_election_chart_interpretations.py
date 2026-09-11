"""Export the canonical election-chart interpretation registry for browsers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "reference" / "election-chart-interpretations.json"
OUTPUT = ROOT / "src" / "data" / "election-chart-interpretations.generated.json"


def rendered() -> str:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = rendered()
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if actual != expected:
            print(
                f"{OUTPUT.relative_to(ROOT)} is stale; run "
                "`python tools/export_election_chart_interpretations.py`.",
                file=sys.stderr,
            )
            return 1
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
