"""Guard high-level documentation against reintroducing resolved project state."""
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_current_docs_do_not_describe_shipped_frontend_work_as_future():
    product = _read('PRODUCT.md')
    roadmap = _read('docs/reference/06-roadmap-and-backlog.md')

    assert 'Known backlog (improvement-plan Phase 4)' not in product
    assert 'PR 2a WIP' not in roadmap
    assert '**Vite + TypeScript migration**' not in roadmap
    assert '**Shipped.** Root `index.html`, `src/`' in roadmap


def test_maintenance_runbook_points_to_the_maintained_roadmap():
    runbook = _read('MAINTENANCE_RUNBOOK.md')

    assert 'docs/reference/06-roadmap-and-backlog.md' in runbook
    assert 'for the active phased roadmap' not in runbook


def test_activity_documentation_avoids_a_stale_fixed_count():
    muhurta_table = _read('docs/reference/07-muhurta-table.md')

    assert '30-activity model' not in muhurta_table
    assert 'source-profile activity catalogue' in muhurta_table


def test_documentation_source_and_projection_contract_is_discoverable():
    project_readme = _read('README.md')
    contributor_guide = _read('CONTRIBUTING.md')
    docs_standard = _read('docs/README.md')
    reference_index = _read('docs/reference/README.md')

    assert 'docs/README.md' in project_readme
    assert 'docs/README.md' in contributor_guide
    assert 'canonical source' in docs_standard.lower()
    assert 'generated projection' in docs_standard.lower()
    assert 'https://panchangam.astrochaganti.com/docs/' in docs_standard
    assert 'how this is calculated' in docs_standard.lower()
    assert 'verify this result' in docs_standard.lower()
    assert 'Gitignored' not in reference_index
    assert 'local only' not in reference_index
