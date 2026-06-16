"""Per-anga ICS variant feeds.

The main `ICSGenerator` (generators/ics.py) emits a dense daily feed —
every PanchangamDay becomes one all-day event with the full panchangam
in its description. Devotees who only care about specific anga events
have asked repeatedly for slim per-anga feeds.

This module provides three filters that compose with `ICSGenerator`:

  - `generate_ekadashi_feed(days, system)`     — Ekadashi days only
  - `generate_festivals_feed(days, system)`    — Festival days only
  - `generate_moon_cycles_feed(days, system)`  — Pournami + Amavasya only

Each filters the input `days` list and emits an ICS through the existing
`ICSGenerator`, so the per-event content matches what subscribers
already see in the dense feed — just filtered to the events they care
about. A future PR may add "slim event" content (festival name + key
times only) if there's demand.

Phase 7, item 4 of docs/tracking/improvement-plan.md.
"""
from __future__ import annotations

from telugu_panchangam.generators.ics import ICSGenerator
from telugu_panchangam.models.panchangam_day import PanchangamDay


def filter_ekadashi_days(days: list[PanchangamDay]) -> list[PanchangamDay]:
    """Days flagged as Ekadashi (Shukla or Krishna), excluding Adhika-month
    duplicates by the engine's existing flag semantics."""
    return [d for d in days if d.is_ekadashi]


def filter_festival_days(days: list[PanchangamDay]) -> list[PanchangamDay]:
    """Days with at least one named festival in `day.festivals`. The
    festival list is populated by `base.py:_festivals` and includes
    annual festivals + monthly Sankashti Chaturthi + Masa Shivaratri."""
    return [d for d in days if d.festivals]


def filter_moon_cycle_days(days: list[PanchangamDay]) -> list[PanchangamDay]:
    """Pournami (full moon) and Amavasya (new moon) days. These are the
    two month-boundary lunar events and the two most-requested filter
    points for moon-cycle observances."""
    return [d for d in days if d.is_pournami or d.is_amavasya]


def generate_ekadashi_feed(days: list[PanchangamDay], system: str) -> bytes:
    """Slim ICS feed containing only Ekadashi days from the input.

    Useful for devotees observing only Ekadashi fasts who don't want
    daily-feed noise in their calendar.
    """
    filtered = filter_ekadashi_days(days)
    if not filtered:
        return _empty_feed(days, system, 'Ekadashi')
    return ICSGenerator().generate(filtered, system, variant_label='Ekadashi')


def generate_festivals_feed(days: list[PanchangamDay], system: str) -> bytes:
    """Slim ICS feed containing only days with named festivals.

    Useful for devotees who want major festivals (Ugadi, Vinayaka
    Chavithi, Deepavali, Maha Shivaratri, …) + monthly observances
    (Sankashti Chaturthi, Masa Shivaratri) without daily noise.
    """
    filtered = filter_festival_days(days)
    if not filtered:
        return _empty_feed(days, system, 'Festivals')
    return ICSGenerator().generate(filtered, system, variant_label='Festivals')


def generate_moon_cycles_feed(days: list[PanchangamDay], system: str) -> bytes:
    """Slim ICS feed containing only Pournami + Amavasya days.

    Useful for devotees tracking the moon cycle for vrats, rituals
    anchored to the full/new moon, or general lunar awareness.
    """
    filtered = filter_moon_cycle_days(days)
    if not filtered:
        return _empty_feed(days, system, 'Moon Cycles')
    return ICSGenerator().generate(filtered, system, variant_label='Moon Cycles')


def _empty_feed(days: list[PanchangamDay], system: str, variant_label: str) -> bytes:
    """A valid empty ICS for the rare case where no days in the input
    match the filter. Preserves calendar metadata so subscribers see a
    clearly-labelled empty calendar rather than a corrupt file.
    """
    from icalendar import Calendar

    from telugu_panchangam.generators.ics import SYSTEM_LABELS

    if not days:
        # We need *some* location/system context for the calendar header;
        # this is only reached if the caller passed an empty list, which
        # is a programmer error worth surfacing.
        raise ValueError(
            f'generate_*_feed called with no input days — cannot derive '
            f'calendar metadata for variant {variant_label!r}'
        )

    cal = Calendar()
    cal.add('prodid', '-//Telugu Panchangam//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname',
            f"AstroChaganti's Panchangam — {days[0].location.name} "
            f"({SYSTEM_LABELS[system]}, {variant_label})")
    cal.add('x-wr-timezone', days[0].location.timezone)
    cal.add('x-wr-caldesc',
            f'Telugu Panchangam — {variant_label} only. No matching days '
            f'in the supplied range.')
    cal.add('refresh-interval;value=duration', 'PT12H')
    cal.add('x-published-ttl', 'PT12H')
    return cal.to_ical()
