import json
from datetime import datetime, timedelta, timezone

from telugu_panchangam.ghati import (
    civil_to_ghati,
    ghati_to_civil,
    ghati_window,
    make_clock,
)


def test_make_clock_seconds_per_ghati():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    next_sunrise = sunrise + timedelta(hours=24)
    clk = make_clock(sunrise, next_sunrise)
    assert clk.seconds_per_ghati == 86400 / 60


def test_civil_to_ghati_sunrise_is_zero():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    assert civil_to_ghati(clk, sunrise) == 0.0


def test_civil_to_ghati_one_ghati_after():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    one_ghati_later = sunrise + timedelta(seconds=clk.seconds_per_ghati)
    assert abs(civil_to_ghati(clk, one_ghati_later) - 1.0) < 1e-9


def test_ghati_to_civil_round_trip():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    for g in (0.0, 7.5, 22.0, 59.999):
        t = ghati_to_civil(clk, g)
        assert abs(civil_to_ghati(clk, t) - g) < 1e-9


def test_ghati_window_names_and_bounds():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    w = ghati_window(clk, 'Vishaghati', start_ghati=10.0, end_ghati=12.5)
    assert w.name == 'Vishaghati'
    assert w.start_ghati == 10.0
    assert w.end_ghati == 12.5
    assert abs((w.end - w.start).total_seconds() - 2.5 * clk.seconds_per_ghati) < 1e-6


def test_ghati_clock_in_mcp_output():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'ghati_clock' in out
    gc = out['ghati_clock']
    assert 'sunrise' in gc and 'next_sunrise' in gc and 'seconds_per_ghati' in gc
    assert 1400 < gc['seconds_per_ghati'] < 1500   # ~24-min sanity bound


def test_ghati_clock_in_all_mcp_tool_responses():
    from telugu_panchangam.mcp.tools import (
        tool_get_muhurta,
        tool_get_panchangam,
        tool_get_panchangam_range,
    )
    # tool_get_panchangam — top-level ghati_clock
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'ghati_clock' in out and out['ghati_clock'] is not None

    # tool_get_muhurta — top-level ghati_clock
    out2 = json.loads(tool_get_muhurta('2026-06-11', city='Hyderabad'))
    assert 'ghati_clock' in out2 and out2['ghati_clock'] is not None

    # tool_get_panchangam_range — ghati_clock inside each per-day dict
    out3 = json.loads(tool_get_panchangam_range('2026-06-11', '2026-06-12', city='Hyderabad'))
    assert 'ghati_clock' in out3['days'][0] and out3['days'][0]['ghati_clock'] is not None
