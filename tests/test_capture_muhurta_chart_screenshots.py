"""Debt-regression checks for the deterministic screenshot capture tool."""

from __future__ import annotations

import ast
from pathlib import Path

CAPTURE_TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "capture_muhurta_chart_screenshots.py"
)


def test_sonar_flagged_literals_have_one_named_definition_each():
    tree = ast.parse(CAPTURE_TOOL.read_text(encoding="utf-8"))
    assignments = {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }

    expected = {
        "MUHURTA_RESULT_SELECTOR": "#mu-result",
        "PANCHANGAM_SHORTLIST_SHOWN_COPY": "Panchangam shortlist shown",
    }
    assert {name: assignments.get(name) for name in expected} == expected

    literals = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    assert {value: literals.count(value) for value in expected.values()} == {
        value: 1 for value in expected.values()
    }
