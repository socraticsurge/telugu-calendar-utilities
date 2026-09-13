"""Browser smoke birth profile cases; no automatic test collection."""

from __future__ import annotations

import json

from tests.browser_smoke.accessibility import _assert_no_horizontal_overflow
from tests.browser_smoke.profile_support import (
    _capture_console,
    _keep_profile_smoke_offline,
    _wait_for_profile_app,
)


def test_birth_details_profile_calls_the_stateless_contract_and_reuses_result(
    docs_server, browser,
):
    """Exercise the default birth-details path against a mocked gateway.

    This verifies the deployed browser bundle, CORS-shaped network boundary,
    review chart, local persistence and both existing profile consumers without
    sending synthetic birth data to a live service.
    """
    page = browser.new_page(viewport={'width': 1024, 'height': 900})
    captured = _capture_console(page)
    calls = []
    allowed_origin = docs_server

    _install_birth_gateway(page, allowed_origin, calls)

    try:
        page.goto(docs_server, wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        page.evaluate('localStorage.clear()')
        page.reload(wait_until='domcontentloaded', timeout=15000)
        _wait_for_profile_app(page)
        page.evaluate("window.switchTool('profiles')")

        panel = page.locator('#card-profiles')
        panel.get_by_role('button', name='Create profile', exact=True).click()

        _assert_desktop_birth_form(page, panel)

        _assert_tablet_birth_form(page)

        _assert_mobile_birth_form(page)

        _calculate_birth_profile(page, panel)

        _assert_calculated_form_keyboard_order(page, panel)

        _save_and_reload_calculated_profile(page, panel, calls)

        storage_before_view = _view_persisted_profile_without_requests(page, panel, calls)

        _assert_saved_profile_mobile_and_edit(page, panel, calls, storage_before_view)

        _assert_calculated_profile_consumers(page)

    finally:
        page.close()

    app_errors = [msg for kind, msg in captured if kind == 'pageerror']
    assert not app_errors, f'birth-details profile surfaced errors: {app_errors[:3]}'


def _install_birth_gateway(page, allowed_origin, calls):
    planets = _birth_gateway_planets()

    def fulfill_guest_gateway(route):
        _fulfill_birth_gateway(route, allowed_origin, calls, planets)

    _keep_profile_smoke_offline(page)
    page.route(
        'http://127.0.0.1:3000/api/guest/**',
        fulfill_guest_gateway,
    )


def _birth_gateway_planets():
    return [
        {
            'name': name,
            'rashi': rashi,
            'degree': 15 if name == 'Chandra' else 10 if name in {'Rahu', 'Ketu'} else index + 0.25,
            'house': ((1 if name == 'Ketu' else index) - 4) % 12 + 1,
            'retrograde': name in {'Shani', 'Rahu', 'Ketu'},
        }
        for index, (name, rashi) in enumerate((
            ('Surya', 'Mesha'), ('Chandra', 'Vrishabha'),
            ('Kuja', 'Mithuna'), ('Budha', 'Karka'), ('Guru', 'Simha'),
            ('Shukra', 'Kanya'), ('Shani', 'Tula'),
            ('Rahu', 'Vrischika'), ('Ketu', 'Vrishabha'),
        ))
    ]

def _fulfill_birth_gateway(route, allowed_origin, calls, planets):
    request = route.request
    headers = {
        'Access-Control-Allow-Origin': allowed_origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Cache-Control': 'private, no-store',
    }
    if request.method == 'OPTIONS':
        route.fulfill(status=204, headers=headers, body='')
        return
    payload = request.post_data_json
    calls.append((request.url, payload))
    if request.url.endswith('/places/search'):
        body = {
            'data': {
                'results': [{
                    'id': 'osm:hyderabad',
                    'label': 'Hyderabad, Telangana, India',
                    'latitude': 17.385,
                    'longitude': 78.4867,
                    'timezone': 'Asia/Kolkata',
                }],
                'attribution': 'OpenStreetMap contributors',
                'attributions': [{
                    'label': '© OpenStreetMap contributors',
                    'url': 'https://www.openstreetmap.org/copyright',
                }],
            },
        }
    else:
        body = {
            'contract_version': '1.0',
            'engine': {
                'name': 'DashaFlow',
                'version': '1.1.0',
                'ayanamsha': 'Lahiri',
                'ephemeris': 'moshier',
            },
            'data': {
                'nakshatra': 'Rohini',
                'pada': 2,
                'janma_rashi': 'Vrishabha',
                'lagna': 'Simha',
                'lagna_degree': 4.69,
                'planets': planets,
            },
        }
    route.fulfill(
        status=200,
        headers=headers,
        content_type='application/json',
        body=json.dumps(body),
    )



def _assert_desktop_birth_form(page, panel):
    desktop_layout = page.evaluate("""() => {
            const rect = selector => document.querySelector(selector).getBoundingClientRect();
            const panel = rect('#card-profiles');
            const root = rect('#profiles-root');
            const form = rect('.profiles-form');
            const methods = rect('.profiles-methods');
            const date = rect('#profile-birth-date');
            const time = rect('#profile-birth-time');
            const choices = [...document.querySelectorAll('.profiles-methods__choice')]
                .map(choice => choice.getBoundingClientRect());
            const calculation = document.querySelector('.profiles-calculation');
            const calculationStyle = getComputedStyle(calculation);
            return {
                panelCenter: panel.left + panel.width / 2,
                rootCenter: root.left + root.width / 2,
                formCenter: form.left + form.width / 2,
                methodsCenter: methods.left + methods.width / 2,
                dateTop: date.top,
                dateHeight: date.height,
                timeTop: time.top,
                timeHeight: time.height,
                choiceWidths: choices.map(choice => choice.width),
                calculationBorderTop: parseFloat(calculationStyle.borderTopWidth),
                calculationBorderLeft: parseFloat(calculationStyle.borderLeftWidth),
            };
        }""")
    assert abs(desktop_layout['panelCenter'] - desktop_layout['rootCenter']) <= 1
    assert abs(desktop_layout['rootCenter'] - desktop_layout['formCenter']) <= 1
    assert abs(desktop_layout['formCenter'] - desktop_layout['methodsCenter']) <= 1
    assert abs(desktop_layout['dateTop'] - desktop_layout['timeTop']) <= 1
    assert abs(desktop_layout['dateHeight'] - desktop_layout['timeHeight']) <= 1
    assert abs(
        desktop_layout['choiceWidths'][0] - desktop_layout['choiceWidths'][1]
    ) <= 1
    assert desktop_layout['calculationBorderTop'] == 1
    assert desktop_layout['calculationBorderLeft'] == 1
    assert panel.locator('.profiles-form__actions button').all_inner_texts() == [
        'Cancel', 'Save calculated profile',
    ]


def _assert_tablet_birth_form(page):
    page.set_viewport_size({'width': 768, 'height': 1024})
    page.wait_for_function("document.body.dataset.mode === 'mobile'")
    tablet_layout = page.evaluate("""() => {
            const rect = selector => document.querySelector(selector).getBoundingClientRect();
            const panel = rect('#card-profiles');
            const root = rect('#profiles-root');
            const date = rect('#profile-birth-date');
            const time = rect('#profile-birth-time');
            const place = rect('#profile-birth-place');
            const findPlace = rect('[data-action="search-birth-place"]');
            const choices = [...document.querySelectorAll('.profiles-methods__choice')]
                .map(choice => choice.getBoundingClientRect());
            return {
                panelCenter: panel.left + panel.width / 2,
                rootCenter: root.left + root.width / 2,
                dateTop: date.top,
                timeTop: time.top,
                placeTop: place.top,
                findPlaceTop: findPlace.top,
                choiceTops: choices.map(choice => choice.top),
                overflow: document.documentElement.scrollWidth - window.innerWidth,
            };
        }""")
    assert abs(tablet_layout['panelCenter'] - tablet_layout['rootCenter']) <= 1
    assert abs(tablet_layout['dateTop'] - tablet_layout['timeTop']) <= 1
    assert abs(tablet_layout['placeTop'] - tablet_layout['findPlaceTop']) <= 1
    assert abs(
        tablet_layout['choiceTops'][0] - tablet_layout['choiceTops'][1]
    ) <= 1
    assert tablet_layout['overflow'] <= 0


def _assert_mobile_birth_form(page):
    page.set_viewport_size({'width': 390, 'height': 844})
    mobile_layout = page.evaluate("""() => {
            const dateGroup = document.querySelector('#profile-birth-date')
                .closest('.profiles-field').getBoundingClientRect();
            const timeGroup = document.querySelector('#profile-birth-time')
                .closest('.profiles-field').getBoundingClientRect();
            const choices = [...document.querySelectorAll('.profiles-methods__choice')]
                .map(choice => choice.getBoundingClientRect());
            const actions = [...document.querySelectorAll('.profiles-form__actions button')]
                .map(action => ({
                    text: action.textContent.trim(),
                    top: action.getBoundingClientRect().top,
                }));
            return {
                birthFieldGap: timeGroup.top - dateGroup.bottom,
                choiceTops: choices.map(choice => choice.top),
                actions,
                overflow: document.documentElement.scrollWidth - window.innerWidth,
            };
        }""")
    assert 15 <= mobile_layout['birthFieldGap'] <= 17
    assert mobile_layout['choiceTops'][1] > mobile_layout['choiceTops'][0]
    assert [action['text'] for action in mobile_layout['actions']] == [
        'Cancel', 'Save calculated profile',
    ]
    assert mobile_layout['actions'][0]['top'] < mobile_layout['actions'][1]['top']
    assert mobile_layout['overflow'] <= 0


def _calculate_birth_profile(page, panel):
    page.set_viewport_size({'width': 1024, 'height': 900})
    page.wait_for_function("document.body.dataset.mode === 'desktop'")
    page.fill('#profile-name', 'Browser Ananya')
    page.fill('#profile-birth-date', '1990-04-15')
    page.fill('#profile-birth-time', '14:30')
    page.fill('#profile-birth-place', 'Hyderabad')
    panel.get_by_role('button', name='Find place', exact=True).click()
    place_choice = panel.locator('.profiles-place-results__choice')
    place_choice.wait_for(state='visible')
    assert 'Hyderabad, Telangana, India' in place_choice.inner_text()
    attribution_link = panel.locator('.profiles-place-attribution a')
    assert attribution_link.count() == 1
    assert attribution_link.get_attribute('href') == (
        'https://www.openstreetmap.org/copyright'
    )
    assert attribution_link.get_attribute('rel') == 'noopener noreferrer'
    place_choice.click()
    panel.get_by_role('button', name='Calculate details', exact=True).click()
    panel.locator('.profiles-birth-review').wait_for(state='visible')

    recalculate = panel.get_by_role(
        'button', name='Recalculate details', exact=True,
    )
    assert recalculate.get_attribute('class').find('profiles-button--secondary') >= 0
    assert recalculate.get_attribute('class').find('profiles-button--primary') == -1


def _assert_calculated_form_keyboard_order(page, panel):
    page.set_viewport_size({'width': 390, 'height': 844})
    page.wait_for_function("document.body.dataset.mode === 'mobile'")
    post_calculation_actions = page.evaluate("""() => (
            [...document.querySelectorAll('.profiles-form__actions button')].map(action => ({
                text: action.textContent.trim(),
                top: action.getBoundingClientRect().top,
            }))
        )""")
    assert [action['text'] for action in post_calculation_actions] == [
        'Cancel', 'Save calculated profile',
    ]
    assert post_calculation_actions[0]['top'] < post_calculation_actions[1]['top']
    panel.get_by_role('button', name='Cancel', exact=True).focus()
    page.keyboard.press('Tab')
    assert page.evaluate("document.activeElement.textContent.trim()") == (
        'Save calculated profile'
    )
    page.set_viewport_size({'width': 1024, 'height': 900})
    page.wait_for_function("document.body.dataset.mode === 'desktop'")


def _save_and_reload_calculated_profile(page, panel, calls):
    assert panel.locator('.profiles-birth-facts').inner_text().find('Rohini') >= 0
    assert panel.locator('.profiles-chart__cell').count() == 12
    assert panel.locator('.profiles-chart-table tbody tr').count() == 9
    reference = panel.get_by_role(
        'link', name='How this is calculated and verified', exact=True,
    )
    assert reference.get_attribute('href') == (
        '/docs/reference/53-birth-profile-calculation'
    )
    assert calls[0][1] == {'query': 'Hyderabad'}
    assert calls[1][1] == {
        'date_of_birth': '1990-04-15',
        'time_of_birth': '14:30',
        'latitude': 17.385,
        'longitude': 78.4867,
        'timezone': 'Asia/Kolkata',
    }
    assert 'name' not in calls[1][1]

    panel.get_by_role(
        'button', name='Save calculated profile', exact=True,
    ).click()
    assert 'Calculated from birth details' in panel.inner_text()
    extension = page.evaluate(
        "JSON.parse(localStorage.getItem('tc-birth-profile-data'))"
    )
    saved_extension = next(iter(extension['profiles'].values()))
    assert saved_extension['birthDetails']['placeLabel'] == (
        'Hyderabad, Telangana, India'
    )

    page.reload(wait_until='domcontentloaded', timeout=15000)
    _wait_for_profile_app(page)
    page.evaluate("window.switchTool('profiles')")
    assert panel.locator('[data-profile-id]').filter(
        has_text='Browser Ananya'
    ).is_visible()


def _view_persisted_profile_without_requests(page, panel, calls):
    # Viewing a saved result is a read-only path: it reuses the persisted
    # calculation, renders its evidence, and performs no new gateway call.
    calls_before_view = list(calls)
    url_before_view = page.url
    storage_before_view = page.evaluate("""() => ({
            roster: localStorage.getItem('tc-tb-profiles'),
            birth: localStorage.getItem('tc-birth-profile-data'),
        })""")
    saved_row = panel.locator('[data-profile-id]').filter(
        has_text='Browser Ananya'
    )
    saved_row.get_by_role(
        'button', name='View Browser Ananya', exact=True,
    ).click()

    assert panel.get_by_role(
        'heading', name='Browser Ananya', exact=True,
    ).is_visible()
    saved_detail = panel.inner_text()
    for expected in (
        '1990-04-15', '14:30', 'Hyderabad, Telangana, India',
        'Asia/Kolkata', 'Rohini', 'Vrishabha', 'Simha',
        'DashaFlow 1.1.0', 'Lahiri ayanamsha', 'moshier ephemeris',
        'contract 1.0',
    ):
        assert expected in saved_detail
    assert panel.locator(
        '[role="img"][aria-label*="D1 Rashi chart"]'
    ).count() == 1
    chart_table = panel.get_by_role(
        'table', name='Planet positions in the D1 Rashi chart', exact=True,
    )
    assert chart_table.locator('tbody tr').count() == 9
    reference = panel.get_by_role(
        'link', name='How this is calculated and verified', exact=True,
    )
    assert reference.get_attribute('href') == (
        '/docs/reference/53-birth-profile-calculation'
    )
    assert page.url == url_before_view
    assert calls == calls_before_view
    assert page.evaluate("""() => ({
            roster: localStorage.getItem('tc-tb-profiles'),
            birth: localStorage.getItem('tc-birth-profile-data'),
        })""") == storage_before_view
    _assert_no_horizontal_overflow(page, 'Calculated profile detail')
    return storage_before_view


def _assert_saved_profile_mobile_and_edit(page, panel, calls, storage_before_view):
    page.set_viewport_size({'width': 320, 'height': 800})
    page.wait_for_function("document.body.dataset.mode === 'mobile'")
    assert panel.locator('.profiles-chart-table__hint').is_visible()
    chart_text_size = panel.locator('.profiles-chart__rashi').first.evaluate(
        'element => Number.parseFloat(getComputedStyle(element).fontSize)'
    )
    assert chart_text_size >= 11
    _assert_no_horizontal_overflow(page, '320px calculated profile detail')
    page.set_viewport_size({'width': 1024, 'height': 900})
    page.wait_for_function("document.body.dataset.mode === 'desktop'")

    panel.get_by_role(
        'button', name='Back to profiles', exact=True,
    ).click()
    assert page.evaluate(
        "document.activeElement?.dataset.action === 'view-profile' && "
        "document.activeElement?.closest('[data-profile-id]')?.innerText"
        ".includes('Browser Ananya')"
    )
    panel.get_by_role(
        'button', name='View Browser Ananya', exact=True,
    ).click()
    request_count_before_edit = len(calls)
    panel.get_by_role('button', name='Edit profile', exact=True).click()
    assert page.input_value('#profile-name') == 'Browser Ananya'
    assert page.evaluate('document.activeElement.id') == 'profile-name'
    panel.get_by_role('button', name='Cancel', exact=True).click()
    assert len(calls) == request_count_before_edit
    assert page.evaluate("""() => ({
            roster: localStorage.getItem('tc-tb-profiles'),
            birth: localStorage.getItem('tc-birth-profile-data'),
        })""") == storage_before_view


def _assert_calculated_profile_consumers(page):
    page.evaluate("window.switchTool('gochara')")
    assert 'Browser Ananya' in page.locator('#go-view').inner_text()
    page.evaluate("window.switchTool('tarabalam')")
    result_row = page.locator('#tb-profiles [data-profile-id]').filter(
        has_text='Browser Ananya'
    )
    assert result_row.is_visible()
    assert not result_row.locator('input[data-profile-selection]').is_disabled()
    assert page.evaluate('window.__hostileExecuted') is not True
