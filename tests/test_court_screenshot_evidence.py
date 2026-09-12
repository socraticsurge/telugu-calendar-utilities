"""Review-evidence checks for the Court assessor UI matrix."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = (
    ROOT / 'docs' / 'screenshots' / 'court-chart-assessor-2026-09-11'
)
MANIFEST = EVIDENCE_DIR / 'fixture-manifest.json'
SCENARIOS = {
    'court-pass',
    'court-preference-miss',
    'court-hard-fail',
    'court-unknown',
}
VIEWPORTS = {(390, 844), (1440, 900)}


def _png_size(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b'\x89PNG\r\n\x1a\n')
    assert payload[12:16] == b'IHDR'
    return struct.unpack('>II', payload[16:24])


def test_court_screenshot_manifest_is_complete_and_current():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    captures = manifest['captures']

    assert manifest['source'] == 'tools/capture_muhurta_chart_screenshots.py'
    assert manifest['liveServicesUsed'] is False
    assert len(captures) == 8
    assert {item['scenario'] for item in captures} == SCENARIOS
    assert {
        (item['viewport']['width'], item['viewport']['height'])
        for item in captures
    } == VIEWPORTS
    assert {item['expectedState'] for item in captures} == {
        'screened', 'screened-review',
    }
    assert len({item['expectedCopy'] for item in captures}) == 4

    filenames = [item['file'] for item in captures]
    assert len(filenames) == len(set(filenames))
    assert len({item['sha256'] for item in captures}) == len(captures)
    for item in captures:
        artifact = EVIDENCE_DIR / item['file']
        payload = artifact.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
        assert _png_size(payload) == (
            item['viewport']['width'], item['viewport']['height'],
        )
