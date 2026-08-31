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


PROFILE_VIEWPORTS = (
    (390, 844, 'mobile'),
    (768, 1024, 'mobile'),
    (1024, 768, 'desktop'),
    (1440, 900, 'desktop'),
)

HOSTILE_PROFILE_NAME = (
    '<img src=x onerror="window.__hostileExecuted=true"> Ready'
)
LONG_PROFILE_NAME = 'N' * 80
READY_PROFILE_ID = 'guest_ready_001'
INCOMPLETE_PROFILE_ID = 'guest_needs_001'


def _profile_rows():
    """Exact persisted v1 shape used by the browser profile store.

    The first name is deliberately executable if a renderer ever regresses to
    innerHTML. Every personalized surface must preserve it as literal text.
    """
    return [
        {
            'id': READY_PROFILE_ID,
            'schemaVersion': 1,
            'name': HOSTILE_PROFILE_NAME,
            'nak': 'Rohini',
            'pada': '',
            'lagna': 'Kanya',
        },
        {
            'id': INCOMPLETE_PROFILE_ID,
            'schemaVersion': 1,
            'name': LONG_PROFILE_NAME,
            'nak': '',
            'pada': '',
            'lagna': '',
        },
    ]


def _keep_profile_smoke_offline(target):
    """Make profile smoke deterministic without hiding local build failures."""
    target.route(
        'https://gc.zgo.at/**',
        lambda route: route.fulfill(
            status=200,
            content_type='application/javascript',
            body='',
        ),
    )
    target.route(
        'https://panchangam.goatcounter.com/**',
        lambda route: route.fulfill(status=204, body=''),
    )
    target.route(
        'https://panchangam.astrochaganti.com/**',
        lambda route: route.fulfill(
            status=404,
            content_type='application/json',
            body='{}',
        ),
    )


def _wait_for_profile_app(page):
    page.wait_for_function(
        "typeof window.switchTool === 'function' && "
        "['mobile', 'desktop'].includes(document.body.dataset.mode)",
        timeout=10000,
    )


def _seed_profile_surfaces(page):
    page.evaluate(
        """profiles => {
            localStorage.clear();
            localStorage.setItem('tc-tb-profiles', JSON.stringify(profiles));
            localStorage.setItem('tc-go-view', 'profile:guest_ready_001');
            localStorage.setItem(
                'tc-mu-profile-ids', JSON.stringify(['guest_ready_001'])
            );
        }""",
        _profile_rows(),
    )
    page.reload(wait_until='domcontentloaded', timeout=15000)
    _wait_for_profile_app(page)


def _assert_no_horizontal_overflow(page, surface_name):
    metrics = page.evaluate(
        """() => ({
            overflow: document.documentElement.scrollWidth
                - document.documentElement.clientWidth,
            offenders: Array.from(document.querySelectorAll('body *'))
                .filter(element => {
                    const style = getComputedStyle(element);
                    if (style.display === 'none' || style.visibility === 'hidden') {
                        return false;
                    }
                    const rect = element.getBoundingClientRect();
                    return rect.right > innerWidth + 0.5;
                })
                .slice(0, 8)
                .map(element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        node: `${element.tagName.toLowerCase()}#${element.id}`
                            + `.${String(element.className).replaceAll(' ', '.')}`,
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                        width: Math.round(rect.width),
                        scrollWidth: element.scrollWidth,
                    };
                }),
            internalOverflow: Array.from(document.querySelectorAll('body *'))
                .filter(element => {
                    const style = getComputedStyle(element);
                    return style.display !== 'none'
                        && style.visibility !== 'hidden'
                        && element.scrollWidth > element.clientWidth + 0.5;
                })
                .sort((a, b) => (b.scrollWidth - b.clientWidth)
                    - (a.scrollWidth - a.clientWidth))
                .slice(0, 8)
                .map(element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        node: `${element.tagName.toLowerCase()}#${element.id}`
                            + `.${String(element.className).replaceAll(' ', '.')}`,
                        clientWidth: element.clientWidth,
                        scrollWidth: element.scrollWidth,
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                    };
                }),
        })"""
    )
    overflow = metrics['overflow']
    assert overflow <= 0, (
        f'{surface_name} has {overflow}px of horizontal overflow at '
        f'{page.viewport_size}; right-edge offenders: {metrics["offenders"]}; '
        f'internal overflow: {metrics["internalOverflow"]}'
    )


