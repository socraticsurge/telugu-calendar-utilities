"""Architectural and behavioral checks for the transport-independent service."""
from datetime import date
from pathlib import Path

import pytest

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.muhurta_search import search_muhurta
from telugu_panchangam.personal.search_contract import SearchOptions, SearchPeriod


def test_search_returns_unformatted_untruncated_decisions():
    location = next(city for city in CITIES if city.name == 'Hyderabad')
    result = search_muhurta(SearchPeriod(date(2026, 7, 18), 3), location,
                            DrikGanitaEngine(), SearchOptions(include_night=True))
    assert len(result.slots) > 12
    for slot in result.slots:
        assert slot['start'].tzinfo is not None
        assert slot['end'] > slot['start']
        assert set(slot['reason_groups']) == {
            'slot_quality', 'day_quality', 'group_fit', 'activity_match', 'notes'}
        if slot['personal_dosha'] is not None or slot['day_dosha'] is not None:
            assert slot['tier'] != 'Excellent'


def test_search_does_not_import_transport_or_serialize_responses():
    source = (Path(__file__).parents[1] /
              'telugu_panchangam/personal/muhurta_search.py').read_text()
    assert 'telugu_panchangam.mcp' not in source
    assert 'json.dumps' not in source
    assert 'slots[:12]' not in source


@pytest.mark.parametrize('count', [0, 15])
def test_search_limit_is_enforced_before_engine_work(count):
    with pytest.raises(ValueError, match='between 1 and 14'):
        search_muhurta(SearchPeriod(date(2026, 7, 18), count), CITIES[0], None, SearchOptions())
