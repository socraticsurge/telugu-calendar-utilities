"""The documented one-command verifier must retain every quality gate."""
from tools.verify_project import commands


def test_verification_contract_covers_all_project_surfaces():
    checks = commands('PYTHON')
    assert checks == [
        ['PYTHON', 'tools/check_activity_provenance.py'],
        ['PYTHON', 'tools/export_activity_rules.py', '--check'],
        ['PYTHON', 'tools/check_ruff_baseline.py'],
        ['PYTHON', 'tools/check_complexity_baseline.py'],
        ['PYTHON', '-m', 'pytest', 'tests/'],
        ['npm', 'run', 'lint'],
        ['npm', 'run', 'test:coverage'],
        ['npm', 'run', 'build'],
    ]