def _assert_visible_targets_are_44px(locator, surface_name):
    visible = [locator.nth(index) for index in range(locator.count())
               if locator.nth(index).is_visible()]
    assert visible, f'{surface_name} exposed no visible interaction targets'
    for target in visible:
        box = target.bounding_box()
        assert box is not None
        assert box['width'] >= 44 and box['height'] >= 44, (
            f'{surface_name} target {target.get_attribute("aria-label") or target.inner_text()!r} '
            f'is {box["width"]:.1f}x{box["height"]:.1f}px; expected at least 44x44px'
        )


def _assert_computed_contrast_aa(page, selector, label):
    """Measure WCAG relative luminance from the rendered computed styles."""
    result = page.locator(selector).first.evaluate(
        """element => {
            const parse = value => {
                const colorPattern = new RegExp(
                    'rgba?\\\\(\\\\s*([\\\\d.]+)[, ]+\\\\s*([\\\\d.]+)[, ]+'
                    + '\\\\s*([\\\\d.]+)(?:\\\\s*[,/]\\\\s*([\\\\d.]+))?\\\\s*\\\\)'
                );
                const match = value.match(colorPattern);
                if (!match) throw new Error(`Unsupported computed color: ${value}`);
                return [Number(match[1]), Number(match[2]), Number(match[3]),
                    match[4] === undefined ? 1 : Number(match[4])];
            };
            const luminance = channels => {
                const linear = channels.slice(0, 3).map(channel => {
                    const value = channel / 255;
                    return value <= 0.04045
                        ? value / 12.92
                        : ((value + 0.055) / 1.055) ** 2.4;
                });
                return 0.2126 * linear[0] + 0.7152 * linear[1]
                    + 0.0722 * linear[2];
            };
            const style = getComputedStyle(element);
            const foreground = parse(style.color);
            let backgroundNode = element;
            let background = [255, 255, 255, 1];
            while (backgroundNode) {
                const candidate = parse(getComputedStyle(backgroundNode).backgroundColor);
                if (candidate[3] > 0) {
                    background = candidate;
                    break;
                }
                backgroundNode = backgroundNode.parentElement;
            }
            if (background[3] < 1) {
                background = background.slice(0, 3).map(
                    value => value * background[3] + 255 * (1 - background[3])
                ).concat(1);
            }
            const lighter = Math.max(luminance(foreground), luminance(background));
            const darker = Math.min(luminance(foreground), luminance(background));
            const ratio = (lighter + 0.05) / (darker + 0.05);
            const fontSize = Number.parseFloat(style.fontSize);
            const fontWeight = Number.parseInt(style.fontWeight, 10) || 400;
            const large = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
            return {
                ratio,
                required: large ? 3 : 4.5,
                foreground: style.color,
                background: getComputedStyle(backgroundNode || document.body).backgroundColor,
                fontSize,
                fontWeight,
            };
        }"""
    )
    assert result['ratio'] >= result['required'], (
        f'{label} contrast is {result["ratio"]:.2f}:1 '
        f'({result["foreground"]} on {result["background"]}); '
        f'expected {result["required"]:.1f}:1 for '
        f'{result["fontSize"]}px/{result["fontWeight"]} text'
    )


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


