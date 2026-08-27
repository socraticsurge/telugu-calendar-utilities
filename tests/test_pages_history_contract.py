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


def test_every_pages_deploy_keeps_live_files_but_bounds_history():
    for name in DEPLOY_WORKFLOWS:
        workflow = (ROOT / '.github/workflows' / name).read_text()
        assert 'keep_files: true' in workflow
        assert 'force_orphan: true' in workflow
        assert 'cname: panchangam.astrochaganti.com' in workflow


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
