"""Guards against version drift between PyPI (pyproject.toml) and the
MCP registry (server.json).

These three strings must agree:
  - pyproject.toml [project] version       → what PyPI publishes
  - server.json    version                  → what the MCP registry advertises
  - server.json    packages[0].version      → what `uvx <pkg>` resolves

If a maintainer bumps one without the others, MCP discovery clients pin
to a stale version of a package PyPI already shipped. This test fails
loudly when they drift.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover — kept for the declared 3.10 floor in pyproject.toml
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / 'pyproject.toml'
SERVER_JSON = REPO_ROOT / 'server.json'


def _pyproject_version() -> str:
    with PYPROJECT.open('rb') as fh:
        return tomllib.load(fh)['project']['version']


def _server_json() -> dict:
    return json.loads(SERVER_JSON.read_text(encoding='utf-8'))


def test_pyproject_and_server_top_level_versions_match():
    py = _pyproject_version()
    sj = _server_json()['version']
    assert py == sj, (
        f'pyproject.toml version is {py!r} but server.json top-level '
        f'version is {sj!r}. Bump both together so the MCP registry '
        f'does not advertise a stale package version.'
    )


def test_server_top_level_and_package_versions_match():
    sj = _server_json()
    top = sj['version']
    pkg = sj['packages'][0]['version']
    assert top == pkg, (
        f'server.json top-level version is {top!r} but '
        f'packages[0].version is {pkg!r}. Both fields must reference '
        f'the same release on PyPI.'
    )


def test_all_three_versions_match():
    """End-to-end: the chain pyproject → server.top → server.package
    must agree, otherwise PyPI / MCP-registry / uvx-resolve disagree."""
    py = _pyproject_version()
    sj = _server_json()
    assert py == sj['version'] == sj['packages'][0]['version'], (
        f'Version chain disagrees: pyproject.toml={py!r}, '
        f'server.json.version={sj["version"]!r}, '
        f'server.json.packages[0].version={sj["packages"][0]["version"]!r}.'
    )
