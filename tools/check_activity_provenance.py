#!/usr/bin/env python3
"""Validate and summarize Muhurtam activity-to-provenance links."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'docs' / 'reference' / 'provenance.json'


def audit() -> dict:
    sys.path.insert(0, str(ROOT))
    from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES

    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    claims = {claim['id']: claim for claim in ledger['claims']}
    linked: dict[str, str] = {}
    errors: list[str] = []

    for activity, rules in ACTIVITY_RULES.items():
        claim_id = rules.get('source_claim')
        if not claim_id:
            continue
        if claim_id in linked.values():
            errors.append(f'{activity}: duplicate activity source claim {claim_id!r}')
            continue
        claim = claims.get(claim_id)
        if claim is None:
            errors.append(f'{activity}: unknown provenance claim {claim_id!r}')
            continue
        valid = True
        if claim['surface'] != 'muhurtam':
            errors.append(f'{activity}: {claim_id!r} is not a muhurtam claim')
            valid = False
        if claim['verification_state'] != 'verified':
            errors.append(
                f'{activity}: {claim_id!r} is {claim["verification_state"]!r}, '
                'not verified')
            valid = False
        if valid:
            linked[activity] = claim_id

    unlinked = sorted(set(ACTIVITY_RULES) - set(linked))
    return {
        'activity_count': len(ACTIVITY_RULES),
        'verified_profile_count': len(linked),
        'verified_profiles': linked,
        'needs_rule_locators': unlinked,
        'errors': errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f'{result["verified_profile_count"]}/{result["activity_count"]} '
            'activities have verified rule-level profiles; '
            f'{len(result["needs_rule_locators"])} need locators.')
        for error in result['errors']:
            print(f'ERROR: {error}', file=sys.stderr)
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
