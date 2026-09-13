"""Browser smoke karnavedha cases; no automatic test collection."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from tests.browser_smoke.accessibility import _assert_no_horizontal_overflow
from tests.browser_smoke.calendar_fixtures import (
    _karnavedha_boundary_lagna_fixture,
    _karnavedha_bounded_lagna_fixture,
)
from tests.browser_smoke.muhurta_support import _run_muhurta_browser_search
from tests.browser_smoke.profile_support import _capture_console


@pytest.mark.parametrize(
    ('scenario', 'failed', 'unknown'),
    (
        ('karnavedha-pass', 0, 0),
        ('karnavedha-chart-fail', 0, 0),
        ('karnavedha-chart-unknown', 0, 0),
        ('karnavedha-tithi-fail', 1, 0),
        ('karnavedha-nakshatra-fail', 1, 0),
        ('karnavedha-both-fail', 2, 0),
        ('karnavedha-unknown', 0, 1),
    ),
)
@pytest.mark.parametrize(
    ('width', 'height'),
    ((390, 844), (1440, 900)),
)
def test_karnavedha_daylight_and_chart_browser_matrix(
    docs_server, browser, scenario, failed, unknown, width, height,
):
    """Exercise every daylight disposition and the surviving chart pass."""
    page = browser.new_page(viewport={'width': width, 'height': height})
    captured = _capture_console(page)
    try:
        calls = _run_muhurta_browser_search(
            page, docs_server, scenario, activity='karnavedha', system='drik',
            lagna_fixture=(
                _karnavedha_boundary_lagna_fixture()
                if scenario == 'karnavedha-chart-unknown'
                else None
            ),
        )
        result = page.locator('#mu-result')
        if scenario == 'karnavedha-pass':
            assert result.locator('.mu-chart-status--screened').is_visible()
            assert 'Karnavedha event checks resolved' in result.inner_text()
            assert (
                'daylight Tithi, daylight Nakshatra and vacant-8th outcomes '
                'all resolved'
            ) in result.inner_text()
            assert result.locator('.mu-slot').count() > 0
            assert result.locator('.mu-tier-excellent').count() > 0
            result.locator('.mu-reason-details').first.locator(
                ':scope > summary').click()
            daylight = result.locator('.mu-rg-daylight').first
            assert daylight.is_visible()
            assert daylight.locator('.mu-chart-rule--pass').count() == 2
            assert '[local sunrise, local sunset)' in daylight.inner_text()
            assert result.locator('.mu-rg-validation').count() == 0
            assert calls
        elif scenario == 'karnavedha-chart-fail':
            assert result.locator('.mu-chart-status--screened').is_visible()
            assert result.locator('.mu-slot').count() == 0
            assert result.locator('.mu-chart-removals').is_visible()
            result.locator('.mu-chart-removals > summary').click()
            assert '8th house is vacant' in result.locator(
                '.mu-chart-removals').inner_text()
            assert 'failed an exact chart requirement' in result.inner_text()
            assert calls
        elif scenario == 'karnavedha-chart-unknown':
            assert result.locator(
                '.mu-chart-status--screened-review').is_visible()
            assert result.locator('.mu-slot').count() > 0
            result.locator('.mu-reason-details').first.locator(
                ':scope > summary').click()
            assert result.locator('.mu-chart-rule--unknown').count() > 0
            assert result.locator('.mu-chart-disposition--review').count() > 0
            assert result.locator('.mu-rg-validation').count() == 0
            assert calls
        else:
            assert result.locator('.mu-chart-status--not-run').is_visible()
            assert result.locator('.mu-slot').count() == 0
            assert calls == []
            dropped = result.locator('.mu-dropped')
            dropped.locator(':scope > summary').click()
            outcomes = dropped.locator('.mu-dropped-daylight')
            assert outcomes.is_visible()
            assert outcomes.locator('.mu-dropped-daylight--fail').count() == failed
            assert outcomes.locator('.mu-dropped-daylight--unknown').count() == unknown
            assert outcomes.locator('.mu-dropped-daylight--pass').count() == (
                2 - failed - unknown)
            if scenario == 'karnavedha-tithi-fail':
                diagnostic = 'Tithi changes at 12:00 inside local daylight'
            elif scenario == 'karnavedha-nakshatra-fail':
                diagnostic = 'Nakshatra changes at 12:30 inside local daylight'
            elif scenario == 'karnavedha-both-fail':
                diagnostic = 'Tithi changes at 12:00'
                assert 'Nakshatra changes at 12:30' in dropped.inner_text()
            else:
                diagnostic = 'Tithi boundary could not be verified'
            assert diagnostic in dropped.inner_text()
            announcement = page.locator('#mu-result-announcement').inner_text()
            assert 'Karnavedha day(s) filtered' in announcement
            assert diagnostic in announcement

        _assert_no_horizontal_overflow(
            page, f'{scenario} Karnavedha at {width}px',
        )
    finally:
        page.close()

    page_errors = [
        message for kind, message in captured if kind == 'pageerror'
    ]
    assert not page_errors, (
        f'{scenario} Karnavedha raised page errors at {width}x{height}: '
        f'{page_errors[:3]}'
    )

@pytest.mark.parametrize(('width', 'height'), ((390, 844), (1440, 900)))
def test_karnavedha_bounded_chart_search_is_not_presented_as_resolved(
    docs_server, browser, width, height,
):
    """A safety-budget bound stays amber and survives the share boundary."""
    page = browser.new_page(viewport={'width': width, 'height': height})
    captured = _capture_console(page)
    try:
        calls = _run_muhurta_browser_search(
            page,
            docs_server,
            'karnavedha-bounded',
            activity='karnavedha',
            system='drik',
            lagna_fixture=_karnavedha_bounded_lagna_fixture(),
            to_date='2026-06-25',
        )
        result = page.locator('#mu-result')
        status = result.locator('.mu-chart-status--screened-bounded')
        assert status.is_visible()
        assert 'bounded candidate set' in status.inner_text()
        assert 'safety budget was reached' in status.inner_text()
        assert result.locator('.mu-chart-status--screened-resolved').count() == 0
        assert result.locator('.mu-slot').count() > 0
        assert len(calls) == 5

        page.evaluate(
            """() => {
                window.__muhurtaShareOpen = null;
                window.open = (url, target) => {
                    window.__muhurtaShareOpen = { url, target };
                    return null;
                };
            }"""
        )
        result.locator('button[aria-label="Share on WhatsApp"]').click()
        opened = page.evaluate('window.__muhurtaShareOpen')
        share_text = parse_qs(urlparse(opened['url']).query)['text'][0]
        assert 'reached its safety budget' in share_text
        assert 'lower-ranked candidates were not assessed' in share_text
        assert 'evaluated and resolved under' not in share_text
        _assert_no_horizontal_overflow(
            page, f'bounded Karnavedha at {width}px',
        )
    finally:
        page.close()

    page_errors = [
        message for kind, message in captured if kind == 'pageerror'
    ]
    assert not page_errors, (
        f'bounded Karnavedha raised page errors at {width}x{height}: '
        f'{page_errors[:3]}'
    )
