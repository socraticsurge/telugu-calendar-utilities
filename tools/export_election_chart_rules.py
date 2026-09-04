"""Export the canonical election-chart rules for the browser evaluator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'src' / 'data' / 'election-chart-rules.generated.json'


def rendered() -> str:
    sys.path.insert(0, str(ROOT))
    from telugu_panchangam.personal.election_assessors.conventions import (
        ELECTION_CHART_CONVENTION_SCHEMA_VERSION,
        ELECTION_CHART_CONVENTIONS,
    )
    from telugu_panchangam.personal.election_chart_rules import (
        ELECTION_CHART_HOUSE_SYSTEM,
        ELECTION_CHART_MANUAL_REMAINDERS,
        ELECTION_CHART_NODE_CONVENTION,
        ELECTION_CHART_PLANETS,
        ELECTION_CHART_RULE_SCHEMA_VERSION,
        ELECTION_CHART_RULES,
    )
    payload = {
        'schema_version': ELECTION_CHART_RULE_SCHEMA_VERSION,
        'source': 'telugu_panchangam.personal.election_chart_rules.ELECTION_CHART_RULES',
        'house_system': ELECTION_CHART_HOUSE_SYSTEM,
        'node_convention': ELECTION_CHART_NODE_CONVENTION,
        'vacancy_includes': list(ELECTION_CHART_PLANETS),
        'convention_schema_version': ELECTION_CHART_CONVENTION_SCHEMA_VERSION,
        'conventions': ELECTION_CHART_CONVENTIONS,
        'rules': {activity: list(rules) for activity, rules in ELECTION_CHART_RULES.items()},
        'manual_remainders': {
            activity: list(items)
            for activity, items in ELECTION_CHART_MANUAL_REMAINDERS.items()
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = rendered()
    if args.check:
        actual = OUTPUT.read_text(encoding='utf-8') if OUTPUT.exists() else ''
        if actual != expected:
            print(
                f'{OUTPUT.relative_to(ROOT)} is stale; run '
                '`python tools/export_election_chart_rules.py`.',
                file=sys.stderr,
            )
            return 1
        return 0
    OUTPUT.write_text(expected, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
