"""Canonical scoring identity stays independent from browser display aliases."""
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from telugu_panchangam.panchangam_names import YOGA_NAMES
from telugu_panchangam.personal.slot_scorers import score_nitya_yoga
from tools.export_shared_calendar_tables import build_export

CASES = json.loads((Path(__file__).parent / 'fixtures/nitya-yoga-vocabulary.json').read_text())


def test_all_canonical_yoga_indices_are_pinned():
    assert [case['canonical'] for case in CASES] == YOGA_NAMES
    assert [case['index'] for case in CASES] == list(range(27))
    assert build_export()['canonicalYogaNames'] == YOGA_NAMES


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['canonical'])
def test_yoga_fixture_matches_python_scoring(case):
    start = datetime(2026, 9, 19, 10, tzinfo=timezone.utc)
    day = SimpleNamespace(yoga=SimpleNamespace(name=case['canonical'], start=start))
    score, _, deferred = score_nitya_yoga(case['canonical'], start, day, False)
    assert score == case['score']
    assert deferred is False
