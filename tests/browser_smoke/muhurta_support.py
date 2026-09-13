"""Browser smoke muhurta support; no automatic test collection."""

from __future__ import annotations

from tests.browser_smoke.chart_gateway import _install_muhurta_routes
from tests.browser_smoke.constants import (
    MUHURTA_FIXTURE_DATE,
    MUHURTA_PLANET_NAMES,
    MUHURTA_PLANET_RASHIS,
    OTHER_TRAVELLER_ID,
    PRIVATE_TRAVELLER_ID,
)
from tests.browser_smoke.profile_support import _wait_for_profile_app


def _seed_private_muhurta_profiles(page):
    rows = [
        {
            'id': OTHER_TRAVELLER_ID,
            'schemaVersion': 1,
            'name': 'Other Private Traveller',
            'nak': 'Ashvini',
            'pada': 2,
            'lagna': 'Mesha',
        },
        {
            'id': PRIVATE_TRAVELLER_ID,
            'schemaVersion': 1,
            'name': 'Private Ananya',
            'nak': 'Rohini',
            'pada': 2,
            'lagna': 'Kanya',
        },
    ]
    natal_planets = [
        {
            'name': name,
            'rashi': 'Vrishabha' if name == 'Ketu' else MUHURTA_PLANET_RASHIS[index],
            'degree': 15 if name == 'Chandra' else 10 if name in {'Rahu', 'Ketu'} else index + 0.5,
            'house': ((1 if name == 'Ketu' else index) - 5) % 12 + 1,
            'retrograde': name in {'Shani', 'Rahu', 'Ketu'},
        }
        for index, name in enumerate(MUHURTA_PLANET_NAMES)
    ]
    extension = {
        'schemaVersion': 1,
        'profiles': {
            PRIVATE_TRAVELLER_ID: {
                'source': 'birth-details',
                'nakshatra': 'Rohini',
                'pada': 2,
                'lagna': 'Kanya',
                'janmaRasi': 'Vrishabha',
                'birthDetails': {
                    'dateOfBirth': '1990-04-15',
                    'timeOfBirth': '14:30',
                    'placeLabel': 'Private Birthplace, India',
                    'latitude': 17.385,
                    'longitude': 78.4867,
                    'timezone': 'Asia/Kolkata',
                },
                'natalChart': {
                    'lagnaDegree': 4.69,
                    'planets': natal_planets,
                },
                'calculation': {
                    'contractVersion': '1.0',
                    'engine': {
                        'name': 'DashaFlow',
                        'version': '1.1.0-test',
                        'ayanamsha': 'Lahiri',
                        'ephemeris': 'swiss',
                    },
                },
            },
        },
    }
    page.evaluate(
        """state => {
            localStorage.clear();
            localStorage.setItem('tc-tb-profiles', JSON.stringify(state.rows));
            localStorage.setItem(
                'tc-mu-profile-ids', JSON.stringify(state.selectedIds)
            );
            localStorage.setItem(
                'tc-birth-profile-data', JSON.stringify(state.extension)
            );
        }""",
        {
            'rows': rows,
            'selectedIds': [OTHER_TRAVELLER_ID, PRIVATE_TRAVELLER_ID],
            'extension': extension,
        },
    )

def _run_muhurta_browser_search(
    page, docs_server, scenario, activity='purchase', system='drik',
    lagna_fixture=None, to_date=MUHURTA_FIXTURE_DATE,
):
    calls = _install_muhurta_routes(
        page, docs_server, scenario, lagna_fixture=lagna_fixture,
    )
    page.goto(
        f'{docs_server}#tarabalam',
        wait_until='domcontentloaded',
        timeout=15000,
    )
    _wait_for_profile_app(page)
    # The settings form is intentionally collapsed in the product shell. Set
    # the real select and dispatch its public change event without forcing the
    # hidden control visible solely for a test.
    page.locator('#tp-system').evaluate(
        """(select, value) => {
            select.value = value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        system,
    )
    if activity == 'vidyarambha':
        option = page.locator('#mu-activity option[value="vidyarambha"]')
        assert option.text_content().strip() == (
            'Aksharabhyasa (First-letter writing)'
        )
    page.select_option('#mu-activity', activity)
    page.fill('#tb-from', MUHURTA_FIXTURE_DATE)
    page.fill('#tb-to', to_date)
    page.get_by_role('button', name='Show Slots', exact=True).click()
    page.locator('#mu-result .mu-chart-status').wait_for(
        state='visible', timeout=20000,
    )
    assert page.locator('#mu-result').get_attribute('aria-busy') == 'false'
    return calls
