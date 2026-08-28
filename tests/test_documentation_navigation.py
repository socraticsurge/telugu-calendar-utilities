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
