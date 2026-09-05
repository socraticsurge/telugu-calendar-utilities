"""Keep dependency installation and security-audit inputs aligned."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_security_workflow_audits_the_uv_locked_runtime_input():
    workflow = (ROOT / ".github/workflows/security.yml").read_text()

    assert "name: pip-audit (requirements.txt)" in workflow
    assert (
        "uv sync --locked --only-group audit --no-install-project --no-build"
        in workflow
    )
    assert "uv export --quiet --locked --no-dev --no-emit-project" in workflow
    assert (
        "pip-audit --strict --disable-pip --require-hashes -r .audit-requirements.txt"
    ) in workflow
    assert "pip install" not in workflow


def test_uv_lock_is_the_single_active_python_resolution():
    lock = (ROOT / "uv.lock").read_text()

    assert 'requires-python = ">=3.10"' in lock
    assert 'name = "mcp-server-panchangam"' in lock
    assert not (ROOT / "requirements.lock").exists()


def test_locked_installer_allows_only_the_pyswisseph_source_archive():
    installer = (ROOT / "tools/install_locked_dependencies.py").read_text()

    assert '"--require-hashes"' in installer
    assert '"--only-binary"' in installer
    assert '":all:"' in installer
    assert '"--no-binary"' in installer
    assert '"pyswisseph"' in installer
    assert '"--no-build-isolation"' in installer
