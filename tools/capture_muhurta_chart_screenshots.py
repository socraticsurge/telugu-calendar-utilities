#!/usr/bin/env python3
"""Capture the deterministic Muhurtam chart-screening review matrix.

This script reuses the browser fixtures that protect the deployable Vite bundle.
It writes review evidence only; it does not call a live chart service.

Usage:
    python tools/capture_muhurta_chart_screenshots.py --dist dist
"""

from __future__ import annotations

import argparse
import hashlib
import http.server
import importlib.util
import json
import socket
import socketserver
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_PATH = REPO_ROOT / 'tests' / 'test_browser_smoke.py'
OUTPUT_DIR = (
    REPO_ROOT / 'docs' / 'screenshots' / 'gold-chart-screening-2026-09-04'
)


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location('muhurta_browser_smoke', SMOKE_PATH)
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
    filename: str
    scenario: str
    activity: str
    system: str
    width: int
    height: int
    expected_state: str
    expected_copy: str


CAPTURES = (
    Capture(
        'fixture-positive-purchase-desktop-1440x900.png',
        'positive', 'purchase', 'drik', 1440, 900, 'screened',
        'Exact chart screening applied',
    ),
    Capture(
        'fixture-positive-purchase-mobile-390x844.png',
        'positive', 'purchase', 'drik', 390, 844, 'screened',
        'Exact chart screening applied',
    ),
    Capture(
        'fixture-mixed-rule-unknown-tablet-768x1024.png',
        'mixed', 'purchase', 'drik', 768, 1024, 'screened',
        'changed within this window',
    ),
    Capture(
        'fixture-travel-mandatory-failure-desktop-1440x900.png',
        'failure', 'travel', 'drik', 1440, 900, 'screened',
        'failed an exact chart requirement',
    ),
    Capture(
        'fixture-gold-pass-desktop-1440x900.png',
        'gold-pass', 'gold', 'drik', 1440, 900, 'screened',
        'Gold event-specific chart clauses resolved',
    ),
    Capture(
        'fixture-gold-pass-mobile-390x844.png',
        'gold-pass', 'gold', 'drik', 390, 844, 'screened',
        'Gold event-specific chart clauses resolved',
    ),
    Capture(
        'fixture-gold-cap-desktop-1440x900.png',
        'gold-cap', 'gold', 'drik', 1440, 900, 'screened-capped',
        'Condition not met',
    ),
    Capture(
        'fixture-gold-cap-mobile-390x844.png',
        'gold-cap', 'gold', 'drik', 390, 844, 'screened-capped',
        'Condition not met',
    ),
    Capture(
        'fixture-gold-unknown-desktop-1440x900.png',
        'gold-unknown', 'gold', 'drik', 1440, 900, 'screened-review',
        'Indeterminate at calculation boundary',
    ),
    Capture(
        'fixture-gold-unknown-mobile-390x844.png',
        'gold-unknown', 'gold', 'drik', 390, 844, 'screened-review',
        'Indeterminate at calculation boundary',
    ),
    Capture(
        'fixture-unsupported-system-tablet-landscape-1024x768.png',
        'unsupported', 'purchase', 'surya-siddhanta', 1024, 768,
        'unsupported-system', 'Selected system kept separate',
    ),
    Capture(
        'fixture-offline-unavailable-mobile-390x844.png',
        'offline', 'purchase', 'drik', 390, 844, 'unavailable',
        'Panchangam shortlist shown',
    ),
    Capture(
        'fixture-malformed-response-unavailable-desktop-1440x900.png',
        'malformed', 'purchase', 'drik', 1440, 900, 'unavailable',
        'Panchangam shortlist shown',
    ),
)


PENDING_FETCH_SCRIPT = """
(() => {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const url = typeof input === 'string' ? input : input.url;
    if (url.includes('/api/guest/muhurta/election-charts')) {
      return new Promise((resolve, reject) => {
        const signal = init.signal;
        const abort = () => reject(new DOMException('Aborted', 'AbortError'));
        if (signal?.aborted) abort();
        else signal?.addEventListener('abort', abort, { once: true });
      });
    }
    return originalFetch(input, init);
  };
})();
"""


