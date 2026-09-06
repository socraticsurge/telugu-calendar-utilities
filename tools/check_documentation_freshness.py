#!/usr/bin/env python3
"""Check generated project facts and high-level computation documentation."""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / 'docs' / 'reference' / 'project-facts.json'
REGISTRY_PATH = ROOT / 'docs' / 'reference' / 'computations.json'
_FEED_DIMENSIONS_LABEL = 'feed dimensions'
_MCP_TOOL_COUNT_LABEL = 'MCP tool count'
_PYPI_README_PATH = 'README_PYPI.md'

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_PUBLIC_TOOL_RE = re.compile(r'\b(?:find|get|list)_[a-z][a-z0-9_]*\b')


def _mcp_tool_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    names: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            function = decorator.func
            if (
                isinstance(function, ast.Attribute)
                and function.attr == 'tool'
                and isinstance(function.value, ast.Name)
                and function.value.id == 'mcp'
            ):
                names.append(node.name)
                break
    return names


def build_facts() -> dict[str, Any]:
    """Derive public catalogue and inventory facts from canonical sources."""
    from telugu_panchangam.cities import CITIES
    from telugu_panchangam.generate import ENGINES
    from telugu_panchangam.personal.activity_catalog import (
        BROWSER_ACTIVITIES,
        BROWSER_ACTIVITY_GROUPS,
    )
    from telugu_panchangam.personal.activity_rules import (
        ACTIVITIES,
        ACTIVITY_ALIASES,
        ACTIVITY_RULES,
    )
    from tools.check_activity_provenance import audit
    from tools.check_computation_inventory import _load_json, _relative_source_paths

    inventory = _load_json(REGISTRY_PATH)
    implementations = [
        implementation
        for computation in inventory['computations']
        for implementation in computation['implementations']
    ]
    activity_audit = audit()
    server_path = ROOT / 'telugu_panchangam' / 'mcp' / 'server.py'
    systems = list(ENGINES)

    return {
        'schema_version': 1,
        'generated_by': 'tools/check_documentation_freshness.py',
        'sources': [
            'docs/reference/computations.json',
            'docs/reference/provenance.json',
            'telugu_panchangam/cities.py',
            'telugu_panchangam/generate.py',
            'telugu_panchangam/mcp/server.py',
            'telugu_panchangam/personal/activity_catalog.py',
            'telugu_panchangam/personal/activity_rules.py',
        ],
        'calculation_systems': systems,
        'city_count': len(CITIES),
        'base_feed_count': len(CITIES) * len(systems),
        'mcp_tools': _mcp_tool_names(server_path),
        'computation_inventory': {
            'record_count': len(inventory['computations']),
            'implementation_count': len(implementations),
            'owner_count': sum(item['role'] == 'owner' for item in implementations),
            'mirror_count': sum(item['role'] == 'mirror' for item in implementations),
            'audited_source_file_count': len(_relative_source_paths(inventory)),
        },
        'muhurta_activities': {
            'canonical_count': len(ACTIVITY_RULES),
            'accepted_key_count': len(ACTIVITIES),
            'accepted_keys': list(ACTIVITIES),
            'aliases': ACTIVITY_ALIASES,
            'browser_count': len(BROWSER_ACTIVITIES),
            'browser_keys': list(BROWSER_ACTIVITIES),
            'browser_group_count': len(BROWSER_ACTIVITY_GROUPS),
            'verified_profile_count': activity_audit['verified_profile_count'],
            'conflicted_profile_count': len(activity_audit['known_conflicts']),
            'heuristic_profile_count': len(activity_audit['heuristic_profiles']),
            'unlinked_profile_count': len(activity_audit['needs_rule_locators']),
        },
    }


def rendered_facts() -> str:
    return json.dumps(build_facts(), indent=2, ensure_ascii=False) + '\n'


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding='utf-8')


def _check_contains(
    errors: list[str], relative_path: str, expected: str, description: str
) -> None:
    if expected not in _read(relative_path):
        errors.append(
            f'{relative_path}: expected current {description} {expected!r}; '
            f'run `python tools/check_documentation_freshness.py --write` '
            'and update the affected prose'
        )


def _generated_facts_errors(facts: dict[str, Any]) -> list[str]:
    expected = json.dumps(facts, indent=2, ensure_ascii=False) + '\n'
    actual = FACTS_PATH.read_text(encoding='utf-8') if FACTS_PATH.exists() else ''
    if actual == expected:
        return []
    return [
        (
            'docs/reference/project-facts.json is stale; run '
            '`python tools/check_documentation_freshness.py --write`'
        )
    ]


