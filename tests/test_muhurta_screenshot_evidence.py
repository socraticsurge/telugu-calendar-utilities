"""Release-evidence checks for the deterministic Muhurtam UI matrix."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = (
    REPO_ROOT / 'docs' / 'screenshots' / 'muhurtam-chart-screening-2026-08-29'
)
MANIFEST_PATH = EVIDENCE_DIR / 'fixture-manifest.json'
REQUIRED_SCENARIOS = {
    'positive',
    'mixed',
    'failure',
    'manual-only',
    'unsupported',
    'offline',
    'malformed',
    'loading',
    'timeout',
}
REQUIRED_VIEWPORTS = {(390, 844), (768, 1024), (1024, 768), (1440, 900)}


def _png_size(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b'\x89PNG\r\n\x1a\n')
    assert payload[12:16] == b'IHDR'
    return struct.unpack('>II', payload[16:24])


def test_muhurtam_screenshot_manifest_is_complete_and_current():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    captures = manifest['captures']

    assert manifest['source'] == 'tools/capture_muhurta_chart_screenshots.py'
    assert manifest['liveServicesUsed'] is False
    assert len(captures) == 10
    assert {item['scenario'] for item in captures} == REQUIRED_SCENARIOS
    assert {
        (item['viewport']['width'], item['viewport']['height'])
        for item in captures
    } == REQUIRED_VIEWPORTS

    filenames = [item['file'] for item in captures]
    assert len(filenames) == len(set(filenames))
    for item in captures:
        path = EVIDENCE_DIR / item['file']
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
        assert _png_size(payload) == (
            item['viewport']['width'], item['viewport']['height'],
        )
