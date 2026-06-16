from datetime import date, timedelta
import pytest
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.pitru_paksha import is_pitru_paksha_day
from telugu_panchangam.cities import CITIES


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def test_is_pitru_paksha_day_pure():
    assert is_pitru_paksha_day('Bhadrapada', 'Krishna') is True
    assert is_pitru_paksha_day('Bhadrapada', 'Shukla') is False
    assert is_pitru_paksha_day('Ashvina', 'Krishna') is False
    assert is_pitru_paksha_day('Adhika Bhadrapada', 'Krishna') is True
    assert is_pitru_paksha_day('Nija Bhadrapada', 'Krishna') is True
    assert is_pitru_paksha_day(None, 'Krishna') is False


def test_pitru_paksha_in_actual_engine_output():
    """Find Pitru Paksha in 2026 calendar (Sep 27 – Oct 10 for this year)."""
    eng = DrikEngine()
    city = _hyderabad()
    found_count = 0
    # Scan Sep–Oct to catch the full paksha regardless of year-to-year drift.
    for d in range(45):
        target = date(2026, 9, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.is_pitru_paksha:
            found_count += 1
            # Verify the flag is consistent with the underlying data
            assert day.paksham == 'Krishna'
            base = day.maasam.removeprefix('Adhika ').removeprefix('Nija ')
            assert base == 'Bhadrapada'
    # Pitru Paksha is 15 civil days; allow 13 to account for tithi-skip days
    assert found_count >= 13, f"Expected ~14-15 Pitru Paksha days in Sep-Oct 2026; found {found_count}"


def test_flag_in_all_mcp_tool_responses():
    import json
    from telugu_panchangam.mcp.tools import (
        tool_get_panchangam, tool_get_muhurta, tool_get_panchangam_range,
    )
    out1 = json.loads(tool_get_panchangam('2026-09-15', city='Hyderabad'))
    assert 'is_pitru_paksha' in out1
    out2 = json.loads(tool_get_muhurta('2026-09-15', city='Hyderabad'))
    assert 'is_pitru_paksha' in out2
    out3 = json.loads(tool_get_panchangam_range('2026-09-15', '2026-09-16', city='Hyderabad'))
    assert 'is_pitru_paksha' in out3['days'][0]


def test_wedding_skipped_during_pitru_paksha():
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    for d in range(45):
        target = date(2026, 9, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if not day.is_pitru_paksha:
            continue
        slots = day_slots(day, activity='wedding')
        assert len(slots) == 0, (
            f"Expected 0 wedding slots on Pitru Paksha day {target}; got {len(slots)}"
        )
        return
    pytest.skip('No Pitru Paksha day found')
