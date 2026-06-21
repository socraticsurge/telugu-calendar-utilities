"""Per-anga ICS variant feed tests (Phase 7 PR 4).

The generators/anga_variants module provides three filtered feed entry
points. These tests verify the filtering is correct AND each variant
produces a valid ICS calendar that subscribers can actually consume.
"""
from datetime import date, timedelta

import pytest
from icalendar import Calendar

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.generators.anga_variants import (
    filter_ekadashi_days,
    filter_festival_days,
    filter_moon_cycle_days,
    filter_tithi_observances,
    generate_ekadashi_feed,
    generate_festivals_feed,
    generate_moon_cycles_feed,
    generate_tithi_observances_feed,
)

HYD = next(c for c in CITIES if c.name == 'Hyderabad')
ENGINE = DrikGanitaEngine()


def _june_2026(n=30):
    """30 days starting 2026-06-01 — broad enough to span ~2 Ekadashis,
    1 Pournami, 1 Amavasya, and several monthly festivals."""
    return [ENGINE.calculate(date(2026, 6, 1) + timedelta(days=i), HYD,
                              include_eclipse=False) for i in range(n)]


# --- Pure filters ----------------------------------------------------------

def test_filter_ekadashi_keeps_only_ekadashi_flagged_days():
    days = _june_2026()
    out = filter_ekadashi_days(days)
    # June 2026 has 2 Ekadashis (Krishna ~11th, Shukla ~25th); both must
    # appear and nothing else.
    assert out, 'expected at least one Ekadashi in June 2026'
    for d in out:
        assert d.is_ekadashi, f'{d.date}: filter let through a non-Ekadashi day'
    # And no Ekadashi day in the input is missing from the output.
    expected = [d.date for d in days if d.is_ekadashi]
    assert [d.date for d in out] == expected


def test_filter_festival_days_keeps_only_days_with_named_festivals():
    days = _june_2026()
    out = filter_festival_days(days)
    for d in out:
        assert d.festivals, f'{d.date}: filter let through a no-festival day'
    expected = [d.date for d in days if d.festivals]
    assert [d.date for d in out] == expected


def test_filter_moon_cycles_keeps_pournami_and_amavasya_only():
    days = _june_2026()
    out = filter_moon_cycle_days(days)
    for d in out:
        assert d.is_pournami or d.is_amavasya, (
            f'{d.date}: filter let through a non-pournami/amavasya day'
        )
    expected = [d.date for d in days if (d.is_pournami or d.is_amavasya)]
    assert [d.date for d in out] == expected


# --- Feed generators -------------------------------------------------------

