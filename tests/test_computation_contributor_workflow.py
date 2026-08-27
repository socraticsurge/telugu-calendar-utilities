"""The computation contributor workflow must retain its safety gates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_contributing_links_the_computation_workflow():
    contributing = _read('CONTRIBUTING.md')

    assert 'docs/reference/10-computation-contributor-workflow.md' in contributing


def test_workflow_names_every_required_stop_and_release_gate():
    workflow = _read('docs/reference/10-computation-contributor-workflow.md')

    for required in (
        'telugu_panchangam/engines/',
        'generators/ics.py',
        '.github/workflows/',
        'Existing test assertion',
        'explicit owner approval',
        'screenshots and owner sign-off',
        'PyPI version bump',
        'python tools/verify_project.py',
    ):
        assert required in workflow


def test_workflow_separates_regression_from_independent_verification():
    workflow = _read('docs/reference/10-computation-contributor-workflow.md')
    normalized = ' '.join(workflow.split())

    assert 'They do not independently verify a formula or textual rule.' in normalized
    assert 'more than one city' in workflow
    assert 'modern Drik result is not the authority' in workflow
    assert '`needs_locator`' in workflow


def test_copyable_template_covers_inventory_and_review_contract():
    template = _read('docs/reference/computation-record-template.md')

    for required in (
        '"id"',
        '"owning_layer"',
        '"implementations"',
        '"inputs"',
        '"outputs"',
        '"time_basis"',
        '"surfaces"',
        '"provenance"',
        '"tests"',
        '"limitations"',
        'computations.json',
        'python tools/verify_project.py',
    ):
        assert required in template


def test_example_matches_the_canonical_panchanga_shuddhi_record():
    workflow = _read('docs/reference/10-computation-contributor-workflow.md')

    for required in (
        'derived.panchanga-shuddhi',
        'telugu_panchangam/panchanga_shuddhi.py',
        'assess_shuddhi',
        'tests/test_panchanga_shuddhi.py',
        '`needs_locator`',
    ):
        assert required in workflow
