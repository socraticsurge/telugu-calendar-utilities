#!/usr/bin/env python3
"""Capture the deterministic Karnavedha day/chart review matrix.

The scenarios reuse the built-site browser fixtures and never call a live
service. Run after ``npm run build``.
"""

from __future__ import annotations

import argparse
import hashlib
import http.server
import importlib.util
import json
import socket
import socketserver
import struct
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SMOKE_PATH = ROOT / 'tests' / 'test_browser_smoke.py'
OUTPUT_DIR = (
    ROOT / 'docs' / 'screenshots' / 'karnavedha-assessor-2026-09-04'
)


def _png_size(payload: bytes) -> tuple[int, int]:
    if payload[:8] != b'\x89PNG\r\n\x1a\n' or payload[12:16] != b'IHDR':
        raise ValueError('Captured evidence is not a PNG image.')
    return struct.unpack('>II', payload[16:24])


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location(
        'karnavedha_browser_smoke', SMOKE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load browser fixtures from {SMOKE_PATH}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _free_port() -> int:
    with socket.socket() as candidate:
        candidate.bind(('127.0.0.1', 0))
        return int(candidate.getsockname()[1])


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


@dataclass(frozen=True)
class Capture:
    scenario: str
    disposition: str
    width: int
    height: int
    expected_state: str
    expected_copy: str
    frame: str = 'overview'

    @property
    def filename(self) -> str:
        mode = 'mobile' if self.width < 600 else 'desktop'
        frame = '' if self.frame == 'overview' else f'-{self.frame}'
        return (
            f'fixture-{self.disposition}{frame}-{mode}-'
            f'{self.width}x{self.height}.png'
        )


SCENARIOS = (
    ('karnavedha-pass', 'pass', 'screened',
     'Karnavedha event checks resolved'),
    ('karnavedha-tithi-fail', 'tithi-fail', 'not-run',
     'Tithi changes at 12:00 inside local daylight'),
    ('karnavedha-nakshatra-fail', 'nakshatra-fail', 'not-run',
     'Nakshatra changes at 12:30 inside local daylight'),
    ('karnavedha-both-fail', 'both-fail', 'not-run',
     'Tithi changes at 12:00'),
    ('karnavedha-unknown', 'unknown', 'not-run',
     'Tithi boundary could not be verified'),
)
CAPTURES = tuple(
    Capture(scenario, disposition, width, height, state, copy)
    for scenario, disposition, state, copy in SCENARIOS
    for width, height in ((1440, 900), (390, 844))
) + tuple(
    Capture(
        'karnavedha-pass',
        'pass',
        width,
        height,
        'screened',
        '8th house is vacant',
        'candidate-chart',
    )
    for width, height in ((1440, 900), (390, 844))
)


def _capture(browser, smoke, base_url: str, capture: Capture) -> dict:
    page = browser.new_page(
        viewport={'width': capture.width, 'height': capture.height})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        smoke._run_muhurta_browser_search(
            page,
            base_url,
            capture.scenario,
            activity='karnavedha',
            system='drik',
        )
        result = page.locator('#mu-result')
        status = result.locator(
            f'.mu-chart-status--{capture.expected_state}')
        if status.count() != 1 or not status.is_visible():
            raise AssertionError(
                f'{capture.scenario}: missing {capture.expected_state}; '
                f'result={result.inner_text()[:800]!r}')
        if capture.disposition == 'pass':
            details = result.locator(
                '.mu-reason-details:has(.mu-rg-daylight)').first
            details.locator(':scope > summary').click()
        else:
            result.locator('.mu-dropped > summary').click()
        text = result.inner_text()
        assert capture.expected_copy in text, (
            f'{capture.scenario}: expected {capture.expected_copy!r}; '
            f'result={text[:1000]!r}')
        assert not errors, f'{capture.scenario}: page errors: {errors[:3]}'
        output = OUTPUT_DIR / capture.filename
        if capture.frame == 'candidate-chart':
            chart = result.locator('.mu-rg-computed').filter(
                has_text='8th house is vacant').first
            if chart.count() != 1 or not chart.is_visible():
                raise AssertionError(
                    f'{capture.scenario}: vacant-8th chart result is not visible')
            chart.screenshot(path=str(output))
            capture_kind = 'element'
        else:
            result.scroll_into_view_if_needed()
            page.screenshot(path=str(output), full_page=False)
            capture_kind = 'viewport'
        payload = output.read_bytes()
        image_width, image_height = _png_size(payload)
        return {
            'file': capture.filename,
            'scenario': capture.scenario,
            'activity': 'karnavedha',
            'system': 'drik',
            'viewport': {
                'width': capture.width,
                'height': capture.height,
            },
            'expectedState': capture.expected_state,
            'expectedCopy': capture.expected_copy,
            'frame': capture.frame,
            'captureKind': capture_kind,
            'imageSize': {
                'width': image_width,
                'height': image_height,
            },
            'sha256': hashlib.sha256(payload).hexdigest(),
        }
    finally:
        page.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    dist = args.dist.resolve()
    if not (dist / 'index.html').is_file():
        parser.error(f'{dist} does not contain index.html; build first')

    smoke = _load_smoke_module()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    port = _free_port()

    def handler(*handler_args, **handler_kwargs):
        return _QuietHandler(
            *handler_args, directory=str(dist), **handler_kwargs)

    server = socketserver.TCPServer(('127.0.0.1', port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f'http://127.0.0.1:{port}'
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                rows = [
                    _capture(browser, smoke, base_url, capture)
                    for capture in CAPTURES
                ]
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    manifest = {
        'capturedAt': datetime.now(timezone.utc).replace(
            microsecond=0).isoformat(),
        'source': 'tools/capture_karnavedha_assessor_screenshots.py',
        'liveServicesUsed': False,
        'policyId': 'raman-karnavedha-daylight-v1',
        'captures': rows,
    }
    (OUTPUT_DIR / 'fixture-manifest.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Captured {len(rows)} deterministic screenshots in {OUTPUT_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
