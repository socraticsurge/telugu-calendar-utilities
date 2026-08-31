"""The application exposes documentation without interrupting result panels."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_shared_navigation_has_one_same_site_documentation_link():
    landing = _read('index.html')

    assert landing.count('href="/docs/"') == 1
    assert '<span class="sidebar-label">Documentation</span>' in landing
    assert '<span class="sidebar-icon">📖</span>' in landing


def test_result_surfaces_do_not_embed_contextual_documentation_panels():
    sources = '\n'.join(
        _read(path)
        for path in (
            'index.html',
            'src/main.ts',
            'src/panels/today.ts',
            'src/panels/tarabalam.ts',
            'src/panels/gochara.ts',
        )
    )

    assert 'Computation reference' not in sources
    assert 'Verify this result' not in sources


def test_navigation_separates_primary_tools_from_resources_and_secondary_links():
    landing = _read('index.html')

    assert 'class="sidebar-group" aria-labelledby="sidebar-tools-label"' in landing
    assert '<h2 class="sidebar-group-label" id="sidebar-tools-label">Tools</h2>' in landing
    assert 'class="sidebar-group" aria-labelledby="sidebar-resources-label"' in landing
    assert '<h2 class="sidebar-group-label" id="sidebar-resources-label">Resources</h2>' in landing
    assert '<section class="sidebar-footer" aria-label="More">' in landing
    assert 'class="sidebar-item sidebar-secondary" id="sidebar-useinai"' in landing
    assert 'class="sidebar-item sidebar-secondary" id="sidebar-about"' in landing


def test_result_surfaces_link_to_method_records_instead_of_carrying_method_essays():
    landing = _read('index.html')
    today = _read('src/panels/today.ts')

    assert '/docs/computations/personal.muhurta-slot-ranking' in landing
    assert '/docs/computations/gochara.transit-verdicts' in landing
    assert '/docs/reference/02-engines-and-model' in landing
    assert '/docs/reference/09-computation-inventory' in landing
    assert 'Brihat Samhita 104.4 supplies the favourable houses' not in landing
    assert 'systems-more' not in landing
    assert 'Cells span sunrise to next sunrise' not in today
