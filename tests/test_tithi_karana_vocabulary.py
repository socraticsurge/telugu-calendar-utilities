"""The vocabulary export retains canonical order and browser compatibility."""

import json

import pytest

from telugu_panchangam import panchangam_names as names
from telugu_panchangam.personal import tithi_class
from tools.export_shared_calendar_tables import ROOT, build_export

CASES = json.loads((ROOT / 'tests/fixtures/tithi-karana-browser-vocabulary.json').read_text())


def test_export_uses_existing_tithi_and_karana_owners():
    data = build_export()
    assert data['tithiNames'] == names.TITHI_NAMES
    assert data['tithiWithinPakshaNames'] == tithi_class.TITHI_NAMES
    assert data['tithiAliases'] == tithi_class._ALIASES
    assert data['karanaRepeating'] == names.KARANA_REPEATING
    assert data['karanaFixed'] == names.KARANA_FIXED
    assert data['schemaVersion'] == 1


@pytest.mark.parametrize('case', CASES, ids=lambda case: str(case['halfTithiIndex']))
def test_all_browser_half_tithi_fixtures_match_canonical_vocabulary(case):
    index = case['halfTithiIndex']
    assert case['facts']['tithi'] == names.TITHI_NAMES[index // 2]
    assert case['facts']['karana'] == names.KARANA_FIXED.get(
        index, names.KARANA_REPEATING[(index - 1) % 7],
    )


def test_fixture_covers_every_half_tithi_index_once():
    assert [case['halfTithiIndex'] for case in CASES] == list(range(60))
