"""Browser smoke muhurta privacy cases; no automatic test collection."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import pytest

from tests.browser_smoke.accessibility import _assert_no_horizontal_overflow
from tests.browser_smoke.calendar_fixtures import _terminal_boundary_lagna_fixture
from tests.browser_smoke.chart_gateway import _install_muhurta_routes
from tests.browser_smoke.constants import MUHURTA_FIXTURE_DATE, PRIVATE_TRAVELLER_ID
from tests.browser_smoke.muhurta_support import (
    _run_muhurta_browser_search,
    _seed_private_muhurta_profiles,
)
from tests.browser_smoke.profile_support import _capture_console, _wait_for_profile_app


def test_gold_screening_accepts_public_terminal_lagna_boundary(
    docs_server, browser,
):
    """The public 2026-09-17 terminal sentinel must not disable screening."""
    page = browser.new_page(viewport={'width': 1024, 'height': 768})
    captured = _capture_console(page)
    try:
        calls = _run_muhurta_browser_search(
            page,
            docs_server,
            'gold-pass',
            activity='gold',
            lagna_fixture=_terminal_boundary_lagna_fixture(),
        )
        result = page.locator('#mu-result')
        assert result.locator('.mu-chart-status--screened').is_visible()
        assert result.locator('.mu-chart-status--unavailable').count() == 0
        assert 'received exact chart screening' in (
            result.locator('.mu-chart-status').inner_text()
        )
        assert calls, 'the exact-chart gateway was not reached'
    finally:
        page.close()

    page_errors = [message for kind, message in captured if kind == 'pageerror']
    assert not page_errors, (
        'terminal-boundary Gold flow raised page errors: '
        f'{page_errors[:3]}'
    )

@pytest.mark.parametrize(
    ('scenario', 'system', 'expected_state', 'expected_copy'),
    (
        (
            'offline', 'drik', 'unavailable',
            'source-specific personal checks could not run without exact chart facts',
        ),
        (
            'unsupported', 'surya-siddhanta', 'unsupported-system',
            'source-specific personal checks were not run for this system',
        ),
    ),
)
def test_role_copy_never_claims_evaluation_when_chart_facts_were_not_used(
    docs_server, browser, scenario, system, expected_state, expected_copy,
):
    page = browser.new_page(viewport={'width': 1024, 'height': 768})
    captured = _capture_console(page)
    try:
        _install_muhurta_routes(page, docs_server, scenario)
        page.goto(
            f'{docs_server}#tarabalam',
            wait_until='domcontentloaded',
            timeout=15000,
        )
        _wait_for_profile_app(page)
        _seed_private_muhurta_profiles(page)
        page.reload(wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        page.locator('#tp-system').evaluate(
            """(select, value) => {
                select.value = value;
                select.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            system,
        )
        page.select_option('#mu-activity', 'travel')
        page.locator('[data-muhurta-role="traveller"]').select_option(
            PRIVATE_TRAVELLER_ID
        )
        page.fill('#tb-from', MUHURTA_FIXTURE_DATE)
        page.fill('#tb-to', MUHURTA_FIXTURE_DATE)
        page.get_by_role('button', name='Show Slots', exact=True).click()
        page.locator(
            f'#mu-result .mu-chart-status--{expected_state}'
        ).wait_for(state='visible', timeout=20000)

        role_copy = page.locator('#mu-result .mu-personal-role').inner_text()
        assert 'evaluated locally' not in role_copy
        assert expected_copy in role_copy
    finally:
        page.close()

    page_errors = [message for kind, message in captured if kind == 'pageerror']
    assert not page_errors, (
        f'{scenario} role-state flow raised page errors: {page_errors[:3]}'
    )

