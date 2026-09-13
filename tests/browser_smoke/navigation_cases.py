"""Browser smoke navigation cases; no automatic test collection."""

from __future__ import annotations

import pytest

from tests.browser_smoke.calendar_fixtures import (
    _current_day_feed_fixture,
    _festival_navigation_feed_fixture,
    _install_direct_route_runtime_assets,
)
from tests.browser_smoke.profile_support import _capture_console


def test_index_loads_without_referenceerror(docs_server, browser):
    """The exact bug class of the v1.8.0 hotfix — a sidecar that
    404s makes every inline script call throw ReferenceError. If
    `muhurta-scorer.js` (or any future sidecar) is missing or its
    exports change, this test fails before deploy."""
    page = browser.new_page()
    captured = _capture_console(page)
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
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
        feed_text = _festival_navigation_feed_fixture()
        page.route(
            '**/feeds/*.ics',
            lambda route: route.fulfill(
                status=200, content_type='text/calendar', body=feed_text,
            ),
        )
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        # Wait until the bundle had time to evaluate.
        for marker in ('switchTool', 'setTimeFmt', 'calcTarabalam',
                       'findMuhurta', 'renderGochara',
                       'shareTodayOnWhatsApp', 'openFestivalDate'):
            kind = page.evaluate(f"typeof window.{marker}")
            assert kind == 'function', (
                f'window.{marker} is {kind!r}, expected "function". '
                f'Check the Object.assign(window, {{...}}) block in '
                f'src/main.ts — inline onclick handlers depend on it.'
            )
        page.evaluate("window.openFestivalDate('2026-08-31')")
        page.wait_for_function(
            """document.querySelector('input.tp-date-input')?.value === '2026-08-31'
            && document.querySelector('#tp-result')?.getAttribute('aria-busy') === 'false'
            && document.querySelector('#tp-result')?.textContent?.includes(
              'Monday, August 31, 2026'
            )"""
        )
        assert 'Monday, August 31, 2026' in page.locator('#tp-result').inner_text()
    finally:
        page.close()

@pytest.mark.parametrize(
    ('width', 'height', 'expected_mode'),
    (
        (390, 844, 'mobile'),
        (768, 1024, 'mobile'),
        (853, 900, 'mobile'),
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
        page.route(
            '**/feeds/*.ics',
            lambda route: route.fulfill(
                status=200,
                content_type='text/calendar',
                body=_current_day_feed_fixture(),
            ),
        )
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
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
        assert page.locator('#m-page-title').evaluate('node => node.tagName') == 'H1'
        assert page.locator('#sidebar-today').get_attribute('aria-current') == 'page'

        if expected_mode == 'mobile':
            title_box = page.locator('#m-page-title-main').bounding_box()
            subtitle_box = page.locator('#m-page-title-sub').bounding_box()
            assert title_box is not None
            assert subtitle_box is not None
            assert subtitle_box['y'] >= title_box['y'] + title_box['height']

        docs_link = page.locator('#sidebar a[href="/docs/"]')
        if expected_mode == 'mobile':
            nav_button = page.locator('#m-nav-btn')
            sidebar = page.locator('#sidebar')
            assert sidebar.get_attribute('aria-hidden') == 'true'
            assert sidebar.evaluate('node => node.inert') is True
            box = nav_button.bounding_box()
            assert box
            assert box['width'] >= 44
            assert box['height'] >= 44
            nav_button.click()
            assert 'm-nav-open' in page.locator('body').get_attribute('class').split()
            assert sidebar.get_attribute('aria-hidden') is None
            assert sidebar.evaluate('node => node.inert') is False
            assert docs_link.is_visible()
            page.keyboard.press('Escape')
            assert 'm-nav-open' not in (page.locator('body').get_attribute('class') or '').split()
            assert sidebar.get_attribute('aria-hidden') == 'true'
            assert sidebar.evaluate('node => node.inert') is True
        else:
            assert docs_link.is_visible()
            assert page.locator('#sidebar').get_attribute('aria-hidden') is None
            assert page.locator('#sidebar').evaluate('node => node.inert') is False

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
    ('route', 'tool', 'visible_surface'),
    (
        ('#gochara', 'gochara', '#panel-gochara'),
        ('#tarabalam', 'tarabalam', '#panel-tarabalam'),
        ('#muhurta', 'tarabalam', '#panel-tarabalam'),
        ('#profiles', 'profiles', '#card-profiles'),
        ('#festivals', 'festivals', '#special-days-card'),
        ('#subscribe', 'subscribe', '#subscribe'),
        ('#useinai', 'useinai', '#card-mcp'),
        ('#about', 'about', '#card-about'),
    ),
)
def test_direct_hash_routes_open_the_expected_surface(
    docs_server, browser, route, tool, visible_surface,
):
    """A bookmarked tool must restore its shell state on a fresh load."""
    page = browser.new_page(viewport={'width': 853, 'height': 900})
    captured = _capture_console(page)
    _install_direct_route_runtime_assets(page)
    try:
        page.goto(f'{docs_server}{route}', wait_until='domcontentloaded', timeout=15000)
        page.wait_for_function(f"document.body.dataset.tool === '{tool}'")
        assert page.locator(visible_surface).is_visible()
        assert page.locator('#m-page-title').evaluate('node => node.tagName') == 'H1'
        sidebar_item = page.locator(f'#sidebar-{tool}')
        if sidebar_item.count():
            assert sidebar_item.get_attribute('aria-current') == 'page'
        assert captured == []
    finally:
        page.close()
