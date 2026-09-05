"""The static browser selector must match the generated activity contract."""
from html.parser import HTMLParser
from pathlib import Path

from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES

ROOT = Path(__file__).parents[1]


class _ActivityOptions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_selector = False
        self.values = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'select' and attrs.get('id') == 'mu-activity':
            self.in_selector = True
        elif self.in_selector and tag == 'option':
            self.values.append(attrs.get('value'))

    def handle_endtag(self, tag):
        if tag == 'select' and self.in_selector:
            self.in_selector = False


def test_html_activity_selector_matches_browser_catalogue():
    parser = _ActivityOptions()
    parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
    assert tuple(parser.values) == BROWSER_ACTIVITIES

