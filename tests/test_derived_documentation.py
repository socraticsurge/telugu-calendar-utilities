"""Contract tests for the non-engine computation documentation."""
from __future__ import annotations

import json
import re
from pathlib import Path

from telugu_panchangam.personal.activity_catalog import (
    BROWSER_ACTIVITIES,
    BROWSER_ACTIVITY_GROUPS,
)
from telugu_panchangam.personal.activity_rules import ACTIVITIES, ACTIVITY_RULES
from tools.check_activity_provenance import audit

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'docs' / 'reference'
DOC03 = REFERENCE / '03-computational-features.md'
DOC05 = REFERENCE / '05-data-flow-and-muhurta.md'
DOC08 = REFERENCE / '08-provenance-and-authority.md'
REGISTRY = REFERENCE / 'computations.json'


def _text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_every_non_engine_computation_has_a_human_readable_contract():
    registry = json.loads(_text(REGISTRY))
    records = [
        record for record in registry['computations']
        if record['owning_layer'] != 'engine-core'
    ]
    documentation = _text(DOC03)

    assert len(records) == 35
    for record in records:
        assert f"`{record['id']}`" in documentation, record['id']


def test_documented_activity_capability_boundary_matches_code():
    documentation = _text(DOC03) + _text(DOC05)
    backend_only = set(ACTIVITY_RULES) - set(BROWSER_ACTIVITIES)

    assert len(ACTIVITY_RULES) == 35
    assert len(ACTIVITIES) == 36
    assert len(BROWSER_ACTIVITIES) == 30
    assert len(BROWSER_ACTIVITY_GROUPS) == 7
    assert backend_only == {
        'beginning',
        'construction_roof',
        'coronation',
        'cremation',
        'wood_cutting',
    }
    for phrase in (
        '35 canonical',
        '36 accepted',
        '30 browser',
        'seven selector groups',
        '`litigation` → `court`',
    ):
        assert phrase in documentation
    for activity in backend_only:
        assert f'`{activity}`' in documentation


def test_provenance_summary_is_generated_from_the_current_activity_ledger():
    result = audit()
    documentation = _text(DOC08)

    assert result['errors'] == []
    assert result['activity_count'] == 35
    assert result['verified_profile_count'] == 34
    assert result['known_conflicts'] == {}
    assert len(result['heuristic_profiles']) == 1
    assert '34 verified canonical profiles' in documentation
    assert 'no contradicted\nprofiles' in documentation
    assert '1 explicit project heuristic' in documentation
    assert 'all 35 canonical profiles' in documentation


def test_docs_separate_owners_mirrors_and_generated_interpretation():
    documentation = _text(DOC03)

    assert 'Python is the owner' in documentation
    assert 'MCP serializes the\nPython result' in documentation
    assert 'browser is not an independent external\nverification source' in documentation
    assert 'interpretation.daily-rasi-phalalu-deterministic' in documentation
    assert 'interpretation.daily-rasi-phalalu-generated' in documentation
    assert 'Generated prose is never used as an input' in documentation
    assert 'How this is calculated' in documentation
    assert 'Verify this result' in documentation


def test_local_markdown_links_in_derived_contract_resolve():
    documentation = _text(DOC03)
    targets = re.findall(r'\]\(([^)#]+\.md)(?:#[^)]*)?\)', documentation)

    assert targets
    for target in targets:
        assert (DOC03.parent / target).is_file(), target
