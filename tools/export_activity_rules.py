#!/usr/bin/env python3
"""Export the browser-supported subset of Python Muhurtam activity rules.

Run without arguments to update the generated JSON. Run with ``--check`` in
tests/CI to fail when the committed artefact has drifted from Python.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'src' / 'data' / 'activity-rules.generated.json'
CONSUMED_FIELDS = (
    'label', 'avoid_karana', 'prefer_lagna_class', 'prefer_choghadiya',
    'skip_on_yoga', 'prefer_vara', 'prefer_tithi_class', 'avoid_tithi_class',
    'required_lagna_class', 'allowed_maasams', 'allowed_varas',
    'avoid_vara_paksha', 'allowed_solar_classes', 'allowed_nakshatras',
    'avoid_nakshatras', 'prefer_nakshatras', 'allowed_tithi_numbers',
    'prefer_tithi_numbers',
    'avoid_tithi_numbers',
    'manual_checks', 'manual_prerequisites', 'avoid_janma_nakshatra',
    'avoid_vara_tithi_names',
    'allowed_lagnas', 'prefer_lagnas',
    'caution_lagna_solar',
    'source_claim', 'audit_claim', 'heuristic_claim', 'related_claims',
    'daytime_only',
    'forenoon_only', 'allowed_pakshams',
    'allowed_solar_signs', 'allowed_tithi_names', 'skip_on_combust',
)


def build_export() -> dict:
    sys.path.insert(0, str(ROOT))
    from telugu_panchangam.personal.activity_catalog import (
        BROWSER_ACTIVITIES, BROWSER_ACTIVITY_GROUPS,
    )
    from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES

    missing = set(BROWSER_ACTIVITIES) - set(ACTIVITY_RULES)
    if missing:
        raise ValueError(f'Browser catalogue contains unknown activities: {sorted(missing)}')

    rules = {
        key: {
            field: ACTIVITY_RULES[key][field]
            for field in CONSUMED_FIELDS
            if field in ACTIVITY_RULES[key]
        }
        for key in BROWSER_ACTIVITIES
    }
    return {
        'schema_version': 1,
        'source': 'telugu_panchangam.personal.activity_rules.ACTIVITY_RULES',
        'consumed_fields': list(CONSUMED_FIELDS),
        'groups': [
            {'label': label, 'activities': list(activities)}
            for label, activities in BROWSER_ACTIVITY_GROUPS
        ],
        'rules': rules,
    }


def rendered() -> str:
    return json.dumps(build_export(), indent=2, ensure_ascii=False) + '\n'


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
                '`python tools/export_activity_rules.py`.',
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
