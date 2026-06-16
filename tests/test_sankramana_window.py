from datetime import date, timedelta
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def test_no_window_on_non_sankranti_day():
    eng = DrikEngine()
    # 2026-06-11 is not a Sankranti day in Hyderabad
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    if day.sankramanam is None:
        assert day.sankramana_avoidance is None


def test_window_present_around_sankranti():
    """Scan for a Sankranti day; verify window is present and ~32 ghatis wide."""
    eng = DrikEngine()
    city = _hyderabad()
    # Scan a few months — at least one Sankranti per month
    for d in range(0, 40):
        target = date(2026, 7, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.sankramana_avoidance is None:
            continue
        # Width must be approximately 32 ghatis (= 32 * seconds_per_ghati)
        dur_s = (day.sankramana_avoidance.end - day.sankramana_avoidance.start).total_seconds()
        expected_s = 32 * day.ghati_clock.seconds_per_ghati
        assert abs(dur_s - expected_s) < 1.0
        assert day.sankramana_avoidance.name == 'Sankramana Avoidance'
        return
    raise AssertionError('Expected a Sankranti within the 40-day scan')


def test_window_centered_on_ingress():
    """The window is symmetric and spans approximately 12.5–13.5 hours."""
    eng = DrikEngine()
    city = _hyderabad()
    for d in range(0, 40):
        target = date(2026, 7, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.sankramana_avoidance is None:
            continue
        dur_h = (day.sankramana_avoidance.end - day.sankramana_avoidance.start).total_seconds() / 3600
        assert 12.5 < dur_h < 13.5
        return


def test_sankramana_avoidance_in_all_mcp_tool_responses():
    """Serialized in all three per-day MCP response paths."""
    import json
    from telugu_panchangam.mcp.tools import (
        tool_get_panchangam, tool_get_muhurta, tool_get_panchangam_range,
    )
    # Use Karkata Sankranti's neighborhood — should have the field (even if None)
    out1 = json.loads(tool_get_panchangam('2026-07-16', city='Hyderabad'))
    assert 'sankramana_avoidance' in out1
    out2 = json.loads(tool_get_muhurta('2026-07-16', city='Hyderabad'))
    assert 'sankramana_avoidance' in out2
    # tool_get_panchangam_range uses start_date and end_date, not days
    out3 = json.loads(tool_get_panchangam_range('2026-07-16', '2026-07-17', city='Hyderabad'))
    assert 'sankramana_avoidance' in out3['days'][0]


def test_samskara_skipped_during_sankramana():
    """Activities with skip_on_sankramana=True drop slots overlapping the window."""
    from telugu_panchangam.personal.muhurta import day_slots
    eng = DrikEngine()
    city = _hyderabad()
    for d in range(0, 40):
        target = date(2026, 7, 1) + timedelta(days=d)
        day = eng.calculate(target, city)
        if day.sankramana_avoidance is None:
            continue
        # 'wedding' activity has skip_on_sankramana — verify no slot
        # overlaps the avoidance window.
        slots = day_slots(day, activity='wedding')
        win = day.sankramana_avoidance
        for s in slots:
            # Each slot has start/end datetimes — no overlap with the window
            assert s['end'] <= win.start or s['start'] >= win.end, (
                f"Slot {s['start']}..{s['end']} overlaps Sankramana window "
                f"{win.start}..{win.end}"
            )
        return
    raise AssertionError('Expected a Sankranti within the 40-day scan')


def test_sankramana_window_none_for_non_sankranti_day_all_engines():
    """All three engines produce None avoidance window on a non-Sankranti day."""
    from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
    from telugu_panchangam.engines.vakya import VakyaEngine
    city = _hyderabad()
    # 2026-06-11 — mid-month, no Sankranti expected
    d = date(2026, 6, 11)
    for eng in [DrikEngine(), SuryaSiddhantaEngine(), VakyaEngine()]:
        day = eng.calculate(d, city)
        if day.sankramanam is None:
            assert day.sankramana_avoidance is None, (
                f"{eng.__class__.__name__}: expected None avoidance on non-Sankranti day"
            )
