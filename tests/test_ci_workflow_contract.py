"""Contracts for CI event coverage and deduplication."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci.yml"


def test_ci_normalizes_push_and_pull_request_concurrency_keys():
    workflow = WORKFLOW.read_text()

    assert "pull_request:" in workflow
    assert "branches-ignore: [master, gh-pages]" in workflow
    assert "group: ci-${{ github.head_ref || github.ref_name }}" in workflow
    assert "group: ci-${{ github.ref }}" not in workflow


def test_ci_retains_supported_runtimes_and_browser_coverage():
    workflow = WORKFLOW.read_text()

    assert "python-version: ['3.10', '3.11', '3.12', '3.13']" in workflow
    assert "playwright install --with-deps chromium" in workflow
    assert "run: uv run --no-sync python tools/check_ruff_baseline.py" in workflow
    assert "run: uv run --no-sync python -m pytest tests/ -v" in workflow
    assert "run: npm test" in workflow
