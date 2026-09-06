"""Install a uv-locked dependency set under the repository's CI policy.

All artifacts must be hash-locked wheels except PySwissEph.  Upstream only
publishes wheels through Python 3.11, so Python 3.12+ support requires building
its hash-locked source archive.  The build runs without isolation against the
locked build-tool group, preventing an unpinned build-time dependency fetch.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def _export(output: Path, selectors: list[str]) -> None:
    _run(
        [
            "uv",
            "export",
            "--quiet",
            "--locked",
            "--no-dev",
            "--no-emit-project",
            *selectors,
            "--output-file",
            str(output),
        ]
    )


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--group", action="append", default=[])
    args = parser.parse_args()

    selectors = [item for extra in args.extra for item in ("--extra", extra)]
    selectors += [item for group in args.group for item in ("--group", group)]

    _run(["uv", "lock", "--check"])
    _run(["uv", "venv", str(VENV), "--python", sys.executable])
    python = _venv_python(VENV)

    needs_pyswisseph_build = sys.version_info >= (3, 12)

    with tempfile.TemporaryDirectory(prefix="locked-dependencies-") as tmp:
        tmp_dir = Path(tmp)
        selected_requirements = tmp_dir / "selected.txt"

        if needs_pyswisseph_build:
            build_requirements = tmp_dir / "build.txt"
            _export(build_requirements, ["--only-group", "build"])
            _run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(python),
                    "--require-hashes",
                    "--only-binary",
                    ":all:",
                    "-r",
                    str(build_requirements),
                ]
            )

        _export(selected_requirements, selectors)
        install_command = [
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--require-hashes",
            "--only-binary",
            ":all:",
        ]
        if needs_pyswisseph_build:
            install_command += [
                "--no-binary",
                "pyswisseph",
                "--no-build-isolation",
            ]
        _run([*install_command, "-r", str(selected_requirements)])


if __name__ == "__main__":
    main()
