"""Keep dependency installation and security-audit inputs aligned."""

import subprocess
import sys
from pathlib import Path

from tools import install_locked_dependencies

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


def test_locked_installer_rejects_an_external_venv_target(tmp_path):
    external_venv = tmp_path / "external-venv"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/install_locked_dependencies.py"),
            "--venv",
            str(external_venv),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unrecognized arguments: --venv" in result.stderr
    assert not external_venv.exists()


def test_locked_installer_targets_only_the_repository_venv(monkeypatch):
    commands = []
    monkeypatch.setattr(install_locked_dependencies, "_run", commands.append)
    monkeypatch.setattr(
        install_locked_dependencies,
        "_export",
        lambda _output, _selectors: None,
    )
    monkeypatch.setattr(install_locked_dependencies.sys, "argv", ["installer"])

    install_locked_dependencies.main()

    assert commands[0] == ["uv", "lock", "--check"]
    assert commands[1] == [
        "uv",
        "venv",
        str(ROOT / ".venv"),
        "--python",
        sys.executable,
    ]


def test_all_workflow_uv_run_commands_disable_builds():
    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        for line_number, line in enumerate(workflow.read_text().splitlines(), start=1):
            if "uv run --no-sync" in line:
                assert "uv run --no-sync --no-build" in line, (
                    f"{workflow.relative_to(ROOT)}:{line_number} permits builds"
                )
