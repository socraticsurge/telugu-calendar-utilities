"""Rendered visual-system contracts for the existing responsive shell."""

from tests import test_browser_smoke

browser = test_browser_smoke.browser
docs_server = test_browser_smoke.docs_server
vite_build = test_browser_smoke.vite_build


def test_navigation_uses_decorative_vectors_and_keyboard_focus(docs_server, browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    try:
        page.goto(docs_server, wait_until="domcontentloaded")
        icons = page.locator(".sidebar-icon")
        assert icons.count() == 7
        for icon in icons.all():
            assert icon.locator("..").get_attribute("aria-hidden") == "true"
            assert (
                icon.evaluate("el => getComputedStyle(el, '::before').maskImage")
                != "none"
            )
        page.locator("#sidebar-subscribe").click()
        page.keyboard.press("Tab")
        page.locator("#app-tab-google").focus()
        page.keyboard.press("ArrowRight")
        focus = page.locator("#app-tab-apple").evaluate(
            "el => ({style:getComputedStyle(el).outlineStyle,width:getComputedStyle(el).outlineWidth})"
        )
        assert focus["style"] != "none"
        assert float(focus["width"].replace("px", "")) >= 2
    finally:
        page.close()
