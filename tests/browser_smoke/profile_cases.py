"""Browser smoke profile cases; no automatic test collection."""

from __future__ import annotations

import pytest

from tests.browser_smoke.accessibility import (
    _assert_computed_contrast_aa,
    _assert_no_horizontal_overflow,
    _assert_visible_targets_are_44px,
)
from tests.browser_smoke.profile_support import (
    HOSTILE_PROFILE_NAME,
    INCOMPLETE_PROFILE_ID,
    LONG_PROFILE_NAME,
    PROFILE_VIEWPORTS,
    READY_PROFILE_ID,
    _capture_console,
    _keep_profile_smoke_offline,
    _seed_profile_surfaces,
    _wait_for_profile_app,
)


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

        _assert_profile_navigation(page, expected_mode)

        profiles_panel, ready = _open_profile_roster(page)

        _assert_manual_profile_detail(page, profiles_panel, ready)

        _assert_profile_form_accessibility(page, profiles_panel)

        _assert_daily_profile_choices(page)

        muhurta_panel, muhurta_root = _assert_muhurta_profile_choices(page)

        _assert_contextual_duplicate_prompt(page, muhurta_panel, muhurta_root)

        assert page.evaluate('window.__hostileExecuted') is False
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, (
        f'profile surfaces raised page errors at {width}x{height}: '
        f'{app_errors[:3]}'
    )

def test_profile_detail_onward_actions_carry_the_selected_person(
    docs_server, browser,
):
    """A ready profile should activate both personalized journeys directly."""
    page = browser.new_page(viewport={'width': 1024, 'height': 768})
    captured = _capture_console(page)
    _keep_profile_smoke_offline(page)
    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        _seed_profile_surfaces(page)

        page.evaluate("window.switchTool('profiles')")
        page.locator(
            f'#card-profiles [data-profile-id="{READY_PROFILE_ID}"] '
            '[data-action="view-profile"]'
        ).click()
        page.get_by_role(
            'button', name='View Daily Horoscope', exact=True,
        ).click()
        page.wait_for_function("document.body.dataset.tool === 'gochara'")
        assert page.input_value('#go-view') == f'profile:{READY_PROFILE_ID}'

        page.reload(wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        _seed_profile_surfaces(page)
        page.evaluate("window.switchTool('profiles')")
        page.locator(
            f'#card-profiles [data-profile-id="{READY_PROFILE_ID}"] '
            '[data-action="view-profile"]'
        ).click()
        page.get_by_role('button', name='Find Muhurtam', exact=True).click()
        page.wait_for_function("document.body.dataset.tool === 'tarabalam'")
        assert page.locator(
            f'#tb-profiles input[data-profile-selection]'
            f'[value="{READY_PROFILE_ID}"]'
        ).is_checked()
    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'profile onward actions raised errors: {app_errors[:3]}'


def _assert_profile_navigation(page, expected_mode):
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


def _open_profile_roster(page):
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
    return profiles_panel, ready


def _assert_manual_profile_detail(page, profiles_panel, ready):
    # A manual profile has a real detail destination, but it must not imply
    # that birth data, a natal chart, or calculation provenance exists.
    manual_view = ready.get_by_role(
        'button', name=f'View {HOSTILE_PROFILE_NAME}', exact=True,
    )
    _assert_visible_targets_are_44px(manual_view, 'profile View action')
    manual_view.click()
    assert profiles_panel.get_by_role(
        'heading', name=HOSTILE_PROFILE_NAME, exact=True,
    ).is_visible()
    assert page.evaluate('document.activeElement.id') == 'profiles-title'
    page.keyboard.press('Tab')
    assert page.evaluate(
        "document.activeElement?.textContent?.trim()"
    ) == 'Back to profiles'
    detail_text = profiles_panel.inner_text()
    assert 'Rohini' in detail_text
    assert 'Kanya' in detail_text
    assert 'Muhurtam' in detail_text
    assert 'Daily Horoscope' in detail_text
    assert (
        'Natal chart and calculation details are available only for '
        'profiles calculated from birth details.'
    ) in detail_text
    assert profiles_panel.locator('[role="img"][aria-label*="D1"]').count() == 0
    assert profiles_panel.locator('table').count() == 0
    assert profiles_panel.get_by_role(
        'link', name='How this is calculated and verified', exact=True,
    ).count() == 0
    _assert_visible_targets_are_44px(
        profiles_panel.locator('button'), 'profile detail actions',
    )
    _assert_no_horizontal_overflow(page, 'Manual profile detail')
    profiles_panel.get_by_role(
        'button', name='Back to profiles', exact=True,
    ).click()
    assert page.evaluate(
        "document.activeElement?.dataset.action === 'view-profile' && "
        "document.activeElement?.closest('[data-profile-id]')?.dataset.profileId "
        "=== 'guest_ready_001'"
    )


def _assert_profile_form_accessibility(page, profiles_panel):
    privacy_box = profiles_panel.locator('.profiles-privacy').bounding_box()
    roster_title_box = profiles_panel.locator(
        '.profiles-roster__title'
    ).bounding_box()
    assert privacy_box is not None
    assert roster_title_box is not None
    intro_to_roster_gap = roster_title_box['y'] - (
        privacy_box['y'] + privacy_box['height']
    )
    assert intro_to_roster_gap >= 24
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
    profiles_panel.get_by_role(
        'button', name='Enter astrology details manually', exact=True,
    ).click()
    profiles_panel.locator('button[type="submit"]').click()
    assert profiles_panel.locator('#profile-name-error').is_visible()
    _assert_computed_contrast_aa(
        page, '#card-profiles #profile-name-error', 'profile form error',
    )
    profiles_panel.get_by_role('button', name='Cancel', exact=True).click()
    _assert_no_horizontal_overflow(page, 'Profiles')


def _assert_daily_profile_choices(page):
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


def _assert_muhurta_profile_choices(page):
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
    return muhurta_panel, muhurta_root


def _assert_contextual_duplicate_prompt(page, muhurta_panel, muhurta_root):
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
