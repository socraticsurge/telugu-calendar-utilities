# tests/test_ics_generator.py
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from icalendar import Calendar

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.generators.ics import ICSGenerator
from telugu_panchangam.models.panchangam_day import EclipseInfo

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()
FIXTURE_DIR = Path(__file__).parent / 'fixtures'

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
    # 2024-03-25 is Pournami — and Holika Dahan, so the festival marker wins
    assert any('⚡' in s or '🪔' in s for s in summaries)


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


# --- Named Ekadashi, night Choghadiya, and (+1) next-day markers ---

def test_named_ekadashi_in_summary_and_specials():
    # 2026-06-11 (Hyderabad) is Krishna Ekadashi of Adhika Jyeshtha → Parama
    day = ENGINE.calculate(date(2026, 6, 11), HYD)
    gen = ICSGenerator()
    raw = gen.generate([day], 'drik')
    cal = Calendar.from_ical(raw)
    event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
    summary = str(event.get('summary'))
    description = str(event.get('description'))
    assert 'Parama Ekadashi' in summary
    assert 'Parama Ekadashi — fasting day' in description
    assert 'Tithi:     Parama Ekadashi' in description


def test_night_choghadiya_section_present_with_next_day():
    days = [ENGINE.calculate(date(2026, 6, 11) + timedelta(days=i), HYD)
            for i in range(2)]
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    first = str(events[0].get('description'))
    last = str(events[1].get('description'))
    assert '─ Night Choghadiya ─' in first
    night = first.split('─ Night Choghadiya ─')[1].split('\n\n')[0]
    blocks = [line for line in night.strip().split('\n') if line.strip()]
    assert len(blocks) == 8
    # 2026-06-11 is a Thursday: night runs Amrit ... Amrit (verified vs Drik Panchang)
    assert blocks[0].endswith('Amrit')
    assert blocks[-1].endswith('Amrit')
    # last day in the feed has no next sunrise — no night section
    assert '─ Night Choghadiya ─' not in last


def test_relative_day_markers_on_anga_times():
    # 2026-06-11 Hyderabad: Nakshatra Revati started the previous day 09:21
    # and ends today 08:16; Yoga Shobhana ends 01:00 the next day;
    # Tithi starts and ends within the day.
    day = ENGINE.calculate(date(2026, 6, 11), HYD)
    gen = ICSGenerator()
    raw = gen.generate([day], 'drik')
    cal = Calendar.from_ical(raw)
    event = [c for c in cal.walk() if c.name == 'VEVENT'][0]
    description = str(event.get('description'))
    nakshatra_line = next(
        line for line in description.split('\n') if line.startswith('Nakshatra:')
    )
    yoga_line = next(
        line for line in description.split('\n') if line.startswith('Yoga:')
    )
    tithi_line = next(
        line for line in description.split('\n') if line.startswith('Tithi:')
    )
    assert '(-1)' in nakshatra_line and '(+1)' not in nakshatra_line
    assert '(+1)' in yoga_line
    assert '(+1)' not in tithi_line and '(-1)' not in tithi_line


# --- Festivals in the feed ---

def _event_for(days, d):
    gen = ICSGenerator()
    cal = Calendar.from_ical(gen.generate(days, 'drik'))
    for ev in cal.walk():
        if ev.name == 'VEVENT' and ev['dtstart'].dt == d:
            return ev
    raise AssertionError(f'no event for {d}')


def test_festival_in_summary_with_diya_prefix():
    # 2026-11-08: Naraka Chaturdashi + Deepavali
    days = [ENGINE.calculate(date(2026, 11, 8), HYD, include_eclipse=False)]
    ev = _event_for(days, date(2026, 11, 8))
    summary = str(ev['summary'])
    assert summary.startswith('🪔')
    assert 'Deepavali' in summary


def test_festival_in_description_specials():
    days = [ENGINE.calculate(date(2026, 10, 20), HYD, include_eclipse=False)]
    ev = _event_for(days, date(2026, 10, 20))
    assert 'Vijayadashami (Dasara)' in str(ev['description'])