def _configure_search(page, smoke, base_url: str, activity: str) -> None:
    smoke._install_direct_route_runtime_assets(page)
    smoke._keep_profile_smoke_offline(page)
    page.goto(f'{base_url}#tarabalam', wait_until='domcontentloaded', timeout=15000)
    smoke._wait_for_profile_app(page)
    page.locator('#tp-system').evaluate(
        """(select) => {
            select.value = 'drik';
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.select_option('#mu-activity', activity)
    page.fill('#tb-from', smoke.MUHURTA_FIXTURE_DATE)
    page.fill('#tb-to', smoke.MUHURTA_FIXTURE_DATE)


def _capture_page(page, path: Path, anchor: str = '#mu-result') -> None:
    page.locator(anchor).scroll_into_view_if_needed()
    page.screenshot(path=str(path), full_page=False)


def _capture_regular(browser, smoke, base_url: str, capture: Capture) -> dict:
    page = browser.new_page(viewport={'width': capture.width, 'height': capture.height})
    try:
        smoke._run_muhurta_browser_search(
            page,
            base_url,
            capture.scenario,
            activity=capture.activity,
            system=capture.system,
        )
        result = page.locator('#mu-result')
        status = result.locator(f'.mu-chart-status--{capture.expected_state}')
        if status.count() != 1 or not status.is_visible():
            classes = result.locator('.mu-chart-status').all()
            actual = [item.get_attribute('class') for item in classes]
            raise AssertionError(
                f'{capture.scenario} expected {capture.expected_state}; '
                f'actual status classes were {actual}; result={result.inner_text()[:800]!r}'
            )
        detail_selector = None
        if capture.scenario == 'positive' or capture.scenario in {
            'gold-pass', 'gold-cap', 'gold-unknown',
        }:
            detail_selector = '.mu-reason-details:has(.mu-rg-computed)'
        elif capture.scenario == 'mixed':
            detail_selector = '.mu-reason-details:has(.mu-chart-rule--unknown)'
        if detail_selector and result.locator(detail_selector).count():
            result.locator(detail_selector).first.locator('summary').first.click()

        result_text = result.text_content() or ''
        assert capture.expected_copy in result_text, (
            f'{capture.scenario} expected copy {capture.expected_copy!r}; '
            f'result={result_text[:1000]!r}'
        )
        output = OUTPUT_DIR / capture.filename
        _capture_page(page, output)
        return _manifest_row(capture, output)
    finally:
        page.close()


def _capture_loading_and_timeout(browser, smoke, base_url: str) -> list[dict]:
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.add_init_script(PENDING_FETCH_SCRIPT)
    rows: list[dict] = []
    try:
        _configure_search(page, smoke, base_url, 'purchase')
        page.get_by_role('button', name='Show Slots', exact=True).click()
        busy = page.locator('#mu-result[aria-busy="true"]')
        busy.wait_for(state='visible', timeout=15000)
        page.wait_for_function(
            "document.querySelector('#mu-result')?.textContent.includes('Shortlist ready')",
            timeout=15000,
        )
        busy_text = busy.inner_text()
        assert 'screening exact election charts' in busy_text.lower(), busy_text
        loading = Capture(
            'fixture-chart-screening-loading-desktop-1440x900.png',
            'loading', 'purchase', 'drik', 1440, 900, 'loading',
            'screening exact election charts',
        )
        loading_path = OUTPUT_DIR / loading.filename
        _capture_page(page, loading_path)
        rows.append(_manifest_row(loading, loading_path))

        unavailable = page.locator('#mu-result .mu-chart-status--unavailable')
        unavailable.wait_for(state='visible', timeout=25000)
        assert page.locator('#mu-result').get_attribute('aria-busy') == 'false'
        assert 'Panchangam shortlist shown' in unavailable.inner_text()
        timeout = Capture(
            'fixture-timeout-unavailable-tablet-768x1024.png',
            'timeout', 'purchase', 'drik', 768, 1024, 'unavailable',
            'Panchangam shortlist shown',
        )
        page.set_viewport_size({'width': timeout.width, 'height': timeout.height})
        timeout_path = OUTPUT_DIR / timeout.filename
        _capture_page(page, timeout_path, '.mu-chart-status--unavailable')
        rows.append(_manifest_row(timeout, timeout_path))
        return rows
    finally:
        page.close()


def _manifest_row(capture: Capture, path: Path) -> dict:
    return {
        'file': capture.filename,
        'scenario': capture.scenario,
        'activity': capture.activity,
        'system': capture.system,
        'viewport': {'width': capture.width, 'height': capture.height},
        'expectedState': capture.expected_state,
        'expectedCopy': capture.expected_copy,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist', type=Path, default=REPO_ROOT / 'dist')
    args = parser.parse_args()
    dist = args.dist.resolve()
    if not (dist / 'index.html').is_file():
        parser.error(f'{dist} does not contain index.html; build the site first')

    smoke = _load_smoke_module()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    port = _free_port()
    def handler(*handler_args, **handler_kwargs):
        return _QuietHandler(
            *handler_args, directory=str(dist), **handler_kwargs,
        )

    server = socketserver.TCPServer(('127.0.0.1', port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Keep the origin byte-exact: the fixture's CORS response echoes this
    # value, and browser origins never include a trailing slash.
    base_url = f'http://127.0.0.1:{port}'

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                rows = [
                    _capture_regular(browser, smoke, base_url, capture)
                    for capture in CAPTURES
                ]
                rows.extend(_capture_loading_and_timeout(browser, smoke, base_url))
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    manifest = {
        'capturedAt': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        'source': 'tools/capture_muhurta_chart_screenshots.py',
        'liveServicesUsed': False,
        'captures': rows,
    }
    (OUTPUT_DIR / 'fixture-manifest.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8'
    )
    print(f'Captured {len(rows)} deterministic screenshots in {OUTPUT_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
