"""Contracts for CI event coverage and deduplication."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci.yml"
DEPENDABOT = ROOT / ".github/dependabot.yml"
BROWSER_SMOKE = ROOT / "tests/test_browser_smoke.py"


def test_ci_normalizes_push_and_pull_request_concurrency_keys():
    workflow = WORKFLOW.read_text()

    assert "pull_request:" in workflow
    assert "branches-ignore: [gh-pages]" in workflow
    assert "branches-ignore: [master" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert (
        "group: ci-${{ github.event.pull_request.head.repo.full_name || "
        "github.repository }}-${{ github.head_ref || github.ref_name }}" in workflow
    )
    assert "group: ci-${{ github.ref }}" not in workflow


def test_ci_retains_supported_runtimes_and_browser_coverage():
    workflow = WORKFLOW.read_text()
    backend, frontend = workflow.split("  frontend-and-browser:", maxsplit=1)

    assert "python-version: ['3.10', '3.11', '3.12', '3.13']" in workflow
    assert "--extra browser-test" not in backend
    assert "actions/setup-node" not in backend
    assert "playwright install" not in backend
    assert "run: npm test" not in backend
    assert "run: uv run --no-sync python tools/check_ruff_baseline.py" in backend
    assert "--ignore=tests/test_browser_smoke.py" in backend
    assert "python-version: '3.11'" in frontend
    assert "--extra test --extra browser-test" in frontend
    assert "playwright install --with-deps chromium" in frontend
    assert "run: npm ci --ignore-scripts" in frontend
    assert "python -m pytest tests/test_browser_smoke.py -v" in frontend
    assert "run: npm test" in frontend


def test_dependabot_tracks_python_node_and_action_locks():
    dependabot = DEPENDABOT.read_text()

    assert dependabot.count("package-ecosystem: pip") == 1
    assert dependabot.count("package-ecosystem: npm") == 1
    assert dependabot.count("package-ecosystem: github-actions") == 1


def test_browser_fallback_install_disables_lifecycle_scripts():
    browser_smoke = BROWSER_SMOKE.read_text()

    assert "[npm, 'ci', '--ignore-scripts']" in browser_smoke
