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
    audited: dict[str, dict[str, str]] = {}
    errors: list[str] = []

    for activity, rules in ACTIVITY_RULES.items():
        audit_id = rules.get('audit_claim')
        claim_id = rules.get('source_claim')
        if audit_id and claim_id:
            errors.append(
                f'{activity}: source_claim and audit_claim are mutually exclusive')
        if audit_id:
            if any(item['claim'] == audit_id for item in audited.values()):
                errors.append(f'{activity}: duplicate activity audit claim {audit_id!r}')
                claim = None
            else:
                claim = claims.get(audit_id)
            if claim is None and not any(
                    item['claim'] == audit_id for item in audited.values()):
                errors.append(f'{activity}: unknown audit claim {audit_id!r}')
            elif claim['surface'] != 'muhurtam':
                errors.append(f'{activity}: audit claim {audit_id!r} is not a muhurtam claim')
            elif claim['verification_state'] != 'contradicted':
                errors.append(
                    f'{activity}: audit claim {audit_id!r} is '
                    f'{claim["verification_state"]!r}, not contradicted')
            else:
                audited[activity] = {
                    'claim': audit_id,
                    'state': claim['verification_state'],
                }
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

    unlinked = sorted(set(ACTIVITY_RULES) - set(linked) - set(audited))
    return {
        'activity_count': len(ACTIVITY_RULES),
        'verified_profile_count': len(linked),
        'verified_profiles': linked,
        'known_conflicts': audited,
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
            f'{len(result["known_conflicts"])} have known conflicts; '
            f'{len(result["needs_rule_locators"])} need locators.')
        for error in result['errors']:
            print(f'ERROR: {error}', file=sys.stderr)
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
