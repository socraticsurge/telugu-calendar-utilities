"""Release-evidence checks for the deterministic Muhurtam UI matrix."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = (
    REPO_ROOT / 'docs' / 'screenshots' / 'gold-chart-screening-2026-09-04'
)
MANIFEST_PATH = EVIDENCE_DIR / 'fixture-manifest.json'
REQUIRED_SCENARIOS = {
    'positive',
    'mixed',
    'failure',
    'gold-pass',
    'gold-cap',
    'gold-unknown',
    'unsupported',
    'offline',
    'malformed',
    'loading',
    'timeout',
}
REQUIRED_VIEWPORTS = {(390, 844), (768, 1024), (1024, 768), (1440, 900)}
KARNAVEDHA_EVIDENCE_DIR = (
    REPO_ROOT / 'docs' / 'screenshots' / 'karnavedha-assessor-2026-09-04'
)


def _png_size(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b'\x89PNG\r\n\x1a\n')
    assert payload[12:16] == b'IHDR'
    return struct.unpack('>II', payload[16:24])


def test_muhurtam_screenshot_manifest_is_complete_and_current():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    captures = manifest['captures']

    assert manifest['source'] == 'tools/capture_muhurta_chart_screenshots.py'
    assert manifest['liveServicesUsed'] is False
    assert len(captures) == 15
    assert {item['scenario'] for item in captures} == REQUIRED_SCENARIOS
    assert {
        (item['viewport']['width'], item['viewport']['height'])
        for item in captures
    } == REQUIRED_VIEWPORTS
    for scenario in ('gold-pass', 'gold-cap', 'gold-unknown'):
        assert {
            (item['viewport']['width'], item['viewport']['height'])
            for item in captures if item['scenario'] == scenario
        } == {(390, 844), (1440, 900)}

    assert {
        item['expectedState']
        for item in captures if item['scenario'] == 'gold-pass'
    } == {'screened'}
    assert {
        item['expectedState']
        for item in captures if item['scenario'] == 'gold-cap'
    } == {'screened-capped'}
    assert {
        item['expectedState']
        for item in captures if item['scenario'] == 'gold-unknown'
    } == {'screened-review'}

    filenames = [item['file'] for item in captures]
    assert len(filenames) == len(set(filenames))
    for item in captures:
        path = EVIDENCE_DIR / item['file']
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
        assert _png_size(payload) == (
            item['viewport']['width'], item['viewport']['height'],
        )


def test_karnavedha_screenshot_manifest_covers_every_daylight_disposition():
    manifest = json.loads(
        (KARNAVEDHA_EVIDENCE_DIR / 'fixture-manifest.json').read_text(
            encoding='utf-8'))
    captures = manifest['captures']

    assert manifest['source'] == (
        'tools/capture_karnavedha_assessor_screenshots.py')
    assert manifest['liveServicesUsed'] is False
    assert manifest['policyId'] == 'raman-karnavedha-daylight-v1'
    assert len(captures) == 12
    assert {item['scenario'] for item in captures} == {
        'karnavedha-pass',
        'karnavedha-tithi-fail',
        'karnavedha-nakshatra-fail',
        'karnavedha-both-fail',
        'karnavedha-unknown',
    }
    for scenario in {item['scenario'] for item in captures}:
        assert {
            (item['viewport']['width'], item['viewport']['height'])
            for item in captures if item['scenario'] == scenario
        } == {(390, 844), (1440, 900)}
    assert {
        item['expectedState']
        for item in captures if item['scenario'] == 'karnavedha-pass'
    } == {'screened'}
    assert {
        item['expectedState']
        for item in captures if item['scenario'] != 'karnavedha-pass'
    } == {'not-run'}
    chart_frames = [
        item for item in captures if item['frame'] == 'candidate-chart'
    ]
    assert len(chart_frames) == 2
    assert {item['scenario'] for item in chart_frames} == {'karnavedha-pass'}
    assert {item['expectedCopy'] for item in chart_frames} == {
        '8th house is vacant',
    }
    assert {item['captureKind'] for item in chart_frames} == {'element'}
    assert {
        (item['viewport']['width'], item['viewport']['height'])
        for item in chart_frames
    } == {(390, 844), (1440, 900)}
    assert all(
        'candidate-chart' in item['file'] for item in chart_frames
    )

    for item in captures:
        path = KARNAVEDHA_EVIDENCE_DIR / item['file']
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256']
        image_size = _png_size(payload)
        assert image_size == (
            item['imageSize']['width'], item['imageSize']['height'],
        )
        if item['captureKind'] == 'viewport':
            assert image_size == (
                item['viewport']['width'], item['viewport']['height'],
            )
        else:
            assert 0 < image_size[0] <= item['viewport']['width']
            assert 0 < image_size[1] <= item['viewport']['height']
