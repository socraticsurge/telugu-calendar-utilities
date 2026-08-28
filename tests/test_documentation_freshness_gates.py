"""Contract tests for computation-documentation coverage and freshness."""
import json

from tools.check_computation_inventory import REGISTRY_PATH, validate_registry
from tools.check_documentation_freshness import build_facts, validate_documentation
from tools.verify_project import all_commands, commands, documentation_commands


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))


def test_complete_verifier_runs_documentation_gates_before_existing_contract():
    documentation = documentation_commands('PYTHON')
    assert documentation == [
        ['PYTHON', 'tools/check_computation_inventory.py'],
        ['PYTHON', 'tools/check_documentation_freshness.py'],
    ]
    assert all_commands('PYTHON') == documentation + commands('PYTHON')


def test_generated_facts_and_high_level_docs_are_current():
    assert validate_documentation() == []


def test_project_facts_are_derived_from_canonical_sources():
    facts = build_facts()

    assert facts['base_feed_count'] == (
        facts['city_count'] * len(facts['calculation_systems'])
    )
    assert facts['computation_inventory']['implementation_count'] == (
        facts['computation_inventory']['owner_count']
        + facts['computation_inventory']['mirror_count']
    )
    assert facts['muhurta_activities']['accepted_key_count'] == (
        facts['muhurta_activities']['canonical_count']
        + len(facts['muhurta_activities']['aliases'])
    )


def test_unclassified_production_source_reports_an_actionable_path(tmp_path):
    registry = _registry()
    excluded = registry['coverage']['exclusions'].pop()
    path = tmp_path / 'computations.json'
    path.write_text(json.dumps(registry), encoding='utf-8')

    errors = validate_registry(path)

    assert any(
        'unclassified production source paths' in error
        and excluded['path'] in error
        for error in errors
    )


def test_renamed_implementation_symbol_reports_record_path_and_symbol(tmp_path):
    registry = _registry()
    record = registry['computations'][0]
    implementation = record['implementations'][0]
    implementation['symbol'] = 'symbol_that_does_not_exist'
    path = tmp_path / 'computations.json'
    path.write_text(json.dumps(registry), encoding='utf-8')

    errors = validate_registry(path)

    assert any(
        record['id'] in error
        and implementation['path'] in error
        and 'symbol_that_does_not_exist' in error
        for error in errors
    )
