# tests/test_ics_generator.py
from datetime import date, datetime, timezone, timedelta
from icalendar import Calendar
from telugu_panchangam.generators.ics import ICSGenerator
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.cities import CITIES
from telugu_panchangam.models.panchangam_day import EclipseInfo

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


def test_eclipse_marker_and_description():
    days = _make_days(1)
    days[0].eclipse = EclipseInfo(
        kind='Lunar', subtype='Total', visible=True,
        start=datetime(2024, 3, 24, 16, 27, tzinfo=timezone.utc),
        end=datetime(2024, 3, 24, 19, 56, tzinfo=timezone.utc),
        sutak_start=datetime(2024, 3, 24, 7, 27, tzinfo=timezone.utc),
        sutak_end=datetime(2024, 3, 24, 19, 56, tzinfo=timezone.utc),
    )
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    summary = str(events[0].get('summary'))
    description = str(events[0].get('description'))
    assert '⚡' in summary
    assert 'Lunar Eclipse (Total)' in description
    assert 'Sutak' in description


def test_eclipse_not_visible_omits_sutak():
    days = _make_days(1)
    days[0].eclipse = EclipseInfo(
        kind='Solar', subtype='Annular', visible=False,
        start=datetime(2024, 3, 24, 9, 56, tzinfo=timezone.utc),
        end=datetime(2024, 3, 24, 14, 27, tzinfo=timezone.utc),
        sutak_start=None, sutak_end=None,
    )
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Solar Eclipse (Annular)' in description
    assert 'not visible' in description
    assert 'Sutak' not in description


def test_special_yogas_in_description():
    days = _make_days(1)
    days[0].special_yogas = ['Sarvartha Siddhi Yoga', 'Dagdha Yoga']
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert '─ Special Yogas ─' in description
    assert '  Sarvartha Siddhi Yoga' in description
    assert '  Dagdha Yoga' in description


def test_no_yogas_section_when_empty():
    days = _make_days(1)
    days[0].special_yogas = []
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Yogas:' not in description


def test_ayanam_and_rituvu_in_description():
    days = _make_days(1)
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Ayanam:' in description
    assert 'Rituvu:' in description
