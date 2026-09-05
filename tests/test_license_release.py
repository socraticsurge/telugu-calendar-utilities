"""Release-contract checks for the AGPL source and notice surface."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_and_mcp_metadata_publish_one_agpl_release() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    version_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)

    assert version_match is not None
    assert version_match.group(1) == "1.18.0"
    assert 'license = "AGPL-3.0-or-later"' in pyproject
    assert 'license-files = ["LICENSE", "THIRD_PARTY_NOTICES.md"]' in pyproject
    assert server["version"] == version_match.group(1)
    assert server["packages"][0]["version"] == version_match.group(1)
    assert "blob/master/LICENSE" in pyproject


def test_release_preserves_license_and_dependency_notices() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 19 November 2007" in license_text
    assert "PySwissEph 2.10.3.2" in notices
    assert "Copyright (c) 2007-2023 Stanislas Marquis" in notices
    assert "Swiss Ephemeris" in notices
    assert "Astrodienst AG" in notices


def test_network_ui_offers_source_and_license() -> None:
    landing = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "Source &amp; AGPL license" in landing
    assert "https://github.com/socraticsurge/telugu-calendar-utilities" in landing
