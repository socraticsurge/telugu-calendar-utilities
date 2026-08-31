"""End-to-end browser smoke against the built Vite site (dist/).

This is the regression net the v1.8.0 hotfix would have benefited
from: even when every endpoint returns 200, the deployed page can
still fail at runtime if the bundle omits functions the page
expects. A real browser load surfaces those errors immediately as
`ReferenceError` in the JS console.

The fixture runs `npm run build` (tsc --noEmit + vite build) so the
tests exercise the exact bytes deploy-landing.yml publishes — NOT a
source checkout. Pre-Vite this file served the old docs/index.html
mega-page; that page is deleted and this net now watches dist/.

This test is conditionally skipped when Playwright or npm is not
installed locally — keep `pytest` runnable for dev environments
without the browser/Node dependency. CI installs both explicitly.

Install (one-time, ~120 MB):

    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import http.server
import shutil
import socket
import socketserver
import subprocess
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
DIST_DIR = REPO_ROOT / 'dist'


@pytest.fixture(scope='module')
def vite_build():
    """Build the site into dist/ with the same command the deploy
    workflows use. Skips (not fails) when npm is unavailable so
    Python-only dev environments keep a green `pytest`; a FAILING
    build, however, fails loudly — that's a real regression."""
    npm = shutil.which('npm')
    if npm is None:
        pytest.skip('npm not installed; browser smoke needs the Vite build.')
    if not (REPO_ROOT / 'node_modules').is_dir():
        subprocess.run([npm, 'ci'], cwd=REPO_ROOT, check=True,
                       capture_output=True, text=True)
    proc = subprocess.run([npm, 'run', 'build'], cwd=REPO_ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0, (
        f'`npm run build` failed (exit {proc.returncode}) — the smoke '
        f'tests exercise dist/, so a broken build is a broken site.\n'
        f'stdout: {proc.stdout[-2000:]}\nstderr: {proc.stderr[-2000:]}'
    )
    assert (DIST_DIR / 'index.html').is_file(), (
        'npm run build succeeded but dist/index.html is missing — '
        'check vite.config.ts build.outDir.'
    )
    return DIST_DIR


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
def docs_server(vite_build):
    """Serve the freshly built dist/ on a free localhost port for the
    duration of the module. Yields the base URL (http://127.0.0.1:PORT).
    (Fixture name kept from the docs/-serving era so the test diff
    stays reviewable; it now serves the deploy artifact.)"""
    port = _pick_free_port()
    handler = lambda *a, **kw: _QuietHandler(*a, directory=str(vite_build), **kw)
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


def test_inline_onclick_surface_is_on_window(docs_server, browser):
    """Stronger guard: every function referenced by an inline
    onclick/onchange attribute in index.html MUST be assigned to
    window by the bundle (modules are scoped; inline handlers look
    names up on window). If the Object.assign(window, {...}) block
    in src/main.ts drops one — or the bundle fails to evaluate —
    the matching button dies silently in production. Scorer-module
    internals are separately covered by the Vitest suite
    (src/scorer/__tests__/muhurta-scorer.test.ts)."""
    page = browser.new_page()
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        # Wait until the bundle had time to evaluate.
        for marker in ('switchTool', 'setTimeFmt', 'calcTarabalam',
                       'findMuhurta', 'renderGochara',
                       'shareTodayOnWhatsApp'):
            kind = page.evaluate(f"typeof window.{marker}")
            assert kind == 'function', (
                f'window.{marker} is {kind!r}, expected "function". '
                f'Check the Object.assign(window, {{...}}) block in '
                f'src/main.ts — inline onclick handlers depend on it.'
            )
    finally:
        page.close()


@pytest.mark.parametrize(
    ('width', 'height', 'expected_mode'),
    (
        (390, 844, 'mobile'),
        (768, 1024, 'mobile'),
        (1024, 768, 'desktop'),
        (1440, 900, 'desktop'),
    ),
)
def test_daily_surface_is_responsive_and_navigation_remains_usable(
    docs_server, browser, width, height, expected_mode,
):
    """Guard the reviewed IA at the four product breakpoints.

    The day-cycle presentation must not introduce horizontal overflow, and
    Documentation must remain reachable from the same navigation in both the
    fixed desktop shell and mobile drawer.
    """
    page = browser.new_page(viewport={'width': width, 'height': height})
    try:
        page.goto(docs_server, wait_until='networkidle', timeout=15000)
        page.wait_for_selector('.day-cycle', timeout=10000)
        metrics = page.evaluate(
            """() => ({
                mode: document.body.dataset.mode,
                overflow: document.documentElement.scrollWidth
                    - document.documentElement.clientWidth,
                cycleGroups: document.querySelectorAll('.day-cycle-group').length,
                helpButton: Boolean(document.querySelector('.m-page-help-btn')),
            })"""
        )
        assert metrics['mode'] == expected_mode
        assert metrics['overflow'] <= 0
        assert metrics['cycleGroups'] == 2
        assert metrics['helpButton'] is False

        docs_link = page.locator('#sidebar a[href="/docs/"]')
        if expected_mode == 'mobile':
            nav_button = page.locator('#m-nav-btn')
            box = nav_button.bounding_box()
            assert box and box['width'] >= 44 and box['height'] >= 44
            nav_button.click()
            assert 'm-nav-open' in page.locator('body').get_attribute('class').split()
            assert docs_link.is_visible()
            page.keyboard.press('Escape')
            assert 'm-nav-open' not in (page.locator('body').get_attribute('class') or '').split()
        else:
            assert docs_link.is_visible()

        for control, expected_hash, expected_card in (
            ('#sidebar-useinai', '#useinai', '#card-mcp'),
            ('#sidebar-about', '#about', '#card-about'),
        ):
            if expected_mode == 'mobile':
                nav_button.click()
            page.locator(control).click()
            assert page.evaluate('location.hash') == expected_hash
            assert 'active' in page.locator(control).get_attribute('class').split()
            assert page.locator(expected_card).is_visible()
            assert page.evaluate('document.body.dataset.tool') == expected_hash[1:]
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
            f'(see the "Find slots" button onclick in index.html); got {kind!r}. '
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
        # Stronger: a successful search must render a tier badge (or the
        # legitimate no-slots message) — a blank-but-no-error result is
        # exactly how a silent render bug would present.
        import re as _re
        assert _re.search(r'Excellent|Good|Fair|Avoid|[Nn]o .*slots', result_html), (
            'muhurta search rendered neither tier badges nor a no-slots '
            f'message. First 300 chars: {result_html[:300]!r}'
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


def test_daily_horoscope_contextual_profile_returns_and_stays_isolated(
    docs_server, browser,
):
    """A first-time guest can create the exact profile Daily Horoscope needs.

    The new profile must become the active Horoscope view without silently
    becoming a Muhurtam participant, and analytics must remain content-free.
    """
    page = browser.new_page()
    captured = _capture_console(page)
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        page.evaluate('localStorage.clear()')
        page.reload(wait_until='domcontentloaded', timeout=15000)
        page.evaluate(
            "window.__profileEvents = []; window.goatcounter = {"
            "count: event => window.__profileEvents.push(event)}"
        )

        page.evaluate("window.switchTool('gochara')")
        page.locator('[data-go-profile-action="create"]').click()
        assert page.locator('body').get_attribute('data-tool') == 'profiles'

        page.fill('#profile-name', 'Browser Ananya')
        page.locator('button[type="submit"]').click()
        assert page.locator('#profile-nakshatra-error').is_visible()
        assert 'Nakshatra' in page.locator('#profile-nakshatra-error').inner_text()

        page.select_option('#profile-nakshatra', 'Krittika')
        page.locator('button[type="submit"]').click()
        assert page.locator('#profile-pada-error').is_visible()
        assert 'spans two Rashis' in page.locator('#profile-pada-error').inner_text()

        page.select_option('#profile-pada', '2')
        page.locator('button[type="submit"]').click()
        page.wait_for_function("document.body.dataset.tool === 'gochara'")

        selected = page.input_value('#go-view')
        assert selected.startswith('profile:')
        assert "Using Browser Ananya's saved birth star" in page.locator(
            '#go-profile-state'
        ).inner_text()
        assert page.evaluate(
            "localStorage.getItem('tc-mu-profile-ids')"
        ) == '[]'
        assert page.evaluate('document.activeElement.id') == 'go-view'

        events = page.evaluate('window.__profileEvents')
        event_text = str(events)
        assert 'Browser Ananya' not in event_text
        assert 'Krittika' not in event_text
        assert selected.removeprefix('profile:') not in event_text
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'contextual Horoscope surfaced errors: {app_errors[:3]}'


def test_muhurta_contextual_profile_preserves_task_and_other_journey(
    docs_server, browser,
):
    """Muhurtam contextual create/select is origin-scoped and cancellable."""
    page = browser.new_page()
    captured = _capture_console(page)
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        page.evaluate('localStorage.clear()')
        page.reload(wait_until='domcontentloaded', timeout=15000)
        page.evaluate("window.switchTool('tarabalam')")
        page.select_option('#mu-activity', 'wedding')

        page.locator('#tb-profiles [data-action="create-profile"]').click()
        page.fill('#profile-name', 'Browser Ravi')
        page.locator('button[type="submit"]').click()
        assert page.locator('#profile-nakshatra-error').is_visible()
        page.select_option('#profile-nakshatra', 'Ashvini')
        page.locator('button[type="submit"]').click()
        page.wait_for_function("document.body.dataset.tool === 'tarabalam'")

        checked = page.locator('input[data-profile-selection]:checked')
        assert checked.count() == 1
        selected_id = checked.get_attribute('value')
        assert selected_id
        assert page.evaluate(
            "localStorage.getItem('tc-mu-profile-ids')"
        ) == f'["{selected_id}"]'
        assert not (page.evaluate(
            "localStorage.getItem('tc-go-view') || ''"
        )).startswith('profile:')
        assert page.input_value('#mu-activity') == 'wedding'
        assert page.evaluate(
            "document.activeElement.dataset.profileSelection"
        ) == selected_id

        page.locator('#tb-profiles [data-action="create-profile"]').click()
        page.fill('#profile-name', 'Do not save')
        page.get_by_role('button', name='Cancel').click()
        page.wait_for_function("document.body.dataset.tool === 'tarabalam'")

        assert page.input_value('#mu-activity') == 'wedding'
        assert page.locator('input[data-profile-selection]:checked').count() == 1
        assert page.locator('#tb-profiles [data-profile-id]').count() == 1
        assert page.evaluate(
            "localStorage.getItem('tc-mu-profile-ids')"
        ) == f'["{selected_id}"]'
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'contextual Muhurtam surfaced errors: {app_errors[:3]}'


def test_gochara_rasi_view_renders_verdicts_and_phalalu(docs_server, vite_build, browser):
    """The regression class this guards: a module-scoped constant left
    behind by the panel extraction turns the gochara RASI view into a
    silent no-op (ReferenceError swallowed by the inline onchange), while
    the default whole-sky view keeps working — exactly what shipped on
    2026-07-18 (CHANDRA_GOOD/rasiFromStar/todayISO undefined in
    panels/gochara.ts). Drives the lazy path: load gochara, choose a
    rasi, and require the phalalu box to render actual content.

    gochara.json isn't part of the Vite build (it lives on gh-pages), so
    stage the production copy into dist/; skip — not fail — when that
    network fetch is unavailable.
    """
    import urllib.request
    dst = vite_build / 'gochara.json'
    if not dst.exists():
        try:
            with urllib.request.urlopen(
                    'https://panchangam.astrochaganti.com/gochara.json',
                    timeout=15) as r:
                dst.write_bytes(r.read())
        except OSError:
            pytest.skip('gochara.json unavailable (offline?) — cannot stage sky data')

    page = browser.new_page()
    captured = _capture_console(page)
    try:
        page.goto(docs_server, wait_until='networkidle', timeout=15000)
        page.evaluate("window.switchTool('gochara')")
        page.wait_for_function(
            "document.getElementById('go-view') && "
            "document.getElementById('go-view').options.length > 1",
            timeout=15000,
        )
        page.select_option('#go-view', '0')  # Mesha — the lazy path
        page.wait_for_function(
            "document.getElementById('go-phalalu') && "
            "document.getElementById('go-phalalu').textContent.trim().length > 0",
            timeout=10000,
        )
        # inner_text() reflects CSS text-transform (headings render
        # uppercased) — compare case-insensitively.
        ph = page.locator('#go-phalalu').inner_text()
        assert 'rasi phalalu' in ph.lower(), (
            f'phalalu box rendered but without a reading: {ph[:200]!r}')
        legend = page.locator('#go-legend').inner_text()
        assert 'favourable' in legend, 'verdict legend missing for a rasi view'
    finally:
        page.close()
    ref_errors = [m for kind, m in captured
                  if 'ReferenceError' in m or 'is not defined' in m]
    assert not ref_errors, f'rasi view surfaced ReferenceError(s): {ref_errors[:3]}'
