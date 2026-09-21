"""Keep the daily answer visible while detailed timing remains keyboard accessible."""

from datetime import datetime, timedelta, timezone

import pytest

from tests import test_browser_smoke
from tests.browser_smoke.calendar_fixtures import _current_day_feed_fixture

expect = test_browser_smoke.playwright_sync.expect
browser = test_browser_smoke.browser
docs_server = test_browser_smoke.docs_server
vite_build = test_browser_smoke.vite_build


@pytest.mark.parametrize("width", [390, 768, 1440])
def test_daily_glance_preserves_data_and_keyboard_disclosure(
    docs_server, browser, width
):
    page = browser.new_page(viewport={"width": width, "height": 900})
    page.route(
        "**/feeds/*.ics",
        lambda route: route.fulfill(
            content_type="text/calendar", body=_current_day_feed_fixture()
        ),
    )
    page.route("**/feeds/*-lagna.json", lambda route: route.fulfill(json={"days": []}))
    try:
        page.goto(docs_server)
        page.locator(".day-cycle").wait_for()
        assert page.locator(".day-cycle-time").count() == 4
        date_target = page.locator(".tp-date-input").bounding_box()
        assert date_target["height"] >= 44
        assert date_target["width"] >= 44
        assert page.locator(".day-cycle").bounding_box()["height"] <= 140
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        details = page.locator(".daily-details")
        assert details.get_attribute("open") is None
        primary = page.locator(".anga-grid").inner_text()
        assert "tithi" in primary.lower()
        assert "nakshatra" in primary.lower()
        summary = details.locator("summary")
        summary.focus()
        page.keyboard.press("Enter")
        expect(details).to_have_attribute("open", "")
        expect(details.locator(".daily-details-body")).to_be_visible()
        assert page.locator(".anga-grid").inner_text() == primary
        summary.focus()
        page.keyboard.press("Space")
        assert details.get_attribute("open") is None
        tomorrow = (datetime.now(timezone.utc).astimezone().date() + timedelta(days=1)).isoformat()
        page.locator(".tp-date-input").fill(tomorrow)
        page.locator(".tp-date-input").dispatch_event("change")
        expect(page.locator("#tp-result")).to_have_attribute("aria-busy", "false")
        expect(page.locator(".tp-date-input")).to_have_value(tomorrow)
        assert page.locator(".day-cycle-time").count() == 4
        assert page.locator(".daily-details").get_attribute("open") is None
    finally:
        page.close()
