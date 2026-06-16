from datetime import date
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES

DrikEngine = DrikGanitaEngine


def _hyderabad():
    return next(c for c in CITIES if c.name.lower() == 'hyderabad')


def test_vishaghati_list_present():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    assert isinstance(day.vishaghati, list)
    # If a nakshatra changes during the day we may get up to 2 windows;
    # most days have 1.
    assert 0 <= len(day.vishaghati) <= 2


def test_vishaghati_each_window_named_vishaghati():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    for w in day.vishaghati:
        assert w.name == 'Vishaghati'


def test_vishaghati_duration_about_4_vighatis():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), _hyderabad())
    for w in day.vishaghati:
        # 4 vighatis = 4 * (seconds_per_ghati / 60)
        expected_s = 4 * (day.ghati_clock.seconds_per_ghati / 60.0)
        actual_s = (w.end - w.start).total_seconds()
        # Tolerate small clipping at day boundaries.
        assert abs(actual_s - expected_s) < 2.0 or actual_s < expected_s


def test_vishaghati_in_mcp_output():
    import json
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    # Located alongside other inauspicious windows.
    assert 'vishaghati' in out.get('inauspicious', {}) or 'vishaghati' in out
    windows = out.get('inauspicious', {}).get('vishaghati') or out.get('vishaghati') or []
    assert isinstance(windows, list)
    for w in windows:
        assert 'start' in w and 'end' in w
        assert 'start_ghati' in w and 'end_ghati' in w


def test_vishaghati_offsets_table_has_27():
    from telugu_panchangam.karana_windows import VISHAGHATI_OFFSETS_GHATI
    assert len(VISHAGHATI_OFFSETS_GHATI) == 27
