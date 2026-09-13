"""Browser smoke accessibility; no automatic test collection."""

from __future__ import annotations


def _assert_no_horizontal_overflow(page, surface_name):
    metrics = page.evaluate(
        """() => ({
            overflow: document.documentElement.scrollWidth
                - document.documentElement.clientWidth,
            offenders: Array.from(document.querySelectorAll('body *'))
                .filter(element => {
                    const style = getComputedStyle(element);
                    if (style.display === 'none' || style.visibility === 'hidden') {
                        return false;
                    }
                    const rect = element.getBoundingClientRect();
                    return rect.right > innerWidth + 0.5;
                })
                .slice(0, 8)
                .map(element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        node: `${element.tagName.toLowerCase()}#${element.id}`
                            + `.${String(element.className).replaceAll(' ', '.')}`,
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                        width: Math.round(rect.width),
                        scrollWidth: element.scrollWidth,
                    };
                }),
            internalOverflow: Array.from(document.querySelectorAll('body *'))
                .filter(element => {
                    const style = getComputedStyle(element);
                    return style.display !== 'none'
                        && style.visibility !== 'hidden'
                        && element.scrollWidth > element.clientWidth + 0.5;
                })
                .sort((a, b) => (b.scrollWidth - b.clientWidth)
                    - (a.scrollWidth - a.clientWidth))
                .slice(0, 8)
                .map(element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        node: `${element.tagName.toLowerCase()}#${element.id}`
                            + `.${String(element.className).replaceAll(' ', '.')}`,
                        clientWidth: element.clientWidth,
                        scrollWidth: element.scrollWidth,
                        left: Math.round(rect.left),
                        right: Math.round(rect.right),
                    };
                }),
        })"""
    )
    overflow = metrics['overflow']
    assert overflow <= 0, (
        f'{surface_name} has {overflow}px of horizontal overflow at '
        f'{page.viewport_size}; right-edge offenders: {metrics["offenders"]}; '
        f'internal overflow: {metrics["internalOverflow"]}'
    )

def _assert_visible_targets_are_44px(locator, surface_name):
    visible = [locator.nth(index) for index in range(locator.count())
               if locator.nth(index).is_visible()]
    assert visible, f'{surface_name} exposed no visible interaction targets'
    for target in visible:
        box = target.bounding_box()
        assert box is not None
        assert box['width'] >= 44, (
            f'{surface_name} target {target.get_attribute("aria-label") or target.inner_text()!r} '
            f'is {box["width"]:.1f}x{box["height"]:.1f}px; expected at least 44x44px'
        )
        assert box['height'] >= 44, (
            f'{surface_name} target {target.get_attribute("aria-label") or target.inner_text()!r} '
            f'is {box["width"]:.1f}x{box["height"]:.1f}px; expected at least 44x44px'
        )

def _assert_computed_contrast_aa(page, selector, label):
    """Measure WCAG relative luminance from the rendered computed styles."""
    result = page.locator(selector).first.evaluate(
        """element => {
            const parse = value => {
                const colorPattern = new RegExp(
                    'rgba?\\\\(\\\\s*([\\\\d.]+)[, ]+\\\\s*([\\\\d.]+)[, ]+'
                    + '\\\\s*([\\\\d.]+)(?:\\\\s*[,/]\\\\s*([\\\\d.]+))?\\\\s*\\\\)'
                );
                const match = value.match(colorPattern);
                if (!match) throw new Error(`Unsupported computed color: ${value}`);
                return [Number(match[1]), Number(match[2]), Number(match[3]),
                    match[4] === undefined ? 1 : Number(match[4])];
            };
            const luminance = channels => {
                const linear = channels.slice(0, 3).map(channel => {
                    const value = channel / 255;
                    return value <= 0.04045
                        ? value / 12.92
                        : ((value + 0.055) / 1.055) ** 2.4;
                });
                return 0.2126 * linear[0] + 0.7152 * linear[1]
                    + 0.0722 * linear[2];
            };
            const style = getComputedStyle(element);
            const foreground = parse(style.color);
            let backgroundNode = element;
            let background = [255, 255, 255, 1];
            while (backgroundNode) {
                const candidate = parse(getComputedStyle(backgroundNode).backgroundColor);
                if (candidate[3] > 0) {
                    background = candidate;
                    break;
                }
                backgroundNode = backgroundNode.parentElement;
            }
            if (background[3] < 1) {
                background = background.slice(0, 3).map(
                    value => value * background[3] + 255 * (1 - background[3])
                ).concat(1);
            }
            const lighter = Math.max(luminance(foreground), luminance(background));
            const darker = Math.min(luminance(foreground), luminance(background));
            const ratio = (lighter + 0.05) / (darker + 0.05);
            const fontSize = Number.parseFloat(style.fontSize);
            const fontWeight = Number.parseInt(style.fontWeight, 10) || 400;
            const large = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
            return {
                ratio,
                required: large ? 3 : 4.5,
                foreground: style.color,
                background: getComputedStyle(backgroundNode || document.body).backgroundColor,
                fontSize,
                fontWeight,
            };
        }"""
    )
    assert result['ratio'] >= result['required'], (
        f'{label} contrast is {result["ratio"]:.2f}:1 '
        f'({result["foreground"]} on {result["background"]}); '
        f'expected {result["required"]:.1f}:1 for '
        f'{result["fontSize"]}px/{result["fontWeight"]} text'
    )
