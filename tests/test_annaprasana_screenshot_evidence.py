"""Review-evidence checks for the Annaprasana assessor UI matrix."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = (
    ROOT / 'docs' / 'screenshots' /
    'annaprasana-chart-assessor-2026-09-04'
)
MANIFEST = EVIDENCE_DIR / 'fixture-manifest.json'
SCENARIOS = {
    'annaprasana-pass',
    'annaprasana-preference-miss',
    'annaprasana-hard-fail',
    'annaprasana-unknown',
}
VIEWPORTS = {(390, 844), (1440, 900)}


def _png_size(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b'\x89PNG\r\n\x1a\n')
    assert payload[12:16] == b'IHDR'
    return struct.unpack('>II', payload[16:24])


def test_annaprasana_screenshot_manifest_is_complete_and_current():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    captures = manifest['captures']

    assert manifest['source'] == 'tools/capture_muhurta_chart_screenshots.py'
    assert manifest['liveServicesUsed'] is False
    assert len(captures) == 9
    assert {item['scenario'] for item in captures} == SCENARIOS
    assert {
        (item['viewport']['width'], item['viewport']['height'])
        for item in captures
    } == VIEWPORTS
    assert len({item['expectedCopy'] for item in captures}) == 5

    mobile_pass = {
        item['file']: item
        for item in captures
        if item['scenario'] == 'annaprasana-pass'
        and item['viewport'] == {'width': 390, 'height': 844}
    }
    assert mobile_pass[
        'fixture-annaprasana-pass-mobile-390x844.png'
    ]['expectedCopy'] == (
        'Annaprasana event-specific chart assessment complete'
    )
    final_outcomes = mobile_pass[
        'fixture-annaprasana-pass-final-outcomes-mobile-390x844.png'
    ]
    assert final_outcomes['expectedCopy'] == 'Preference met · tie-break only'
    assert final_outcomes['additionalExpectedCopy'] == (
        'Natural malefics in Lagna: none; Chandra is outside Lagna.'
    )

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
