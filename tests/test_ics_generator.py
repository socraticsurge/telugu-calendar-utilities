# tests/test_ics_generator.py
from datetime import date, datetime, timezone
from icalendar import Calendar
from telugu_panchangam.generators.ics import ICSGenerator
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()

def _make_days(n=3):
    from datetime import timedelta
    d = date(2024, 3, 24)
    return [ENGINE.calculate(d + timedelta(days=i), HYD) for i in range(n)]

def test_generate_returns_bytes():
    days = _make_days()
    gen = ICSGenerator()
    result = gen.generate(days, 'drik')
    assert isinstance(result, bytes)

def test_output_is_valid_ical():
    days = _make_days()
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    assert cal is not None

def test_event_count_equals_days():
    days = _make_days(3)
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert len(events) == 3

def test_special_day_has_bolt_prefix():
    days = _make_days(3)
    # 2024-03-25 is Pournami
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    summaries = [str(e.get('summary')) for e in events]
    assert any('⚡' in s for s in summaries)
