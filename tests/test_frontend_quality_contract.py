"""Contracts for the frontend lint and coverage regression gates."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_quality_tools_and_runner_are_exactly_pinned():
    package = json.loads((ROOT / "package.json").read_text())

    assert package["scripts"]["lint"] == (
        'eslint "src/**/*.ts" vite.config.ts ".vitepress/**/*.ts" '
        '--max-warnings 0 --no-inline-config '
        '--suppressions-location eslint-suppressions.json'
    )
    assert package["scripts"]["test:coverage"] == "vitest run --coverage"
    expected = {
        "eslint": "10.10.0",
        "@eslint/js": "10.0.1",
        "typescript-eslint": "8.69.0",
        "vitest": "4.1.9",
        "@vitest/coverage-v8": "4.1.9",
    }
    assert {
        name: package["devDependencies"][name]
        for name in expected
    } == expected


def test_eslint_suppressions_are_an_exact_reviewed_baseline():
    suppressions = json.loads((ROOT / "eslint-suppressions.json").read_text())

    assert suppressions == {
        ".vitepress/config.ts": {
            "@typescript-eslint/no-explicit-any": {"count": 14},
        },
        "src/__tests__/gochara-interpretation-evidence.test.ts": {
            "@typescript-eslint/ban-ts-comment": {"count": 1},
        },
        "src/__tests__/today-festival-next.test.ts": {
            "@typescript-eslint/ban-ts-comment": {"count": 1},
        },
        "src/__tests__/today-request-order.test.ts": {
            "@typescript-eslint/ban-ts-comment": {"count": 1},
        },
        "src/muhurta-scorer.ts": {
            "@typescript-eslint/no-explicit-any": {"count": 2},
        },
    }


def test_coverage_boundary_is_full_source_and_uses_absolute_caps():
    config = (ROOT / "vite.config.ts").read_text()

    assert "include: ['src/**/*.ts']" in config
    assert "exclude: ['src/**/__tests__/**']" in config
    assert "statements: -2035" in config
    assert "branches: -2037" in config
    assert "functions: -279" in config
    assert "lines: -1601" in config
