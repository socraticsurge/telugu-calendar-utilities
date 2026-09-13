"""Browser smoke contextual profile cases; no automatic test collection."""

from __future__ import annotations

from tests.browser_smoke.profile_support import _capture_console


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
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        # Pre-populate a Tarabalam profile so the muhurta scorer's
        # lagna code paths (the ones that crashed in v1.8.0) actually
        # run. Without people set, scoring stays on the fast path.
        page.evaluate(
            "localStorage.setItem('tc-tb-profiles', JSON.stringify("
            "[{name:'Smoke',nak:'Krittika',pada:'1',lagna:'Mesha'}]));"
        )
        page.reload(wait_until='domcontentloaded', timeout=15000)
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
        if page.locator('#mu-result .mu-slot').count():
            assert 'ranked by tier, then score' in page.locator(
                '#mu-result .tb-summary'
            ).inner_text()
            assert 'Excellent slots appear before Good ones' in page.locator(
                '#mu-result .mu-ranking-note'
            ).inner_text()
            first_reason = page.locator(
                '#mu-result .mu-slot .mu-reason-details'
            ).first
            assert first_reason.count() == 1
            assert first_reason.evaluate('node => node.open') is False
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

        page.get_by_role(
            'button', name='Enter astrology details manually', exact=True,
        ).click()
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
        page.get_by_role(
            'button', name='Enter astrology details manually', exact=True,
        ).click()
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
