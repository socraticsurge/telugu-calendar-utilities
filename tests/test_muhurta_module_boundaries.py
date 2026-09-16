"""Guard extraction direction and intentionally different day/night policies."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from telugu_panchangam.personal import muhurta
from telugu_panchangam.personal.muhurta_eligibility import (
    _chandra_position_rejection,
    _day_skip_reason,
    _night_traditional_skip,
    _traditional_skip_reason,
)
from tools.analyze_computation_architecture import _layer, source_scope_class

ROOT = Path(__file__).resolve().parents[1]
MODULES = ('muhurta_eligibility', 'muhurta_slot_scoring', 'muhurta_explanations')


@pytest.mark.parametrize('name', MODULES)
def test_extracted_owners_remain_visible_in_the_scoring_architecture(name):
    path = f'telugu_panchangam/personal/{name}.py'
    assert _layer(path) == 'scoring'
    assert source_scope_class(path) == 'additive-feature'


def _imported_modules(source):
    imports = []
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or '')
            imports.extend(f'{node.module}.{alias.name}' for alias in node.names)
    return imports


@pytest.mark.parametrize('name', MODULES)
@pytest.mark.parametrize('forbidden', (
        'telugu_panchangam.mcp',
        'telugu_panchangam.generators',
        'telugu_panchangam.engines',
        'telugu_panchangam.personal.muhurta',
        'telugu_panchangam.personal.muhurta_search',
))
def test_extracted_modules_do_not_import_transport_or_orchestration(name, forbidden):
    source = ROOT / 'telugu_panchangam/personal' / f'{name}.py'
    assert not [
        imported for imported in _imported_modules(source)
        if imported == forbidden or imported.startswith(forbidden + '.')
    ]


def test_eclipse_rejection_precedes_other_day_policies():
    day = SimpleNamespace(eclipse=SimpleNamespace(kind='solar'))
    assert _day_skip_reason(
        day, {}, 'any', None, None, 'stars', {'admissible': False}
    ) == 'solar eclipse · auspicious activities deferred'


def test_night_admission_does_not_apply_day_yoga_rejection():
    day = SimpleNamespace(special_yogas=['Visha'], yoga=SimpleNamespace(name='Siddhi'))
    rules = {'label': 'Test activity', 'skip_on_yoga': ['Visha']}
    assert _traditional_skip_reason(day, rules) == (
        'Visha · Test activity traditionally avoids this day'
    )
    assert not _night_traditional_skip(day, rules)


@pytest.mark.parametrize('mode', ['strict', 'puja_ok', 'stars', 'unknown'])
def test_absent_participants_do_not_trigger_chandra_rejection(mode):
    assert _chandra_position_rejection([], mode) is None


@pytest.mark.parametrize('mode,position,rejected', [
    ('strict', 2, True), ('puja_ok', 2, False),
    ('strict', 4, True), ('puja_ok', 4, True), ('stars', 4, False),
])
def test_chandra_modes_retain_their_distinct_admission_sets(mode, position, rejected):
    assert (_chandra_position_rejection([position], mode) is not None) == rejected


@pytest.mark.parametrize('function,args', [
    (muhurta.day_slots, (None,)), (muhurta.night_slots, (None, None)),
])
@pytest.mark.parametrize('options,message', [
    ({'activity': 'invalid', 'chandra_mode': 'invalid'}, 'activity must be one of'),
    ({'chandra_mode': 'invalid'}, 'chandra_mode must be one of'),
    ({'janma_nakshatras': ['Rohini'], 'janma_rasis': []}, 'janma_rasis must align'),
])
def test_public_validation_precedes_day_access(function, args, options, message):
    with pytest.raises(ValueError, match=message):
        function(*args, **options)
