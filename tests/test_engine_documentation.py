"""Freshness contract for the engine and PanchangamDay documentation."""
import json
import re
from dataclasses import fields
from pathlib import Path

from telugu_panchangam.engines.base import PanchangamEngine
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.models.panchangam_day import PanchangamDay

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / 'docs/reference/02-engines-and-model.md'
PROVENANCE_PATH = ROOT / 'docs/reference/provenance.json'


def _doc() -> str:
    return DOC_PATH.read_text(encoding='utf-8')


def test_engine_documentation_maps_every_panchangam_day_field():
    documentation = _doc()

    for model_field in fields(PanchangamDay):
        assert f'`{model_field.name}`' in documentation


def test_engine_documentation_symbols_and_claims_stay_live():
    documentation = _doc()
    symbol_owners = {
        PanchangamEngine: ('facts_at', '_festivals', '_finalize_day'),
        DrikGanitaEngine: (
            '_tithi_span', '_nakshatra_span', '_yoga_span', '_karana_spans'),
        SuryaSiddhantaEngine: (
            '_tithi_span', '_nakshatra_span', '_yoga_span', '_karana_spans'),
        VakyaEngine: (
            '_tithi_span', '_nakshatra_span', '_yoga_span', '_karana_spans'),
    }
    for owner, symbols in symbol_owners.items():
        for symbol in symbols:
            assert hasattr(owner, symbol)
            documented_symbol = re.compile(
                rf'`(?:[A-Za-z0-9_.]+\.)?{re.escape(symbol)}`')
            assert documented_symbol.search(documentation)

    provenance = json.loads(PROVENANCE_PATH.read_text(encoding='utf-8'))
    claim_ids = {claim['id'] for claim in provenance['claims']}
    required_claims = {
        'drik.sidereal_positions',
        'surya_siddhanta.mean_motion_manda',
        'vakya.provisional_lunar_model',
        'panchangam.rise_set_convention',
        'panchangam.calendar_semantics',
        'panchangam.mixed_daily_windows',
    }
    assert required_claims <= claim_ids
    for claim_id in required_claims:
        assert f'`{claim_id}`' in documentation


def test_engine_documentation_local_links_and_test_paths_exist():
    documentation = _doc()

    for target in re.findall(r'\[[^]]+\]\(([^)]+)\)', documentation):
        if '://' in target or target.startswith('#'):
            continue
        local_target = target.split('#', maxsplit=1)[0]
        assert (DOC_PATH.parent / local_target).resolve().exists(), target

    test_paths = set(re.findall(r'`(tests/[^`]+\.py)`', documentation))
    assert test_paths
    for test_path in test_paths:
        assert (ROOT / test_path).is_file(), test_path


def test_engine_documentation_does_not_restore_superseded_claims():
    documentation = _doc()

    assert 'Each engine differs *only*' not in documentation
    assert 'every anga from just two functions' not in documentation
    assert 'oscillates ±1° over a ~248-year cycle' not in documentation