@pytest.mark.parametrize(
    ('width', 'height', 'expected_mode'),
    ((390, 844, 'mobile'), (1440, 900, 'desktop')),
)
def test_chart_aware_muhurta_profile_role_and_share_stay_private(
    docs_server, browser, width, height, expected_mode,
):
    """A chosen source-specific role survives screening but not sharing.

    The fixture includes two names plus a calculated profile's birth details
    and natal chart. Only the stable role ID is kept locally; the gateway sees
    location and instants, and WhatsApp receives no profile or natal evidence.
    """
    page = browser.new_page(viewport={'width': width, 'height': height})
    captured = _capture_console(page)
    try:
        calls = _install_muhurta_routes(page, docs_server, 'profile')
        page.goto(
            f'{docs_server}#tarabalam',
            wait_until='domcontentloaded',
            timeout=15000,
        )
        _wait_for_profile_app(page)
        _seed_private_muhurta_profiles(page)
        page.reload(wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        page.select_option('#mu-activity', 'travel')

        role_select = page.locator('[data-muhurta-role="traveller"]')
        assert role_select.is_visible()
        assert role_select.locator('option').all_inner_texts() == [
            'Other Private Traveller', 'Private Ananya',
        ]
        role_select.select_option(PRIVATE_TRAVELLER_ID)
        assert role_select.input_value() == PRIVATE_TRAVELLER_ID
        assert page.evaluate(
            "JSON.parse(localStorage.getItem('tc-mu-role-selections')).roles.travel"
        ) == PRIVATE_TRAVELLER_ID

        page.fill('#tb-from', MUHURTA_FIXTURE_DATE)
        page.fill('#tb-to', MUHURTA_FIXTURE_DATE)
        page.get_by_role('button', name='Show Slots', exact=True).click()
        page.locator(
            '#mu-result .mu-chart-status--screened'
        ).wait_for(state='visible', timeout=20000)

        result = page.locator('#mu-result')
        assert page.locator('body').get_attribute('data-mode') == expected_mode
        assert 'Private Ananya · evaluated locally' in result.locator(
            '.mu-personal-role'
        ).inner_text()
        assert result.locator('.mu-slot').count() > 0
        assert result.locator('.mu-rg-personal-computed').count() > 0

        # The stateless chart request has no activity, role, profile, birth or
        # natal-chart field. Only public city coordinates and exact instants
        # cross the browser boundary.
        assert calls
        for payload in calls:
            assert set(payload) == {'contract_version', 'location', 'instants'}
            serialized = json.dumps(payload)
            for private_value in (
                'Private Ananya', 'Other Private Traveller', '1990-04-15',
                '14:30', 'Private Birthplace', 'Rohini', 'Vrishabha', 'Kanya',
            ):
                assert private_value not in serialized

        page.evaluate(
            """() => {
                window.__muhurtaShareOpen = null;
                window.open = (url, target) => {
                    window.__muhurtaShareOpen = { url, target };
                    return null;
                };
            }"""
        )
        result.locator(
            'button[aria-label="Share on WhatsApp"]'
        ).click()
        opened = page.evaluate('window.__muhurtaShareOpen')
        assert opened['target'] == '_blank'
        share_text = parse_qs(urlparse(opened['url']).query)['text'][0]
        assert 'profile details are intentionally omitted' in share_text
        for private_value in (
            'Private Ananya', 'Other Private Traveller', '1990-04-15',
            '14:30', 'Private Birthplace', 'Rohini', 'Vrishabha', 'Kanya',
            '4.69', 'DashaFlow 1.1.0-test',
        ):
            assert private_value not in share_text

        result.locator('.mu-reason-details').first.locator(
            ':scope > summary'
        ).click()
        _assert_no_horizontal_overflow(
            page, f'profile-role chart-aware Muhurtam at {width}px',
        )
    finally:
        page.close()

    page_errors = [
        message for kind, message in captured if kind == 'pageerror'
    ]
    reference_errors = [
        message for _, message in captured
        if 'ReferenceError' in message or 'is not defined' in message
    ]
    assert not page_errors, (
        f'profile-role chart-aware Muhurtam raised page errors at '
        f'{width}x{height}: {page_errors[:3]}'
    )
    assert not reference_errors, (
        f'profile-role chart-aware Muhurtam raised reference errors at '
        f'{width}x{height}: {reference_errors[:3]}'
    )
