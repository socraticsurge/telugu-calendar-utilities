"""Contracts for reproducible computation-architecture evidence."""
from datetime import date
from pathlib import Path

import pytest

from tools.analyze_computation_architecture import (
    _summary,
    build_report,
    source_scope_class,
)
from tools.benchmark_computation_paths import benchmark

ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / 'docs' / 'decisions' / '0002-computation-layer-organization.md'


def test_architecture_report_maps_modules_consumers_and_layers():
    report = build_report('HEAD', commit_limit=20)

    assert report['schema_version'] == 1
    assert report['scope']['source_files'] == 96
    assert report['scope']['established_source_files'] == 78
    assert report['scope']['additive_feature_source_files'] == 18
    assert report['scope']['total_source_files'] == 96
    assert report['scope']['source_files'] == report['scope']['total_source_files']
    assert report['scope']['source_files'] == (
        report['scope']['established_source_files']
        + report['scope']['additive_feature_source_files']
    )
    assert report['scope']['computation_records'] == 62
    assert len(report['output_consumer_map']) == 62
    assert len({item['id'] for item in report['output_consumer_map']}) == 62
    assert {'engines', 'derived-calendar', 'scoring', 'mcp', 'browser-panels'} \
        <= set(report['layers'])

    summary = _summary(report)
    assert 'Production modules: 96' in summary
    assert 'Established production modules: 78' in summary
    assert 'Additive feature modules: 18' in summary


def test_profiles_panel_extends_architecture_additively():
    assert source_scope_class('src/panels/profiles.ts') == 'additive-feature'


def test_guest_profile_store_extends_architecture_additively():
    assert source_scope_class('src/lib/guest-profile-store.ts') == 'additive-feature'


def test_profile_selection_extends_architecture_additively():
    assert source_scope_class('src/lib/profile-selection.ts') == 'additive-feature'


def test_birth_profile_api_extends_architecture_additively():
    assert source_scope_class('src/lib/birth-profile-api.ts') == 'additive-feature'


def test_remote_activation_extends_architecture_additively():
    assert source_scope_class(
        'src/lib/remote-calculation-activation.ts'
    ) == 'additive-feature'


def test_profile_journey_extends_architecture_additively():
    report = build_report('HEAD', commit_limit=20)
    module_scopes = {
        item['path']: item['scope_class']
        for item in report['modules']
    }

    assert {
        path: module_scopes[path]
        for path in (
            'src/lib/birth-profile-api.ts',
            'src/lib/guest-profile-store.ts',
            'src/lib/profile-selection.ts',
            'src/panels/profiles.ts',
        )
    } == {
        'src/lib/birth-profile-api.ts': 'additive-feature',
        'src/lib/guest-profile-store.ts': 'additive-feature',
        'src/lib/profile-selection.ts': 'additive-feature',
        'src/panels/profiles.ts': 'additive-feature',
    }


@pytest.mark.parametrize('ref', ('--help', 'HEAD..master', 'HEAD^{tree}', '../HEAD'))
def test_architecture_report_rejects_unsafe_git_refs(ref):
    with pytest.raises(ValueError, match='unsupported Git ref'):
        build_report(ref, commit_limit=1)


@pytest.mark.parametrize('commit_limit', (0, -1, 10_001))
def test_architecture_report_bounds_history_work(commit_limit):
    with pytest.raises(ValueError, match='commit_limit must be between'):
        build_report('HEAD', commit_limit=commit_limit)


def test_architecture_report_exposes_real_boundary_risks():
    report = build_report('HEAD', commit_limit=20)
    boundary = report['api_boundary']

    private_mcp_symbols = {
        item['symbol'] for item in boundary['private_symbol_imports']
        if item['importer'] == 'telugu_panchangam/mcp/tools.py'
    }
    assert private_mcp_symbols == {
        '_validate_ayanamsa', '_nak_index', '_rasi_index',
    }
    assert {
        (item['path'], item['expression'])
        for item in boundary['engine_private_attribute_access']
    } == {
        ('telugu_panchangam/personal/homa.py',
         'engine._sun_longitude_func'),
    }
    assert boundary['concrete_engine_module_imports']


def test_architecture_report_tracks_generation_and_manual_mirrors():
    report = build_report('HEAD', commit_limit=20)
    groups = {item['name']: item for item in report['duplicate_contracts']}

    assert len(groups) == 8
    assert groups['activity_profiles']['strategy'] == 'generated-from-python'
    assert sum(
        item['strategy'] == 'manual-mirror' for item in groups.values()
    ) == 7
    assert all(
        location['line'] is not None
        for item in groups.values()
        for location in item['locations']
    )
    assert report['generated_contracts'][0]['exported_rule_count'] == 30


def test_enginecore_evidence_records_current_asymmetry_without_changing_it():
    report = build_report('HEAD', commit_limit=20)
    engines = report['engine_asymmetry']

    assert engines['DrikGanitaEngine']['bases'] == ['PanchangamEngine']
    assert engines['SuryaSiddhantaEngine']['bases'] == ['PanchangamEngine']
    assert engines['VakyaEngine']['bases'] == ['SuryaSiddhantaEngine']
    assert len(engines['shared_method_names']['all_three']) == 10


def test_runtime_comparison_tool_reports_all_existing_systems():
    report = benchmark(
        start=date(2026, 1, 1),
        days=1,
        runs=1,
        facts_per_day=1,
    )

    assert report['parameters']['include_eclipse'] is False
    assert {item['system'] for item in report['systems']} == {
        'drik', 'surya_siddhanta', 'vakya',
    }
    assert all(item['facts_evaluations'] == 1 for item in report['systems'])


def test_architecture_decision_has_required_tradeoffs_and_approval_gates():
    decision = ADR.read_text(encoding='utf-8')

    for phrase in (
        'Runtime efficiency',
        'Developer change efficiency',
        'Correctness and verification risk',
        'Expected benefit',
        'Migration/correctness risk',
        'Verification strategy',
        'Owner approval?',
        'Why EngineCore remains parked',
        'Reactivation',
        '#182',
        '#183',
        '#184',
    ):
        assert phrase in decision