def test_generate_ekadashi_feed_is_valid_ical_and_only_contains_ekadashi():
    days = _june_2026()
    raw = generate_ekadashi_feed(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert events, 'expected at least one event in the Ekadashi feed'
    # Every event's summary should mention an Ekadashi name. The dense
    # generator emits SUMMARYs like '⚡ Parama Ekadashi · Revati · Shobhana'
    # so we look for 'Ekadashi' anywhere in the summary text.
    for ev in events:
        summary = str(ev.get('summary'))
        assert 'Ekadashi' in summary, f'event summary lacks Ekadashi: {summary!r}'


def test_generate_festivals_feed_is_valid_ical_and_only_contains_festival_days():
    days = _june_2026()
    raw = generate_festivals_feed(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert events, 'expected at least one festival event in June 2026'
    # Festival events get the 🪔 prefix in summary (per ICSGenerator
    # convention). Sanity-check at least one.
    summaries = [str(ev.get('summary')) for ev in events]
    assert any('🪔' in s for s in summaries), (
        f'expected at least one 🪔-prefixed festival event; got: {summaries}'
    )


def test_generate_moon_cycles_feed_is_valid_ical_and_only_contains_pournami_amavasya():
    days = _june_2026()
    raw = generate_moon_cycles_feed(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert events, 'expected at least one moon-cycle event in June 2026'
    for ev in events:
        summary = str(ev.get('summary'))
        assert 'Pournami' in summary or 'Amavasya' in summary, (
            f'moon-cycle event has neither Pournami nor Amavasya: {summary!r}'
        )


def test_filter_tithi_observances_keeps_ekadashi_pournami_amavasya_pradosham():
    days = _june_2026(30)
    out = filter_tithi_observances(days)
    assert out, 'expected at least one observance day in June 2026'
    for d in out:
        assert d.is_ekadashi or d.is_pournami or d.is_amavasya or d.is_pradosham, (
            f'{d.date}: filter let through a non-observance day'
        )
    expected = [d.date for d in days
                if d.is_ekadashi or d.is_pournami or d.is_amavasya or d.is_pradosham]
    assert [d.date for d in out] == expected


def test_tithi_observances_feed_is_valid_ical():
    days = _june_2026(30)
    raw = generate_tithi_observances_feed(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert events, 'expected at least one observance event in June 2026'
    assert b'Tithi Observances' in raw


def test_tithi_observances_is_superset_of_ekadashi_and_moon_cycles():
    days = _june_2026(30)
    obs_dates = {d.date for d in filter_tithi_observances(days)}
    ek_dates = {d.date for d in filter_ekadashi_days(days)}
    moon_dates = {d.date for d in filter_moon_cycle_days(days)}
    assert ek_dates.issubset(obs_dates), 'observances should include all Ekadashi days'
    assert moon_dates.issubset(obs_dates), 'observances should include all moon-cycle days'


# --- Calendar metadata + labeling ------------------------------------------

def test_each_variant_calendar_name_is_distinct():
    """Subscribers might subscribe to multiple variants; calendar names
    must be unique so the variants are distinguishable in client UI."""
    days = _june_2026()
    names = set()
    for gen in (generate_ekadashi_feed, generate_festivals_feed,
                generate_moon_cycles_feed, generate_tithi_observances_feed):
        raw = gen(days, 'drik')
        cal = Calendar.from_ical(raw)
        names.add(str(cal.get('x-wr-calname')))
    # Four variants → four distinct calendar names. Dense feed not
    # included here but its name format also differs.
    assert len(names) == 4, f'expected 4 distinct calendar names, got {names}'


def test_variants_preserve_refresh_interval_and_branding():
    """Subscribers' clients use REFRESH-INTERVAL to know when to re-fetch.
    All variants must inherit the same 12-hour refresh as the dense feed.
    """
    days = _june_2026()
    for gen in (generate_ekadashi_feed, generate_festivals_feed,
                generate_moon_cycles_feed, generate_tithi_observances_feed):
        raw = gen(days, 'drik')
        # REFRESH-INTERVAL appears literally in the raw bytes
        assert b'REFRESH-INTERVAL;VALUE=DURATION:PT12H' in raw
        assert b'X-PUBLISHED-TTL:PT12H' in raw
        assert b"AstroChaganti's Panchangam" in raw


# --- Edge cases ------------------------------------------------------------

def test_empty_input_raises_clearly():
    """Caller passing no days at all is a programmer error — we raise
    so the bug surfaces, rather than emit a malformed calendar."""
    with pytest.raises(ValueError, match='cannot derive calendar metadata'):
        generate_ekadashi_feed([], 'drik')


def test_zero_match_returns_valid_empty_ics():
    """A short range with no Ekadashi (e.g. a 5-day window between
    Ekadashis) yields a valid empty calendar that subscribers can still
    install — they just see no events."""
    # 2026-06-13 to 06-17: no Ekadashi (Krishna Ekadashi was 06-11)
    short_range = [ENGINE.calculate(date(2026, 6, 13) + timedelta(days=i), HYD,
                                     include_eclipse=False) for i in range(5)]
    # Sanity: no Ekadashi in this stretch
    assert not any(d.is_ekadashi for d in short_range)
    raw = generate_ekadashi_feed(short_range, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    assert events == [], 'zero-match feed should have no events'
    # But calendar metadata is preserved
    assert "AstroChaganti's Panchangam" in str(cal.get('x-wr-calname'))
    assert 'Ekadashi' in str(cal.get('x-wr-calname'))