@pytest.mark.parametrize(
    ('width', 'height', 'expected_mode'),
    PROFILE_VIEWPORTS,
)
def test_guest_profiles_and_consumers_are_responsive_safe_and_ordered(
    docs_server, browser, width, height, expected_mode,
):
    """Exercise the built profile UI and both consumers at product breakpoints.

    Hidden tool panels stay mounted in this app, so each query is anchored to
    the panel that has just been made visible. This catches layout, ordering,
    readiness, target-size and text-injection regressions in the bytes that
    would actually be deployed.
    """
    page = browser.new_page(viewport={'width': width, 'height': height})
    captured = _capture_console(page)
    page.add_init_script('window.__hostileExecuted = false')
    _keep_profile_smoke_offline(page)
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        _seed_profile_surfaces(page)

        assert page.locator('body').get_attribute('data-mode') == expected_mode
        if expected_mode == 'mobile':
            assert page.locator('#m-topbar').is_visible()
            mobile_nav = page.locator('#m-nav-btn')
            assert mobile_nav.is_visible()
            _assert_visible_targets_are_44px(mobile_nav, 'mobile navigation')
        else:
            assert page.locator('#sidebar').is_visible()
            assert not page.locator('#m-nav-btn').is_visible()

        tool_labels = page.locator(
            '#sidebar-tools-label + .sidebar-nav .sidebar-label'
        ).all_inner_texts()
        assert tool_labels == [
            'Panchangam', 'Daily Horoscope', 'Muhurtam', 'Profiles', 'Festivals',
        ]

        # Profiles destination: stable order, explicit readiness and inert text.
        page.evaluate("window.switchTool('profiles')")
        profiles_panel = page.locator('#card-profiles')
        assert profiles_panel.is_visible()
        assert page.locator('body').get_attribute('data-tool') == 'profiles'
        assert profiles_panel.locator('.profiles-roster__name').all_inner_texts() == [
            HOSTILE_PROFILE_NAME, LONG_PROFILE_NAME,
        ]
        ready = profiles_panel.locator(
            f'[data-profile-id="{READY_PROFILE_ID}"]'
        )
        incomplete = profiles_panel.locator(
            f'[data-profile-id="{INCOMPLETE_PROFILE_ID}"]'
        )
        ready_text = ready.inner_text()
        incomplete_text = incomplete.inner_text()
        assert 'Muhurtam\nReady' in ready_text
        assert 'Daily Horoscope\nReady · Vrishabha Janma Rashi' in ready_text
        assert 'Muhurtam\nNeeds Nakshatra' in incomplete_text
        assert 'Daily Horoscope\nNeeds Nakshatra' in incomplete_text
        assert profiles_panel.locator('img').count() == 0
        _assert_visible_targets_are_44px(
            profiles_panel.locator('button'), 'Profiles',
        )
        for selector, label in (
            ('.profiles-privacy', 'profile body text'),
            ('.profiles-roster__details', 'muted profile detail'),
            ('.profiles-button--primary', 'profile primary action'),
            (
                '.profiles-readiness__value--needs-details',
                'profile readiness warning',
            ),
        ):
            _assert_computed_contrast_aa(
                page, f'#card-profiles {selector}', label,
            )
        profiles_panel.get_by_role(
            'button', name='Create another profile', exact=True,
        ).click()
        profiles_panel.locator('button[type="submit"]').click()
        assert profiles_panel.locator('#profile-name-error').is_visible()
        _assert_computed_contrast_aa(
            page, '#card-profiles #profile-name-error', 'profile form error',
        )
        profiles_panel.get_by_role('button', name='Cancel', exact=True).click()
        _assert_no_horizontal_overflow(page, 'Profiles')

        # Daily Horoscope: label and option groups retain source order; an
        # incomplete profile stays visible but cannot be selected.
        page.evaluate("window.switchTool('gochara')")
        gochara_panel = page.locator('#panel-gochara')
        assert gochara_panel.is_visible()
        assert gochara_panel.locator('label[for="go-view"]').text_content() == (
            'Horoscope for'
        )
        go_select = gochara_panel.locator('#go-view')
        assert go_select.is_visible()
        assert go_select.input_value() == f'profile:{READY_PROFILE_ID}'
        assert go_select.locator('optgroup').evaluate_all(
            'groups => groups.map(group => group.label)'
        ) == ['Saved profiles', 'Any Rashi']
        saved_options = go_select.locator('optgroup[label="Saved profiles"] option')
        assert saved_options.all_inner_texts() == [
            f'{HOSTILE_PROFILE_NAME} · Vrishabha Rashi + Kanya Lagna',
            f'{LONG_PROFILE_NAME} · Needs Nakshatra',
        ]
        assert not saved_options.nth(0).is_disabled()
        assert saved_options.nth(1).is_disabled()
        assert HOSTILE_PROFILE_NAME in gochara_panel.locator(
            '#go-profile-state'
        ).inner_text()
        assert gochara_panel.locator('#go-profile-state img').count() == 0
        _assert_visible_targets_are_44px(go_select, 'Daily Horoscope selector')
        _assert_visible_targets_are_44px(
            gochara_panel.locator('#go-profile-state button'),
            'Daily Horoscope profile actions',
        )
        _assert_no_horizontal_overflow(page, 'Daily Horoscope')

        # Muhurtam: the ready choice remains selected while incomplete data is
        # legible and disabled. The effective checkbox target is its 44px label.
        page.evaluate("window.switchTool('tarabalam')")
        muhurta_panel = page.locator('#panel-tarabalam')
        assert muhurta_panel.is_visible()
        assert muhurta_panel.locator('.tb-section-label').all_text_contents()[-1] == (
            'Who is this for?'
        )
        muhurta_root = muhurta_panel.locator('#tb-profiles')
        assert muhurta_root.locator('.muhurta-profile-option__name').all_inner_texts() == [
            HOSTILE_PROFILE_NAME, LONG_PROFILE_NAME,
        ]
        mu_ready = muhurta_root.locator(
            f'[data-profile-id="{READY_PROFILE_ID}"]'
        )
        mu_incomplete = muhurta_root.locator(
            f'[data-profile-id="{INCOMPLETE_PROFILE_ID}"]'
        )
        assert mu_ready.locator('input[data-profile-selection]').is_checked()
        assert not mu_ready.locator('input[data-profile-selection]').is_disabled()
        assert mu_incomplete.locator('input[data-profile-selection]').is_disabled()
        assert 'Needs Nakshatra before Muhurtam' in mu_incomplete.inner_text()
        assert muhurta_root.locator('img').count() == 0
        _assert_visible_targets_are_44px(
            muhurta_root.locator('button'), 'Muhurtam profile actions',
        )
        _assert_visible_targets_are_44px(
            muhurta_root.locator(
                '.muhurta-profile-option__label:has(input:not([disabled]))'
            ),
            'Muhurtam profile choices',
        )
        _assert_no_horizontal_overflow(page, 'Muhurtam')

        # The shared contextual form lists existing profiles before creating a
        # duplicate. Its legal maximum-length names must wrap at every width.
        create_from_muhurta = muhurta_root.locator(
            '[data-action="create-profile"]'
        )
        create_from_muhurta.click()
        contextual_profiles = page.locator('#card-profiles')
        assert contextual_profiles.is_visible()
        assert LONG_PROFILE_NAME in contextual_profiles.locator(
            '.profiles-form__existing'
        ).inner_text()
        _assert_no_horizontal_overflow(page, 'Contextual profile form')
        contextual_profiles.get_by_role(
            'button', name='Cancel', exact=True,
        ).click()
        assert muhurta_panel.is_visible()
        assert page.evaluate(
            "document.activeElement?.dataset.action === 'create-profile'"
        )

        assert page.evaluate('window.__hostileExecuted') is False
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, (
        f'profile surfaces raised page errors at {width}x{height}: '
        f'{app_errors[:3]}'
    )


