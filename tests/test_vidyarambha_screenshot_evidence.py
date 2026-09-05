"""Release-evidence checks for the Aksharabhyasa UI matrix."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = (
    REPO_ROOT
    / 'docs'
    / 'screenshots'
    / 'aksharabhyasa-chart-assessor-2026-09-05'
)
MANIFEST_PATH = EVIDENCE_DIR / 'fixture-manifest.json'
RESULT_SCENARIOS = {
    'vidyarambha-pass',
    'vidyarambha-preference-miss',
    'vidyarambha-hard-fail',
    'vidyarambha-unknown',
}
REQUIRED_SCENARIOS = RESULT_SCENARIOS | {'vidyarambha-selector'}
REQUIRED_VIEWPORTS = {(390, 844), (1440, 900)}


def _png_size(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b'\x89PNG\r\n\x1a\n')
    assert payload[12:16] == b'IHDR'
    return struct.unpack('>II', payload[16:24])


def test_aksharabhyasa_screenshot_manifest_is_complete_and_current():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    captures = manifest['captures']

    assert manifest['source'] == 'tools/capture_muhurta_chart_screenshots.py'
    assert manifest['liveServicesUsed'] is False
    assert len(captures) == 10
    assert {item['scenario'] for item in captures} == REQUIRED_SCENARIOS
    assert {item['activity'] for item in captures} == {'vidyarambha'}
    assert {item['system'] for item in captures} == {'drik'}
    assert {
        (item['viewport']['width'], item['viewport']['height'])
        for item in captures
    } == REQUIRED_VIEWPORTS
    for scenario in REQUIRED_SCENARIOS:
        assert {
            (item['viewport']['width'], item['viewport']['height'])
            for item in captures if item['scenario'] == scenario
        } == REQUIRED_VIEWPORTS

    assert {
        item['expectedState'] for item in captures
    } == {'screened', 'pre-search'}
    assert {
        item['expectedCopy']
        for item in captures
        if item['scenario'] == 'vidyarambha-selector'
    } == {'Aksharabhyasa (First-letter writing)'}
    assert {
        item['expectedCopy']
        for item in captures
        if item['scenario'] == 'vidyarambha-preference-miss'
    } == {'Preference not present · no penalty'}
    assert {
        item['expectedCopy']
        for item in captures
        if item['scenario'] == 'vidyarambha-hard-fail'
    } == {'House 8 occupants: Surya.'}

    filenames = [item['file'] for item in captures]
    assert len(filenames) == len(set(filenames))
    assert {
        path.name for path in EVIDENCE_DIR.glob('*.png')
    } == set(filenames)
    for item in captures:
        path = EVIDENCE_DIR / item['file']
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
        assert _png_size(payload) == (
            item['viewport']['width'], item['viewport']['height'],
        )
