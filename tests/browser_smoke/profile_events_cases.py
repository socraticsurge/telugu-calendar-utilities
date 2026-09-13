"""Browser smoke profile events cases; no automatic test collection."""

from __future__ import annotations

from tests.browser_smoke.profile_support import (
    INCOMPLETE_PROFILE_ID,
    READY_PROFILE_ID,
    _capture_console,
    _keep_profile_smoke_offline,
    _seed_profile_surfaces,
    _wait_for_profile_app,
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
        panel_a.get_by_role(
            'button', name='Enter astrology details manually', exact=True,
        ).click()
        page_a.fill('#profile-name', 'Unsaved local draft')
        assert page_a.evaluate('document.activeElement.id') == 'profile-name'

        # Tab B saves a complete profile through the public UI. The native
        # storage event refreshes Tab A's store and both mounted consumers.
        page_b.evaluate("window.switchTool('profiles')")
        panel_b = page_b.locator('#card-profiles')
        panel_b.get_by_role('button', name='Create profile', exact=True).click()
        panel_b.get_by_role(
            'button', name='Enter astrology details manually', exact=True,
        ).click()
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
