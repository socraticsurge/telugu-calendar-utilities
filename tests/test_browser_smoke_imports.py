"""Protect the two nonstandard import paths used by browser smoke consumers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_screenshot_loader_resolves_smoke_package_outside_repository(tmp_path):
    script = """
import importlib.util
import sys
from pathlib import Path

root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location(
    'capture', root / 'tools/capture_muhurta_chart_screenshots.py',
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
try:
    spec.loader.exec_module(module)
except ModuleNotFoundError as error:
    if error.name.startswith('playwright'):
        sys.exit(0)  # The capture tool is optional in Python-only installations.
    raise
before = list(sys.path)
smoke = module._load_smoke_module()
assert sys.path == before
assert smoke.REPO_ROOT == root
assert smoke.MUHURTA_FIXTURE_DATE == '2026-06-11'
for name in (
    '_install_direct_route_runtime_assets', '_keep_profile_smoke_offline',
    '_wait_for_profile_app', '_run_muhurta_browser_search',
):
    assert callable(getattr(smoke, name))
"""
    result = subprocess.run(
        [sys.executable, '-I', '-c', script, str(ROOT)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_smoke_without_playwright_skips_instead_of_breaking_collection(tmp_path):
    script = """
import importlib.abc
import sys
import pytest

class NoPlaywright(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('playwright'):
            raise ModuleNotFoundError('No module named playwright', name=fullname)

sys.path.insert(0, sys.argv[1])
sys.meta_path.insert(0, NoPlaywright())
try:
    import tests.test_browser_smoke
except pytest.skip.Exception as error:
    assert 'Playwright not installed' in str(error)
else:
    raise AssertionError('Missing Playwright must skip the browser module')
"""
    result = subprocess.run(
        [sys.executable, '-I', '-c', script, str(ROOT)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
