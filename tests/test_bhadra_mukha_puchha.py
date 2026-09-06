from datetime import date

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def _find_vishti_day(year, month, eng=None, city=None):
    """Find first date in given month where any Vishti karana is in day.karana."""
    eng = eng or DrikGanitaEngine()
    city = city or _hyderabad()
    for d in range(1, 29):
        day = eng.calculate(date(year, month, d), city)
        if any(k.name == 'Vishti' for k in day.karana):
            return day
    return None


def test_mukha_and_puchha_present_when_vishti_in_day():
    day = _find_vishti_day(2026, 6)
    assert day is not None
    # If Vishti is within the day, at least one of Mukha/Puchha will be set;
    # both will be set when the full Vishti span fits within the day boundaries.
    assert day.bhadra_mukha is not None or day.bhadra_puchha is not None


def test_tithi_specific_yama_quarters_and_widths():
    """Verse 44 assigns quarters; Mukha=5/30 and Puchha=3/30 of Vishti."""
    from datetime import datetime, timedelta, timezone

    from telugu_panchangam.ghati import make_clock
    from telugu_panchangam.karana_windows import compute_bhadra_windows
    from telugu_panchangam.models.panchangam_day import Span

    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    end = start + timedelta(hours=12)
    clock = make_clock(start, start + timedelta(hours=24))
    expected = {
        'Shukla Chaturthi': (1, 4), 'Krishna Chaturdashi': (1, 4),
        'Shukla Ashtami': (2, 1), 'Krishna Dashami': (2, 1),
        'Shukla Ekadashi': (3, 2), 'Krishna Saptami': (3, 2),
        'Pournami': (4, 3), 'Krishna Tritiya': (4, 3),
    }
    for tithi, (mq, pq) in expected.items():
        mukha, puchha = compute_bhadra_windows(
            [Span('Vishti', start, end)], clock,
            tithi_at=lambda _dt, name=tithi: name,
        )
        assert mukha is not None
        assert puchha is not None
        total = (end - start).total_seconds()
        assert abs((mukha.start - start).total_seconds() - total * (mq - 1) / 4) < 1
        assert abs((mukha.end - mukha.start).total_seconds() - total * 5 / 30) < 1
        assert abs((puchha.end - start).total_seconds() - total * pq / 4) < 1
        assert abs((puchha.end - puchha.start).total_seconds() - total * 3 / 30) < 1


def test_litigation_alias_does_not_turn_approximate_puchha_into_legal_bonus():
    """The compatibility alias must use Court rules without a Puchha score."""
    from datetime import timedelta

    from telugu_panchangam.personal.muhurta import GOOD_CHOGHADIYA, day_slots

    eng = DrikGanitaEngine()
    city = _hyderabad()

    for d in range(0, 90):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.bhadra_puchha is None:
            continue
        p = day.bhadra_puchha
        # Only proceed when a good choghadiya block actually overlaps Puchha;
        # otherwise there can never be a bonus slot regardless of scoring.
        has_overlap = any(
            b.start < p.end and b.end > p.start
            for b in day.choghadiya
            if GOOD_CHOGHADIYA.get(b.name) is not None
        )
        if not has_overlap:
            continue
        slots = day_slots(day, activity='litigation')
        assert not any(
            'Bhadra Puchha' in reason
            for slot in slots for reason in slot.get('reasons', [])
        )
        return

    # If no qualifying day was found, skip rather than fail.
    import pytest
    pytest.skip('No day with good-choghadiya/Puchha overlap found in 90-day scan')


def test_no_slot_overlaps_bhadra_mukha():
    """No auspicious slot may overlap day.bhadra_mukha (hard cut-out window)."""
    from datetime import timedelta

    from telugu_panchangam.personal.muhurta import day_slots

    eng = DrikGanitaEngine()
    city = _hyderabad()

    found_mukha_day = False
    for d in range(0, 60):
        target = date(2026, 6, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.bhadra_mukha is None:
            continue
        found_mukha_day = True
        slots = day_slots(day, activity='any')
        mukha_s = day.bhadra_mukha.start
        mukha_e = day.bhadra_mukha.end
        for slot in slots:
            overlaps = slot['start'] < mukha_e and slot['end'] > mukha_s
            assert not overlaps, (
                f"Slot {slot['start'].time()}–{slot['end'].time()} on {target} "
                f"overlaps Bhadra Mukha {mukha_s.time()}–{mukha_e.time()}"
            )

    if not found_mukha_day:
        import pytest
        pytest.skip('No Bhadra Mukha window found in 60-day scan')


def test_bhadra_windows_in_all_mcp_tool_responses():
    """bhadra_mukha and bhadra_puchha must be serialized by all per-day MCP tools."""
    import json

    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    # Pick a Vishti day for meaningful values.
    out1 = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'bhadra_mukha' in out1
    assert 'bhadra_puchha' in out1

    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'bhadra_mukha' in out2
    assert 'bhadra_puchha' in out2

    out3 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'bhadra_mukha' in out3['days'][0]
    assert 'bhadra_puchha' in out3['days'][0]
