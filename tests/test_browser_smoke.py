"""End-to-end browser smoke against docs/index.html.

This is the regression net the v1.8.0 hotfix would have benefited
from: even when every endpoint returns 200, the deployed page can
still fail at runtime if a referenced script defines functions the
inline code expects. A real browser load surfaces those errors
immediately as `ReferenceError` in the JS console.

This test is conditionally skipped when Playwright is not
installed locally — keep `pytest` runnable for dev environments
without the browser dependency. CI installs Playwright explicitly.

Install (one-time, ~120 MB):

    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import http.server
import socket
import socketserver
import threading
import time
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip(
    'playwright.sync_api',
    reason='Playwright not installed; install with `pip install playwright '
           '&& playwright install chromium` to run browser smoke tests.',
)
sync_playwright = playwright_sync.sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / 'docs'


def _pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Same as SimpleHTTPRequestHandler but doesn't spam stderr per
    request. Tests can be noisy enough already."""

    def log_message(self, format, *args):  # noqa: A002 (matches base API)
        return


@pytest.fixture(scope='module')
def docs_server():
    """Serve docs/ on a free localhost port for the duration of the
    module. Yields the base URL (http://127.0.0.1:PORT)."""
    port = _pick_free_port()
    handler = lambda *a, **kw: _QuietHandler(*a, directory=str(DOCS_DIR), **kw)
    httpd = socketserver.TCPServer(('127.0.0.1', port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        # Brief wait so the first request doesn't race the bind.
        time.sleep(0.1)
        yield f'http://127.0.0.1:{port}'
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            yield b
        finally:
            b.close()


def _capture_console(page):
    """Returns a list that page-error and console events will
    append to. The test then inspects the list."""
    captured = []
    page.on('pageerror', lambda exc: captured.append(('pageerror', str(exc))))
    page.on('console', lambda msg: (
        captured.append(('console.error', msg.text)) if msg.type == 'error'
        else None
    ))
    return captured


def test_index_loads_without_referenceerror(docs_server, browser):
    """The exact bug class of the v1.8.0 hotfix — a sidecar that
    404s makes every inline script call throw ReferenceError. If
    `muhurta-scorer.js` (or any future sidecar) is missing or its
    exports change, this test fails before deploy."""
    page = browser.new_page()
    captured = _capture_console(page)
    try:
        page.goto(docs_server, wait_until='networkidle', timeout=15000)
    finally:
        page.close()
    ref_errors = [
        msg for kind, msg in captured
        if 'ReferenceError' in msg or 'is not defined' in msg
    ]
    assert not ref_errors, (
        f'Browser load surfaced {len(ref_errors)} ReferenceError(s): '
        f'{ref_errors[:3]}'
    )


def test_muhurta_scorer_module_loads(docs_server, browser):
    """Stronger guard: assert the scorer module's exports are on
    window after page load. If the sidecar 404s OR the file silently
    fails to assign to window (browser parse error, syntax bug, etc.)
    this test catches it independently of any inline-script call."""
    page = browser.new_page()
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        # Wait until the scorer module had time to evaluate.
        for marker in ('muLagnaPosition', 'muLagnasInClass', 'muScoreTier',
                       'computePersonalDosha'):
            kind = page.evaluate(f"typeof window.{marker}")
            assert kind == 'function', (
                f'window.{marker} is {kind!r}, expected "function". '
                f'Check that muhurta-scorer.js is reachable and '
                f'exports the symbol.'
            )
    finally:
        page.close()


def test_muhurta_finder_search_does_not_throw_referenceerror(docs_server, browser):
    """Exercise the muhurta search end-to-end with a populated
    profile and assert (a) no ReferenceError in the JS console and
    (b) the result region doesn't fall into the catch-all
    "Could not load the feed" branch — that's the exact symptom
    the v1.8.0 hotfix surfaced (sidecar 404 → ReferenceError on
    every helper call → catch-all error message)."""
    page = browser.new_page()
    captured = _capture_console(page)
    try:
        page.goto(docs_server, wait_until='networkidle', timeout=15000)
        # Pre-populate a Tarabalam profile so the muhurta scorer's
        # lagna code paths (the ones that crashed in v1.8.0) actually
        # run. Without people set, scoring stays on the fast path.
        page.evaluate(
            "localStorage.setItem('tc-tb-profiles', JSON.stringify("
            "[{name:'Smoke',nak:'Krittika',pada:'1',lagna:'Mesha'}]));"
        )
        page.reload(wait_until='networkidle', timeout=15000)
        # The "Find slots" button calls findMuhurta() directly. Call
        # it via JS — deterministic vs synthesising click events on a
        # headless DOM. If the function isn't on window the test
        # FAILS (no skip): a renamed/removed entry-point is itself a
        # regression worth surfacing.
        kind = page.evaluate("typeof window.findMuhurta")
        assert kind == 'function', (
            f'window.findMuhurta should be the muhurta search entry-point '
            f'(see docs/index.html "Find slots" button onclick); got {kind!r}. '
            f'If the function was renamed, update this test in lockstep.'
        )
        page.evaluate('window.findMuhurta()')
        # Wait for either a rendered slot card OR the catch-all error
        # node to appear in #mu-result, with a generous timeout (the
        # search fetches the ICS feed + lagna data).
        page.wait_for_function(
            "document.querySelector('#mu-result') "
            "&& document.querySelector('#mu-result').innerHTML.trim().length > 0",
            timeout=20000,
        )
        # The page renders "Could not load the feed" when the search's
        # try/catch trips. That's the exact production symptom of the
        # v1.8.0 hotfix — assert it does NOT show up.
        result_html = page.locator('#mu-result').inner_html()
        assert 'Could not load the feed' not in result_html, (
            'muhurta search produced the catch-all "Could not load the '
            'feed" error. A ReferenceError likely tripped the try/catch '
            'block in findMuhurta(). Console events: '
            f'{[m for _, m in captured][:5]}'
        )
    finally:
        page.close()
    ref_errors = [
        msg for kind, msg in captured
        if 'ReferenceError' in msg or 'is not defined' in msg
    ]
    assert not ref_errors, (
        f'muhurta search surfaced ReferenceError(s): {ref_errors[:3]}'
    )
