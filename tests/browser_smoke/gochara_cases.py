"""Browser smoke gochara cases; no automatic test collection."""

from __future__ import annotations

import pytest

from tests.browser_smoke.accessibility import _assert_no_horizontal_overflow
from tests.browser_smoke.profile_support import _capture_console


def test_gochara_unavailable_state_spans_the_chart(docs_server, browser):
    """An unavailable feed is one chart-level state, not one chart cell."""
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    captured = _capture_console(page)
    try:
        page.route('**/gochara.json', lambda route: route.abort())
        page.goto(
            f'{docs_server}/#gochara',
            wait_until='domcontentloaded',
            timeout=15000,
        )
        error = page.locator('#go-chart > .preview-error')
        error.wait_for(state='visible')
        chart_box = page.locator('#go-chart').bounding_box()
        error_box = error.bounding_box()
        assert chart_box is not None
        assert error_box is not None
        assert error_box['width'] >= chart_box['width'] * 0.8
        assert page.evaluate(
            'document.documentElement.scrollWidth === '
            'document.documentElement.clientWidth'
        )
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'Gochara empty state surfaced errors: {app_errors[:3]}'

@pytest.mark.parametrize(
    ('route', 'viewports'),
    (
        ('53-birth-profile-calculation', ((390, 844), (768, 1024))),
        (
            '54-muhurtam-election-chart-screening',
            ((390, 844), (768, 1024), (1024, 768)),
        ),
    ),
)
def test_documentation_diagrams_and_tables_do_not_overflow_page(
    docs_server, browser, route, viewports,
):
    """Wide evidence stays locally scrollable without widening the page."""
    page = browser.new_page()
    captured = _capture_console(page)
    try:
        for width, height in viewports:
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(
                f'{docs_server}/docs/reference/{route}.html',
                wait_until='domcontentloaded',
                timeout=15000,
            )
            page.locator('.vp-doc .mermaid svg').first.wait_for(state='visible')
            if width == 768:
                assert page.locator('.VPNavBarHamburger').is_visible()
            _assert_no_horizontal_overflow(
                page, f'Documentation {route} at {width}x{height}',
            )
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'Documentation surfaced errors: {app_errors[:3]}'

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
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
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
        assert 'from lagna' not in ph.lower()
        details = page.locator('#go-phalalu .go-phalalu-details')
        assert details.count() == 1
        assert details.evaluate('node => node.open') is False
        assert details.locator('.go-phalalu-detail-lines p').count() == 8
        legend = page.locator('#go-legend').inner_text()
        assert 'favourable' in legend, 'verdict legend missing for a rasi view'
    finally:
        page.close()
    ref_errors = [m for kind, m in captured
                  if 'ReferenceError' in m or 'is not defined' in m]
    assert not ref_errors, f'rasi view surfaced ReferenceError(s): {ref_errors[:3]}'
