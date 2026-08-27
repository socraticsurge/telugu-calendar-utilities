"""Contracts for bounded GitHub Pages history and custom-domain safety."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY_WORKFLOWS = (
    'deploy-landing.yml',
    'generate.yml',
    'gochara.yml',
    'lagna.yml',
    'rasi_phalalu.yml',
)


def test_partial_pages_deploys_keep_the_complete_live_tree():
    for name in DEPLOY_WORKFLOWS:
        workflow = (ROOT / '.github/workflows' / name).read_text()
        assert 'keep_files: true' in workflow
        assert 'force_orphan:' not in workflow
        assert 'cname: panchangam.astrochaganti.com' in workflow


def test_pages_compactor_preserves_the_tree_in_a_parentless_commit():
    workflow = (ROOT / '.github/workflows/compact-pages.yml').read_text()
    workflow_lines = {line.strip() for line in workflow.splitlines()}

    assert '-f tree="$current_tree"' in workflow
    assert 'parents[]' not in workflow
    assert 'parent_count' in workflow
    assert 'published_tree' in workflow
    assert '-F force=true' in workflow
    assert 'gh-pages moved during compaction' in workflow
    assert 'if [ "$cname" != "panchangam.astrochaganti.com" ]; then' in workflow_lines


def test_retention_runbook_defines_backup_verification_and_rollback():
    policy = (ROOT / 'docs/operations/gh-pages-retention.md').read_text().lower()

    for required in (
        'panchangam feeds',
        'gochara',
        'lagna',
        'rasi phalalu',
        'backup bundle',
        'rollback',
        'cname',
    ):
        assert required in policy
