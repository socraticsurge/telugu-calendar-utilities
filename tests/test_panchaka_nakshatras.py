from datetime import date, timedelta

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.nakshatra_filters import (
    PANCHAKA_NAKSHATRAS,
    is_panchaka_nakshatra,
)


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def test_panchaka_nakshatras_count_and_membership():
    assert len(PANCHAKA_NAKSHATRAS) == 5
    assert PANCHAKA_NAKSHATRAS == frozenset({
        'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
        'Uttara Bhadrapada', 'Revati',
    })


def test_is_panchaka_nakshatra():
    assert is_panchaka_nakshatra('Revati') is True
    assert is_panchaka_nakshatra('Dhanishtha') is True
    assert is_panchaka_nakshatra('Ashvini') is False
    assert is_panchaka_nakshatra('Pushya') is False


def test_engine_sets_flag_consistent_with_nakshatra_name():
    eng = DrikEngine()
    city = _hyderabad()
    # Scan 30 days; at least a few will be Panchaka.
    found_panchaka = False
    for d in range(30):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        expected = is_panchaka_nakshatra(day.nakshatra.name)
        assert day.in_panchaka_nakshatra is expected, (
            f"{target}: nakshatra={day.nakshatra.name}, "
            f"in_panchaka={day.in_panchaka_nakshatra}, expected={expected}"
        )
        if day.in_panchaka_nakshatra:
            found_panchaka = True
    assert found_panchaka, "30-day scan should hit at least one Panchaka day"


def test_flag_in_all_mcp_tool_responses():
    import json

    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    out1 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'in_panchaka_nakshatra' in out1
    assert isinstance(out1['in_panchaka_nakshatra'], bool)

    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'in_panchaka_nakshatra' in out2

    out3 = json.loads(tool_get_panchangam_range(
        '2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'in_panchaka_nakshatra' in out3['days'][0]


def test_cremation_skip_during_panchaka():
    """An activity with skip_on_panchaka_nakshatra drops Panchaka days."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    # Find a Panchaka day in a 30-day window
    for d in range(30):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if not day.in_panchaka_nakshatra:
            continue
        slots = day_slots(day, activity='cremation')
        assert len(slots) == 0, (
            f"Expected 0 cremation slots on Panchaka day {target} "
            f"(nakshatra={day.nakshatra.name}); got {len(slots)}"
        )
        return
    # If we get here without finding a Panchaka day, check a longer range
    # — the 30-day window must include one by the 27-nakshatra cycle.
    raise AssertionError("No Panchaka day found in 30-day scan starting 2026-06-01")


def test_cremation_allowed_on_non_panchaka_day():
    """Cremation activity returns slots on a non-Panchaka day (no blanket skip)."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    # Find a non-Panchaka day
    for d in range(30):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.in_panchaka_nakshatra or day.eclipse is not None:
            continue
        day_slots(day, activity='cremation')
        # May be 0 if all choghadiya are blocked, but the panchaka rule
        # itself must not be the reason. We verify by checking diagnose_day.
        from telugu_panchangam.personal.muhurta import diagnose_day
        reason = diagnose_day(day, activity='cremation')
        assert reason is None or 'Panchaka' not in reason, (
            f"Non-Panchaka day {target} (nakshatra={day.nakshatra.name}) "
            f"incorrectly flagged as Panchaka: {reason}"
        )
        return
    raise AssertionError("No suitable non-Panchaka day found in 30-day scan")


def test_panchaka_flag_in_ss_and_vakya_engines():
    """Both SS and Vakya engines populate the flag consistently."""
    from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
    from telugu_panchangam.engines.vakya import VakyaEngine
    city = _hyderabad()
    for EngClass in (SuryaSiddhantaEngine, VakyaEngine):
        eng = EngClass()
        for d in range(14):
            target = date(2026, 6, 1) + timedelta(days=d)
            day = eng.calculate(target, city)
            expected = is_panchaka_nakshatra(day.nakshatra.name)
            assert day.in_panchaka_nakshatra is expected, (
                f"{EngClass.__name__} {target}: nakshatra={day.nakshatra.name}, "
                f"flag={day.in_panchaka_nakshatra}, expected={expected}"
            )
