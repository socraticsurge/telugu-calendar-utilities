"""Contract tests for the canonical production-computation inventory."""
import json
from pathlib import Path

from tools.check_computation_inventory import REGISTRY_PATH, validate_registry

ROOT = Path(__file__).resolve().parents[1]


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))


def test_computation_inventory_passes_its_contract():
    assert validate_registry() == []


def test_inventory_covers_public_computation_families_and_browser_mirrors():
    records = _registry()['computations']
    by_id = {record['id']: record for record in records}

    assert len(records) >= 50
    assert {
        'panchangam.tithi',
        'panchangam.nakshatra',
        'panchangam.eclipse-sutak',
        'personal.tarabalam',
        'personal.muhurta-slot-ranking',
        'gochara.transit-verdicts',
        'interpretation.daily-rasi-phalalu-generated',
    } <= set(by_id)

    mirror_paths = {
        implementation['path']
        for record in records
        for implementation in record['implementations']
        if implementation['role'] == 'mirror'
    }
    assert 'src/panels/tarabalam.ts' in mirror_paths
    assert 'src/panels/gochara.ts' in mirror_paths
    assert 'src/panels/today.ts' in mirror_paths


def test_inventory_test_links_are_repository_relative():
    for record in _registry()['computations']:
        for test_path in record['tests']:
            path = Path(test_path)
            assert not path.is_absolute()
            assert '..' not in path.parts
            assert (ROOT / path).is_file()
