#!/usr/bin/env python3
"""Run the complete local verification contract in its documented order."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def documentation_commands(python: str = sys.executable) -> list[list[str]]:
    """Return documentation gates added ahead of the established checks."""
    return [
        [python, 'tools/check_computation_inventory.py'],
        [python, 'tools/check_documentation_freshness.py'],
    ]


def commands(python: str = sys.executable) -> list[list[str]]:
    """Return the canonical checks, kept inspectable for docs and tests."""
    return [
        [python, 'tools/check_activity_provenance.py'],
        [python, 'tools/export_activity_rules.py', '--check'],
        [python, 'tools/check_ruff_baseline.py'],
        [python, '-m', 'pytest', 'tests/'],
        ['npm', 'test'],
        ['npm', 'run', 'build'],
    ]


def all_commands(python: str = sys.executable) -> list[list[str]]:
    """Return the complete verification contract in execution order."""
    return documentation_commands(python) + commands(python)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run provenance, generated-data, backend, and frontend checks.')
    parser.add_argument(
        '--list', action='store_true', help='print checks without running them')
    args = parser.parse_args()

    checks = all_commands()
    if args.list:
        for command in checks:
            print(subprocess.list2cmdline(command))
        return 0

    for command in checks:
        print(f'\n==> {subprocess.list2cmdline(command)}', flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT)
        except FileNotFoundError as exc:
            print(f'ERROR: required executable not found: {exc.filename}', file=sys.stderr)
            return 127
        if result.returncode:
            return result.returncode
    print('\nAll project verification checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
