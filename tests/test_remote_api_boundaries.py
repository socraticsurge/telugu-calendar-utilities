"""Guard browser API dependency direction without changing runtime contracts."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'src/lib'


def imports(path):
    source = path.read_text()
    return re.findall(r'''(?:from\s*|import\s*\()['"]([^'"]+)['"]''', source)


@pytest.mark.parametrize('path', sorted((LIB / 'guest-profile').glob('*.ts')))
def test_persistence_never_imports_endpoint_clients(path):
    assert not any('birth-profile-api' in name or 'election-chart-api' in name
                   for name in imports(path))


@pytest.mark.parametrize('path', [LIB / 'chart-contracts.ts', LIB / 'local-chart-time.ts'])
def test_neutral_chart_modules_have_no_network_or_ui_dependency(path):
    assert not any('profile-api' in name or 'chart-api' in name or '/panels/' in name
                   or name.endswith('/http') or name.endswith('/base')
                   for name in imports(path))
    assert not re.search(r'\b(?:fetch|XMLHttpRequest)\s*\(', path.read_text())


@pytest.mark.parametrize('path', sorted((LIB / 'remote-api').glob('*.ts')))
def test_api_internals_never_import_facades_or_ui(path):
    assert not any('profile-api' in name or 'chart-api' in name or '/panels/' in name
                   or 'guest-profile' in name for name in imports(path))


def test_profile_wall_time_validation_uses_neutral_modules():
    dependencies = imports(ROOT / 'src/panels/profiles/birth-validation.ts')
    assert '../../lib/local-chart-time' in dependencies
    assert not any(name.endswith('-api') for name in dependencies)