def test_guest_profile_keyboard_order_and_native_confirmation(
    docs_server, browser,
):
    """Prove the real built form and destructive confirmation are keyboard-safe."""
    page = browser.new_page(viewport={'width': 1024, 'height': 768})
    captured = _capture_console(page)
    _keep_profile_smoke_offline(page)
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        _seed_profile_surfaces(page)

        # Enter through a contextual journey action, not a test-only shortcut.
        page.evaluate("window.switchTool('gochara')")
        gochara_panel = page.locator('#panel-gochara')
        gochara_panel.locator(
            f'[data-go-profile-action="edit"]'
            f'[data-go-profile-id="{READY_PROFILE_ID}"]'
        ).click()
        profiles_panel = page.locator('#card-profiles')
        assert profiles_panel.is_visible()
        assert page.evaluate('document.activeElement.id') == 'profile-name'

        form = profiles_panel.locator('form.profiles-form')
        assert form.locator('.profiles-field__label').all_text_contents() == [
            'Name', 'Nakshatra', 'Padam', 'Lagna',
        ]
        for current_id, next_id in (
            ('profile-name', 'profile-nakshatra'),
            ('profile-nakshatra', 'profile-pada'),
            ('profile-pada', 'profile-lagna'),
        ):
            assert page.evaluate('document.activeElement.id') == current_id
            page.keyboard.press('Tab')
            assert page.evaluate('document.activeElement.id') == next_id

        # Leave the form, then verify native Escape/cancel restores the exact
        # delete trigger before a second dialog confirmation performs deletion.
        form.get_by_role('button', name='Cancel', exact=True).click()
        assert page.evaluate(
            "document.activeElement?.dataset.goProfileFocus "
            "=== 'edit:guest_ready_001'"
        )

        # A direct edit returns focus to the replacement control in the
        # re-rendered Profiles roster, not to the removed form or document body.
        page.evaluate("window.switchTool('profiles')")
        profiles_panel = page.locator('#card-profiles')
        direct_edit = profiles_panel.locator(
            f'[data-profile-id="{READY_PROFILE_ID}"] '
            '[data-action="edit-profile"]'
        )
        direct_edit.click()
        assert page.evaluate('document.activeElement.id') == 'profile-name'
        profiles_panel.get_by_role('button', name='Cancel', exact=True).click()
        assert page.evaluate(
            "document.activeElement?.dataset.action === 'edit-profile' && "
            "document.activeElement?.closest('[data-profile-id]')?.dataset.profileId "
            "=== 'guest_ready_001'"
        )

        incomplete_row = profiles_panel.locator(
            f'[data-profile-id="{INCOMPLETE_PROFILE_ID}"]'
        )
        delete_trigger = incomplete_row.locator('[data-action="delete-profile"]')
        delete_trigger.click()
        dialog = page.locator('dialog.profiles-dialog')
        assert dialog.is_visible()
        page.keyboard.press('Escape')
        assert dialog.count() == 0
        assert page.evaluate(
            "document.activeElement?.dataset.action === 'delete-profile' && "
            "document.activeElement?.closest('[data-profile-id]')?.dataset.profileId "
            "=== 'guest_needs_001'"
        )

        incomplete_row.locator('[data-action="delete-profile"]').click()
        page.locator('dialog.profiles-dialog').get_by_role(
            'button', name='Delete profile', exact=True,
        ).click()
        assert profiles_panel.locator(
            f'[data-profile-id="{INCOMPLETE_PROFILE_ID}"]'
        ).count() == 0
        assert profiles_panel.locator('[data-profile-id]').count() == 1
        assert len(page.evaluate(
            "JSON.parse(localStorage.getItem('tc-tb-profiles') || '[]')"
        )) == 1
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'profile keyboard flow raised page errors: {app_errors[:3]}'


