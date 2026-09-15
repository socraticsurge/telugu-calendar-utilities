"""Exercise the opt-in pilot through the built application, not isolated helpers."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.test_browser_smoke import browser as browser
from tests.test_browser_smoke import docs_server as docs_server
from tests.test_browser_smoke import vite_build as vite_build

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('width', [390, 1440])
def test_daily_view_uses_structured_facts_without_description_parsing(browser, docs_server, width):
    data = json.loads((ROOT / 'tests/fixtures/calendar-data-contract.json').read_text())
    fixture = next(item for item in data if item['city'] == 'Hyderabad'
                   and item['system'] == 'drik' and '20260718' in item['days'])
    for event in fixture['days'].values():
        event['description'] = 'Description wording is intentionally unavailable.'
    context = browser.new_context(viewport={'width': width, 'height': 900}, timezone_id='Asia/Kolkata')
    page = context.new_page()
    page.clock.set_fixed_time(datetime(2026, 7, 18, 6, tzinfo=timezone.utc))
    errors, ics_requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: ics_requests.append(request.url) if request.url.endswith('.ics') else None)
    page.route('**/feeds/*.days-v1.json', lambda route: route.fulfill(json=fixture))
    page.route('**/feeds/*-lagna.json', lambda route: route.fulfill(json={'days': []}))
    try:
        page.goto(f'{docs_server}/?calendarData=structured#today')
        page.locator('#tp-result .preview-card').wait_for()
        text = page.locator('#tp-result').inner_text()
        assert 'Shukla Panchami' in text
        assert 'Purva Phalguni' in text
        assert 'Parabhava' in text
        assert not ics_requests
        assert not errors
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        output = ROOT / 'release-evidence/screenshots/calculation-boundaries'
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / f'structured-today-{width}.png'), full_page=True)
        page.evaluate("window.switchTool('tarabalam')")
        page.select_option('#mu-activity', 'any')
        page.fill('#tb-from', '2026-07-18')
        page.fill('#tb-to', '2026-07-19')
        page.get_by_role('button', name='Show Slots', exact=True).click()
        page.locator('#mu-result .mu-slot').first.wait_for()
        assert page.locator('#mu-result').get_attribute('aria-busy') == 'false'
        assert not ics_requests
        assert not errors
        page.screenshot(path=str(output / f'structured-muhurta-{width}.png'), full_page=True)
    finally:
        context.close()
