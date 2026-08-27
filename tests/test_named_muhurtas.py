"""Conformance tests for the 30 named muhurtas.

Pins the module to docs/reference/07-muhurta-table.md and — crucially —
cross-checks the proportional day/15 division against the frozen engine:
the 8th daytime muhurta must coincide with the engine's Abhijit Muhurta.
"""
from datetime import date, timedelta

from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES
from telugu_panchangam.muhurtas import (
    named_muhurtas, DAY_MUHURTAS, NIGHT_MUHURTAS,
)

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _day_and_next(y, m, d):
    day = ENGINE.calculate(date(y, m, d), HYD)
    nxt = ENGINE.calculate(date(y, m, d) + timedelta(days=1), HYD)
    return day, nxt


def test_counts_and_tiling():
    day, nxt = _day_and_next(2026, 7, 21)
    ms = named_muhurtas(day, nxt)
    day_ms = [m for m in ms if m['period'] == 'day']
    night_ms = [m for m in ms if m['period'] == 'night']
    assert len(day_ms) == 15 and len(night_ms) == 15

    def close(a, b):  # sub-second: 15*(span/15) != span exactly in float
        return abs((a - b).total_seconds()) < 1

    # Day muhurtas tile sunrise -> sunset with no gaps (contiguity exact).
    assert day_ms[0]['start'] == day.sunrise
    day_ends_at_sunset = close(day_ms[-1]['end'], day.sunset)
    assert day_ends_at_sunset
    for a, b in zip(day_ms, day_ms[1:]):
        assert a['end'] == b['start']

    # Night muhurtas tile sunset -> next sunrise.
    assert night_ms[0]['start'] == day.sunset
    night_ends_at_sunrise = close(night_ms[-1]['end'], nxt.sunrise)
    assert night_ends_at_sunrise
    for a, b in zip(night_ms, night_ms[1:]):
        assert a['end'] == b['start']


def test_day_only_when_no_next_day():
    day, _ = _day_and_next(2026, 7, 21)
    assert len(named_muhurtas(day)) == 15


def test_equal_length_within_each_period():
    day, nxt = _day_and_next(2026, 6, 25)
    ms = named_muhurtas(day, nxt)
    day_lens = {(m['end'] - m['start']) for m in ms if m['period'] == 'day'}
    night_lens = {(m['end'] - m['start']) for m in ms if m['period'] == 'night'}
    assert len(day_lens) == 1   # all daytime muhurtas equal
    assert len(night_lens) == 1


def test_eighth_daytime_muhurta_is_engine_abhijit():
    """The strongest cross-check: proportional day/15 must reproduce the
    engine's Abhijit exactly (both are midday-centred, width day/15)."""
    for y, m, d in [(2026, 7, 21), (2026, 6, 25), (2026, 1, 14), (2026, 12, 5)]:
        day, nxt = _day_and_next(y, m, d)
        if day.date.weekday() == 2:   # Python Wed; engine gives no Abhijit
            continue
        ms = named_muhurtas(day, nxt)
        eighth = next(m for m in ms if m['period'] == 'day' and m['index'] == 8)
        assert eighth['is_abhijit']
        assert day.abhijit_muhurta is not None
        # allow sub-second float slack
        assert abs((eighth['start'] - day.abhijit_muhurta.start).total_seconds()) < 1
        assert abs((eighth['end'] - day.abhijit_muhurta.end).total_seconds()) < 1


def test_no_abhijit_on_wednesday():
    """Wednesday has no Abhijit — the 8th daytime muhurta is ordinary,
    matching the engine (which returns no Abhijit window that day)."""
    from datetime import timedelta as _td
    d = date(2026, 7, 22)  # Wednesday
    assert d.weekday() == 2
    day = ENGINE.calculate(d, HYD)
    assert day.abhijit_muhurta is None
    eighth = next(m for m in named_muhurtas(day) if m['index'] == 8)
    assert eighth['is_abhijit'] is False


def test_brahma_is_fourteenth_night():
    day, nxt = _day_and_next(2026, 7, 21)
    ms = named_muhurtas(day, nxt)
    b = next(m for m in ms if m['period'] == 'night' and m['index'] == 14)
    assert b['is_brahma'] and b['name'] == 'Brahma' and b['nature'] == 'auspicious'


def test_natures_match_reference_table():
    # Day: inauspicious at 1,2,4,10,11,12,15 (7); rest auspicious (8).
    day_inausp = {i + 1 for i, (_, _, nat) in enumerate(DAY_MUHURTAS)
                  if nat == 'inauspicious'}
    assert day_inausp == {1, 2, 4, 10, 11, 12, 15}
    # Night: inauspicious at 1,2,6,7 (4); rest auspicious (11).
    night_inausp = {i + 1 for i, (_, _, nat) in enumerate(NIGHT_MUHURTAS)
                    if nat == 'inauspicious'}
    assert night_inausp == {1, 2, 6, 7}
    # Chanda (night 9) is auspicious, ruled by Moon (owner ruling).
    assert NIGHT_MUHURTAS[8] == ('Chanda', 'Chandra (Moon)', 'auspicious')
