#!/usr/bin/env python3
"""Validate and summarize Muhurtam activity-to-provenance links."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'docs' / 'reference' / 'provenance.json'


def _related_claim_errors(
    activity: str,
    rules: dict,
    claims: dict[str, dict],
) -> list[str]:
    errors: list[str] = []
    for related_id in rules.get('related_claims', ()):
        related = claims.get(related_id)
        if related is None:
            errors.append(f'{activity}: unknown related claim {related_id!r}')
        elif related['surface'] != 'muhurtam':
            errors.append(
                f'{activity}: related claim {related_id!r} is not a '
                'muhurtam claim'
            )
    return errors


def _claim_field_errors(
    activity: str,
    claim_ids: tuple[str | None, str | None, str | None],
) -> list[str]:
    fields = [
        field
        for field, value in zip(
            ('source_claim', 'audit_claim', 'heuristic_claim'),
            claim_ids,
            strict=True,
        )
        if value
    ]
    if len(fields) <= 1:
        return []
    return [
        (
            f'{activity}: provenance claim fields are mutually exclusive: '
            f'{", ".join(fields)}'
        )
    ]


def _register_special_claim(
    *,
    activity: str,
    claim_id: str | None,
    label: str,
    duplicate_label: str,
    required_state: str,
    claims: dict[str, dict],
    recorded: dict[str, dict[str, str]],
) -> list[str]:
    if not claim_id:
        return []
    if any(item['claim'] == claim_id for item in recorded.values()):
        return [f'{activity}: duplicate {duplicate_label} claim {claim_id!r}']
    claim = claims.get(claim_id)
    if claim is None:
        return [f'{activity}: unknown {label} claim {claim_id!r}']
    if claim['surface'] != 'muhurtam':
        return [f'{activity}: {label} claim {claim_id!r} is not a muhurtam claim']
    if claim['verification_state'] != required_state:
        return [
            (
                f'{activity}: {label} claim {claim_id!r} is '
                f'{claim["verification_state"]!r}, not {required_state}'
            )
        ]
    recorded[activity] = {
        'claim': claim_id,
        'state': claim['verification_state'],
    }
    return []


def _register_source_claim(
    *,
    activity: str,
    claim_id: str | None,
    claims: dict[str, dict],
    linked: dict[str, str],
) -> list[str]:
    if not claim_id:
        return []
    if claim_id in linked.values():
        return [f'{activity}: duplicate activity source claim {claim_id!r}']
    claim = claims.get(claim_id)
    if claim is None:
        return [f'{activity}: unknown provenance claim {claim_id!r}']

    errors: list[str] = []
    if claim['surface'] != 'muhurtam':
        errors.append(f'{activity}: {claim_id!r} is not a muhurtam claim')
    if claim['verification_state'] != 'verified':
        errors.append(
            f'{activity}: {claim_id!r} is {claim["verification_state"]!r}, '
            'not verified'
        )
    if not errors:
        linked[activity] = claim_id
    return errors


def audit() -> dict:
    sys.path.insert(0, str(ROOT))
    from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES

    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    claims = {claim['id']: claim for claim in ledger['claims']}
    linked: dict[str, str] = {}
    audited: dict[str, dict[str, str]] = {}
    heuristic: dict[str, dict[str, str]] = {}
    errors: list[str] = []

    for activity, rules in ACTIVITY_RULES.items():
        audit_id = rules.get('audit_claim')
        heuristic_id = rules.get('heuristic_claim')
        claim_id = rules.get('source_claim')
        errors.extend(_related_claim_errors(activity, rules, claims))
        errors.extend(_claim_field_errors(
            activity, (claim_id, audit_id, heuristic_id)
        ))
        errors.extend(_register_special_claim(
            activity=activity,
            claim_id=audit_id,
            label='audit',
            duplicate_label='activity audit',
            required_state='contradicted',
            claims=claims,
            recorded=audited,
        ))
        errors.extend(_register_special_claim(
            activity=activity,
            claim_id=heuristic_id,
            label='heuristic',
            duplicate_label='heuristic',
            required_state='heuristic',
            claims=claims,
            recorded=heuristic,
        ))
        errors.extend(_register_source_claim(
            activity=activity,
            claim_id=claim_id,
            claims=claims,
            linked=linked,
        ))

    unlinked = sorted(
        set(ACTIVITY_RULES) - set(linked) - set(audited) - set(heuristic))
    return {
        'activity_count': len(ACTIVITY_RULES),
        'verified_profile_count': len(linked),
        'verified_profiles': linked,
        'known_conflicts': audited,
        'heuristic_profiles': heuristic,
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
        heuristic_count = len(result['heuristic_profiles'])
        heuristic_label = (
            'explicit heuristic' if heuristic_count == 1
            else 'explicit heuristics')
        print(
            f'{result["verified_profile_count"]}/{result["activity_count"]} '
            'activities have verified rule-level profiles; '
            f'{len(result["known_conflicts"])} have known conflicts; '
            f'{heuristic_count} {heuristic_label}; '
            f'{len(result["needs_rule_locators"])} need locators.')
        for error in result['errors']:
            print(f'ERROR: {error}', file=sys.stderr)
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