def test_guest_profile_storage_events_refresh_consumers_without_losing_a_draft(
    docs_server, browser,
):
    """Two tabs reconcile profile writes without overwriting an open editor."""
    context = browser.new_context(viewport={'width': 1024, 'height': 768})
    _keep_profile_smoke_offline(context)
    page_a = context.new_page()
    page_b = context.new_page()
    captured_a = _capture_console(page_a)
    captured_b = _capture_console(page_b)
    try:
        page_a.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page_a)
        page_a.evaluate('localStorage.clear()')
        page_a.reload(wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page_a)

        page_b.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page_b)

        # Tab A starts a local draft and owns focus in the editor.
        page_a.evaluate("window.switchTool('profiles')")
        panel_a = page_a.locator('#card-profiles')
        panel_a.get_by_role('button', name='Create profile', exact=True).click()
        page_a.fill('#profile-name', 'Unsaved local draft')
        assert page_a.evaluate('document.activeElement.id') == 'profile-name'

        # Tab B saves a complete profile through the public UI. The native
        # storage event refreshes Tab A's store and both mounted consumers.
        page_b.evaluate("window.switchTool('profiles')")
        panel_b = page_b.locator('#card-profiles')
        panel_b.get_by_role('button', name='Create profile', exact=True).click()
        page_b.fill('#profile-name', 'External Ready')
        page_b.select_option('#profile-nakshatra', 'Rohini')
        panel_b.locator('button[type="submit"]').click()
        external_row = panel_b.locator('[data-profile-id]').filter(
            has_text='External Ready'
        )
        external_id = external_row.get_attribute('data-profile-id')
        assert external_id

        page_a.wait_for_function(
            "profileId => Boolean(document.querySelector("
            "`#go-view option[value=\"profile:${profileId}\"]`)) && "
            "Boolean(document.querySelector("
            "`#tb-profiles [data-profile-id=\"${profileId}\"]`))",
            arg=external_id,
            timeout=10000,
        )
        assert page_a.input_value('#profile-name') == 'Unsaved local draft'
        assert page_a.evaluate('document.activeElement.id') == 'profile-name'

        # Inspect each consumer only after making its panel visible.
        page_a.evaluate("window.switchTool('gochara')")
        gochara_a = page_a.locator('#panel-gochara')
        assert gochara_a.is_visible()
        assert gochara_a.locator(
            f'#go-view option[value="profile:{external_id}"]'
        ).count() == 1

        page_a.evaluate("window.switchTool('tarabalam')")
        muhurta_a = page_a.locator('#panel-tarabalam')
        assert muhurta_a.is_visible()
        assert muhurta_a.locator(
            f'#tb-profiles [data-profile-id="{external_id}"]'
        ).is_visible()

        # Returning to the still-open editor keeps the draft; Cancel then
        # reconciles to the externally saved profile list.
        page_a.evaluate("window.switchTool('profiles')")
        assert page_a.input_value('#profile-name') == 'Unsaved local draft'
        panel_a.get_by_role('button', name='Cancel', exact=True).click()
        assert panel_a.locator(
            f'[data-profile-id="{external_id}"]'
        ).is_visible()
        assert 'External Ready' in panel_a.inner_text()

        # Clear from Tab B and require the destination plus both consumers in
        # Tab A to converge through the same storage-event path.
        panel_b.get_by_role(
            'button', name='Clear all profiles', exact=True,
        ).click()
        page_b.locator('dialog').get_by_role(
            'button', name='Clear all profiles', exact=True,
        ).click()
        assert panel_b.locator('.profiles-empty').is_visible()

        page_a.wait_for_selector(
            '#card-profiles .profiles-empty', state='visible', timeout=10000,
        )
        page_a.evaluate("window.switchTool('gochara')")
        gochara_a = page_a.locator('#panel-gochara')
        assert gochara_a.locator(
            f'#go-view option[value="profile:{external_id}"]'
        ).count() == 0
        page_a.evaluate("window.switchTool('tarabalam')")
        muhurta_a = page_a.locator('#panel-tarabalam')
        assert muhurta_a.locator('#tb-profiles [data-profile-id]').count() == 0
        assert muhurta_a.locator('.muhurta-profile-empty').is_visible()
    finally:
        context.close()

    app_errors = [
        msg for kind, msg in [*captured_a, *captured_b]
        if kind == 'pageerror'
    ]
    assert not app_errors, f'two-tab profile flow raised page errors: {app_errors[:3]}'


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
