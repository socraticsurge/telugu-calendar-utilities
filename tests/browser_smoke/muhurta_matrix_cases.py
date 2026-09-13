"""Browser smoke muhurta matrix cases; no automatic test collection."""

from __future__ import annotations

import pytest

from tests.browser_smoke.muhurta_assertions import (
    _assert_muhurta_result_common,
    _assert_muhurta_result_for_scenario,
)
from tests.browser_smoke.muhurta_support import _run_muhurta_browser_search
from tests.browser_smoke.profile_support import _capture_console


@pytest.mark.parametrize(
    ('scenario', 'activity', 'system', 'expected_state'),
    (
        ('positive', 'purchase', 'drik', 'screened'),
        ('gold-pass', 'gold', 'drik', 'screened'),
        ('gold-cap', 'gold', 'drik', 'screened'),
        ('gold-unknown', 'gold', 'drik', 'screened'),
        ('annaprasana-pass', 'annaprasana', 'drik', 'screened'),
        ('annaprasana-preference-miss', 'annaprasana', 'drik', 'screened'),
        ('annaprasana-hard-fail', 'annaprasana', 'drik', 'screened'),
        ('annaprasana-unknown', 'annaprasana', 'drik', 'screened'),
        (
            'annaprasana-unsupported', 'annaprasana',
            'surya-siddhanta', 'unsupported-system',
        ),
        ('annaprasana-offline', 'annaprasana', 'drik', 'unavailable'),
        ('court-pass', 'court', 'drik', 'screened'),
        ('court-preference-miss', 'court', 'drik', 'screened'),
        ('court-hard-fail', 'court', 'drik', 'screened'),
        ('court-unknown', 'court', 'drik', 'screened'),
        (
            'karnavedha-unsupported', 'karnavedha',
            'surya-siddhanta', 'unsupported-system',
        ),
        ('karnavedha-offline', 'karnavedha', 'drik', 'unavailable'),
        ('failure', 'travel', 'drik', 'screened'),
        ('mixed', 'purchase', 'drik', 'screened'),
        ('unsupported', 'purchase', 'surya-siddhanta', 'unsupported-system'),
        ('offline', 'purchase', 'drik', 'unavailable'),
        ('malformed', 'purchase', 'drik', 'unavailable'),
        ('manual-only', 'vehicle', 'drik', 'manual-only'),
        ('not-run', 'wedding', 'drik', 'not-run'),
    ),
)
@pytest.mark.parametrize(
    ('width', 'height', 'expected_mode'),
    ((390, 844, 'mobile'), (1440, 900, 'desktop')),
)
def test_chart_aware_muhurta_built_browser_state_matrix(
    docs_server, browser, scenario, activity, system, expected_state,
    width, height, expected_mode,
):
    """Prove every chart-aware result state in the deployable bundle.

    Feed, Lagna boundaries and gateway responses are intercepted independently,
    so failures identify the UI/API boundary instead of a mutable live service.
    The same state matrix runs at the two layout extremes requested for review.
    """
    page = browser.new_page(viewport={'width': width, 'height': height})
    captured = _capture_console(page)
    try:
        calls = _run_muhurta_browser_search(
            page, docs_server, scenario, activity=activity, system=system,
        )
        result = page.locator('#mu-result')
        status = result.locator(f'.mu-chart-status--{expected_state}')
        assert status.is_visible()
        assert page.locator('body').get_attribute('data-mode') == expected_mode

        _assert_muhurta_result_for_scenario(
            page, result, status, calls, scenario,
        )
        _assert_muhurta_result_common(
            page, result, status, scenario, expected_state, width,
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
        f'{scenario} chart-aware Muhurtam raised page errors at '
        f'{width}x{height}: {page_errors[:3]}'
    )
    assert not reference_errors, (
        f'{scenario} chart-aware Muhurtam raised reference errors at '
        f'{width}x{height}: {reference_errors[:3]}'
    )