def _count_contracts(facts: dict[str, Any]) -> dict[str, list[tuple[str, str]]]:
    city_count = facts['city_count']
    system_count = len(facts['calculation_systems'])
    feed_count = facts['base_feed_count']
    tool_count = len(facts['mcp_tools'])
    return {
        'README.md': [
            (f'{city_count} cities', 'city count'),
            (f'{city_count} cities × {system_count} systems = {feed_count} feeds', 'feed count'),
        ],
        'ARCHITECTURE.md': [
            (f'{city_count} cities × {system_count} systems', _FEED_DIMENSIONS_LABEL),
        ],
        'docs/reference/README.md': [
            (f'{city_count} cities × {system_count} systems', _FEED_DIMENSIONS_LABEL),
            (f'**{tool_count} tools**', _MCP_TOOL_COUNT_LABEL),
        ],
        'docs/reference/01-system-mindmap.md': [
            (f'{city_count} cities x {system_count} systems', _FEED_DIMENSIONS_LABEL),
            (f'MCP server ({tool_count} tools)', _MCP_TOOL_COUNT_LABEL),
        ],
        'docs/reference/04-user-facing-features.md': [
            (f'MCP server — {tool_count} tools', _MCP_TOOL_COUNT_LABEL),
            (f'{city_count} cities × {system_count} systems = {feed_count} feeds', 'feed count'),
        ],
        _PYPI_README_PATH: [
            (f'{city_count} pre-configured cities', 'city count'),
        ],
    }


def _count_contract_errors(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, checks in _count_contracts(facts).items():
        for expected, description in checks:
            _check_contains(errors, path, expected, description)
    return errors


def _tool_documentation_errors(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_tools = set(facts['mcp_tools'])
    for path in ('docs/reference/04-user-facing-features.md', _PYPI_README_PATH):
        documented = set(_PUBLIC_TOOL_RE.findall(_read(path)))
        missing = expected_tools - documented
        unknown = documented - expected_tools
        if missing:
            errors.append(f'{path}: missing MCP tools: {", ".join(sorted(missing))}')
        if unknown:
            errors.append(
                f'{path}: names obsolete or not public MCP tools: '
                + ', '.join(sorted(unknown))
            )
    return errors


def _activity_documentation_errors(facts: dict[str, Any]) -> list[str]:
    package_readme = _read(_PYPI_README_PATH)
    missing = [
        key
        for key in facts['muhurta_activities']['accepted_keys']
        if f'`{key}`' not in package_readme
    ]
    if not missing:
        return []
    return [
        'README_PYPI.md: missing accepted find_muhurta activity keys: '
        + ', '.join(missing)
    ]


def _stale_node_claim_errors() -> list[str]:
    errors: list[str] = []
    stale_claims = {
        _PYPI_README_PATH: ('Rahu/Ketu set (3, 6, 11)',),
        'telugu_panchangam/mcp/server.py': ('Rahu/Ketu houses omit the 10th',),
        'docs/reference/08-provenance-and-authority.md': (
            'known conflict in the configured node houses',
        ),
        'docs/reference/README.md': ('known Rahu/Ketu conflict',),
    }
    for path, phrases in stale_claims.items():
        text = _read(path)
        for phrase in phrases:
            if phrase in text:
                errors.append(
                    f'{path}: obsolete Gochara node claim {phrase!r}; '
                    'the configured houses are now 3, 6, 10 and 11'
                )
    return errors


def validate_documentation(facts: dict[str, Any] | None = None) -> list[str]:
    """Return actionable drift errors for generated and public documentation."""
    facts = facts or build_facts()
    return [
        *_generated_facts_errors(facts),
        *_count_contract_errors(facts),
        *_tool_documentation_errors(facts),
        *_activity_documentation_errors(facts),
        *_stale_node_claim_errors(),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check generated facts and computation-documentation freshness.'
    )
    parser.add_argument(
        '--write', action='store_true', help='regenerate project-facts.json'
    )
    args = parser.parse_args()

    if args.write:
        FACTS_PATH.write_text(rendered_facts(), encoding='utf-8')

    errors = validate_documentation()
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1

    facts = build_facts()
    inventory = facts['computation_inventory']
    activities = facts['muhurta_activities']
    print(
        f'Documentation facts current: {inventory["record_count"]} computations, '
        f'{len(facts["mcp_tools"])} MCP tools, {facts["city_count"]} cities, '
        f'{activities["canonical_count"]} Muhurtam profiles.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
