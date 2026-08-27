"""Keep dependency installation and security-audit inputs aligned."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_security_workflow_audits_the_ci_requirements_input():
    workflow = (ROOT / ".github/workflows/security.yml").read_text()

    assert "pip uninstall --yes mcp-server-panchangam" in workflow
    assert "pip-audit --local --strict" in workflow
    assert "pip-audit --local --strict --skip-editable" not in workflow
    assert "pip-audit -r requirements.txt" not in workflow
    assert "pip-audit -r requirements.lock" not in workflow


def test_lockfile_documents_an_upgrade_refresh():
    header = "\n".join((ROOT / "requirements.lock").read_text().splitlines()[:24])

    assert "uv pip compile pyproject.toml --extra test --python-version 3.11" in header
    assert "--upgrade --generate-hashes -o requirements.lock" in header