def test_ganda_moola_noted_in_description():
    # 2026-06-11: Revati nakshatra at sunrise (Ganda Moola)
    days = [ENGINE.calculate(date(2026, 6, 11), HYD, include_eclipse=False)]
    ev = _event_for(days, date(2026, 6, 11))
    assert 'Ganda Moola' in str(ev['description'])


def test_feed_declares_refresh_interval():
    raw = ICSGenerator().generate(_make_days(1), 'drik').decode()
    assert 'REFRESH-INTERVAL;VALUE=DURATION:PT12H' in raw
    assert 'X-PUBLISHED-TTL:PT12H' in raw


def test_feed_name_uses_astrochaganti_branding():
    raw = ICSGenerator().generate(_make_days(1), 'drik').decode()
    assert "AstroChaganti's Panchangam — Hyderabad (Drik Ganita)" in raw.replace('\r\n ', '')


def test_monthly_sankramanam_named_not_bare_sankranti():
    days = [ENGINE.calculate(date(2026, 6, 15), HYD, include_eclipse=False)]
    ev = _event_for(days, date(2026, 6, 15))
    desc = str(ev['description'])
    assert 'Mithuna Sankramanam' in desc
    assert '⚡ Sankranti' not in desc

def test_monthly_sankramanam_is_not_a_special_day_title():
    # 2026-07-17: Karka sankramanam (entry after sunset Jul 16), nothing else
    days = [ENGINE.calculate(date(2026, 7, 17), HYD, include_eclipse=False)]
    ev = _event_for(days, date(2026, 7, 17))
    assert '⚡' not in str(ev['summary'])
    assert 'Karka Sankramanam' in str(ev['description'])


# --- Golden-snapshot regression (Phase 7 PR 3) ---
#
# Subscribers' calendar clients (Apple, Google Calendar, Outlook) lock onto
# specific iCal properties — UID stability, DTSTART/DTEND VALUE=DATE shape,
# X-WR-CALNAME spelling, REFRESH-INTERVAL, X-PUBLISHED-TTL, the SUMMARY
# prefix conventions (⚡ Ekadashi, 🪔 festival, etc.), and the DESCRIPTION
# block layout. The existing substring tests above pin individual fields
# in isolation — they cannot catch reordering, whitespace shifts, or a
# silent format drift that touches multiple fields at once.
#
# This snapshot test guards against that whole class. The golden fixture
# (tests/fixtures/golden_hyderabad_drik_2026-06-11_3d.ics) is the exact
# bytes the generator emits for the 3-day stretch 2026-06-11..2026-06-13
# in Hyderabad with the Drik engine, captured on master at the time of
# Phase 7 PR 3 (commit before this test landed). ICSGenerator emits no
# generation-time timestamps — no DTSTAMP, no PRODID-version — so the
# output is byte-deterministic across runs (sanity-checked at fixture
# creation).
#
# When this test fails:
#   1. Diff the regenerated bytes against the fixture to see what shifted.
#   2. If the shift is intentional (new property, copy edit), regenerate
#      the fixture and reference the rationale in the PR body.
#   3. If the shift is a regression, find the engine/generator change
#      that caused it.


def test_ics_golden_snapshot_2026_06_11_hyderabad_drik_3day():
    """Byte-stable subscriber feed format guard. See module note above
    for the regeneration playbook on intentional drift."""
    days = [ENGINE.calculate(date(2026, 6, 11) + timedelta(days=i), HYD,
                              include_eclipse=False) for i in range(3)]
    actual = ICSGenerator().generate(days, 'drik')
    fixture_path = FIXTURE_DIR / 'golden_hyderabad_drik_2026-06-11_3d.ics'
    expected = fixture_path.read_bytes()
    assert actual == expected, (
        f'ICS output diverged from golden fixture. '
        f'Regenerated {len(actual)} bytes vs fixture {len(expected)} bytes. '
        f'See the module docstring for the regeneration playbook. '
        f'Fixture: {fixture_path}'
    )
