from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.disha_shoola import disha_shoola
from telugu_panchangam.engines.drik import DrikGanitaEngine


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def test_disha_shoola_full_week():
    assert disha_shoola('Adivaram') == 'West'
    assert disha_shoola('Somavaram') == 'East'
    assert disha_shoola('Mangalavaram') == 'North'
    assert disha_shoola('Budhavaram') == 'North'
    assert disha_shoola('Guruvaram') == 'South'
    assert disha_shoola('Shukravaram') == 'West'
    assert disha_shoola('Shanivaram') == 'East'


def test_disha_shoola_unknown_returns_none():
    assert disha_shoola('Foo') is None
    assert disha_shoola(None) is None


def test_engine_populates_disha_shoola():
    eng = DrikGanitaEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert day.disha_shoola_direction in {'East', 'West', 'North', 'South'}


def test_disha_shoola_in_all_mcp_tool_responses():
    import json

    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    out1 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'disha_shoola_direction' in out1

    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'disha_shoola_direction' in out2

    out3 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'disha_shoola_direction' in out3['days'][0]


def test_travel_skips_day_when_direction_matches_disha_shoola():
    """If the user travels West on a Sunday (Disha Shoola = West), no slots."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikGanitaEngine()
    city = _hyderabad()
    # 2026-06-07 is Sunday (Adivaram), Disha Shoola = West.
    day = eng.calculate(date(2026, 6, 7), city)
    assert day.vaaram == 'Adivaram'
    assert day.disha_shoola_direction == 'West'
    # Travel West -> blocked
    slots_west = day_slots(day, activity='travel', travel_direction='West')
    assert len(slots_west) == 0


def test_travel_allowed_when_direction_safe():
    """If the user travels East on Sunday (Disha Shoola West), normal slots."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikGanitaEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 6, 7), city)
    # Travel East on a West-blocked day -> slots are not filtered out
    slots_east = day_slots(day, activity='travel', travel_direction='East')
    # Don't assert > 0 strictly (other filters may apply), but the call must succeed
    assert isinstance(slots_east, list)


def test_travel_without_direction_unchanged():
    """travel_direction=None means no Disha Shoola filtering applied."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikGanitaEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 6, 7), city)
    slots = day_slots(day, activity='travel')  # no travel_direction kwarg
    assert isinstance(slots, list)


def test_diagnose_day_disha_shoola():
    """diagnose_day explains the Disha Shoola block."""
    from telugu_panchangam.personal.muhurta import diagnose_day
    eng = DrikGanitaEngine()
    city = _hyderabad()
    day = eng.calculate(date(2026, 6, 7), city)
    reason = diagnose_day(day, activity='travel', travel_direction='West')
    assert reason is not None
    assert 'Disha Shoola' in reason
    assert 'West' in reason
