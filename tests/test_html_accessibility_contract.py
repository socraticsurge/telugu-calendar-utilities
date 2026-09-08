"""Accessibility and CSS hygiene contracts for checked-in HTML surfaces."""

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
LAGNA_HORA_SPEC = (
    ROOT / "docs/specs/2026-06-15-lagna-hora-ui-preview.html"
).read_text(encoding="utf-8")
ONE_SHELL_SPEC = (
    ROOT / "docs/specs/2026-07-18-one-shell-prototype.html"
).read_text(encoding="utf-8")


class _HtmlContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.comments: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]],
    ) -> None:
        self.tags.append((tag, dict(attrs)))

    def handle_comment(self, data: str) -> None:
        self.comments.append(data)


def _parse(source: str) -> _HtmlContractParser:
    parser = _HtmlContractParser()
    parser.feed(source)
    return parser


def _tag_with_id(parser: _HtmlContractParser, element_id: str) -> tuple[str, dict]:
    return next(
        (tag, attrs) for tag, attrs in parser.tags if attrs.get("id") == element_id
    )


def _css_rule(source: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]+)\}}", source)
    assert match, f"Missing CSS rule for {selector}"
    return match.group(1)


def _css_property(rule: str, name: str) -> str:
    match = re.search(rf"(?:^|;)\s*{re.escape(name)}\s*:\s*([^;]+)", rule)
    assert match, f"Missing {name} in CSS rule"
    return match.group(1).strip()


def _rgb(css_color: str) -> tuple[float, float, float]:
    if css_color.startswith("#"):
        value = css_color[1:]
        if len(value) == 3:
            value = "".join(channel * 2 for channel in value)
        return tuple(float(int(value[index:index + 2], 16)) for index in (0, 2, 4))
    match = re.fullmatch(
        r"rgba\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)",
        css_color,
    )
    assert match, f"Unsupported CSS color {css_color}"
    red, green, blue, alpha = map(float, match.groups())
    return tuple(channel * alpha + 255 * (1 - alpha) for channel in (red, green, blue))


def _luminance(rgb: tuple[float, float, float]) -> float:
    channels = []
    for channel in rgb:
        value = channel / 255
        channels.append(
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    foreground_luminance = _luminance(_rgb(foreground))
    background_luminance = _luminance(_rgb(background))
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def test_live_html_uses_native_status_list_and_group_semantics():
    parser = _parse(INDEX)

    assert _tag_with_id(parser, "mu-result-announcement")[0] == "output"
    assert _tag_with_id(parser, "copy-confirm")[0] == "output"
    assert '<output class="preview-error">Loading…</output>' in INDEX
    assert all(
        not (tag == "ul" and attrs.get("role") == "list")
        for tag, attrs in parser.tags
    )
    assert _tag_with_id(parser, "sel-fmt-toggle")[0] == "fieldset"
    assert '<legend class="sr-only">Time format</legend>' in INDEX
    assert all("TARABALAM HIDDEN" not in comment for comment in parser.comments)


def test_checked_in_prototype_labels_are_associated_with_controls_or_groups():
    parser = _parse(ONE_SHELL_SPEC)

    assert all(
        attrs.get("for")
        for tag, attrs in parser.tags
        if tag == "label"
    )
    assert any(
        tag == "fieldset" and "people" in (attrs.get("class") or "").split()
        for tag, attrs in parser.tags
    )


def test_repeated_selectors_are_consolidated_without_changing_their_scope():
    for selector in (
        ".tool-tab",
        ".preview-head .date",
        'body[data-mode="mobile"] .upcoming-date',
        'body[data-mode="mobile"] #panel-tarabalam .tb-controls',
    ):
        assert INDEX.count(f"\n    {selector} {{") == 1


def test_flagged_small_text_meets_wcag_aa_contrast():
    surfaces = (
        (INDEX, ".preview-head .badge"),
        (INDEX, 'body[data-mode="mobile"] #go-conditions .chip'),
        (LAGNA_HORA_SPEC, ".palette-site .hora-cell.malefic"),
        (LAGNA_HORA_SPEC, ".palette-site .lagna-seg.unfav"),
    )

    for source, selector in surfaces:
        rule = _css_rule(source, selector)
        foreground = _css_property(rule, "color")
        background = _css_property(rule, "background")
        assert _contrast_ratio(foreground, background) >= 4.5, selector
