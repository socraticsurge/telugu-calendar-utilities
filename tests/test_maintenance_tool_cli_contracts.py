"""Golden CLI contracts for the refactored repository-maintenance tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ('arguments', 'expected_stdout'),
    [
        (
            ('tools/check_computation_inventory.py',),
            (
                'Computation inventory valid: 62 records, 166 implementations, '
                '98 audited source files, 62/62 methods documented.\n'
            ),
        ),
        (
            ('tools/check_documentation_freshness.py',),
            (
                'Documentation facts current: 62 computations, 17 MCP tools, '
                '22 cities, 35 Muhurtam profiles.\n'
            ),
        ),
        (
            ('tools/check_activity_provenance.py',),
            (
                '34/35 activities have verified rule-level profiles; 0 have '
                'known conflicts; 1 explicit heuristic; 0 need locators.\n'
            ),
        ),
        (('tools/export_muhurtam_rule_crosswalk.py', '--check'), ''),
    ],
)
def test_maintenance_cli_output_is_stable(
    arguments: tuple[str, ...], expected_stdout: str
) -> None:
    completed = subprocess.run(
        [sys.executable, *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stderr == ''
    assert completed.stdout == expected_stdout
