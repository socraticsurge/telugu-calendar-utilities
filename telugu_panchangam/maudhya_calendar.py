"""All-planet Asta/Udaya (combustion) calendar.

Computes heliacal setting (Asta) and rising (Udaya) for the five classical
planets — Mercury, Venus, Mars, Jupiter, Saturn — over a date range for a
given city.  These mark when a planet becomes invisible due to proximity to
the Sun (Asta) and when it re-emerges (Udaya).

Algorithm
---------
Uses ``swe.heliacal_ut()`` from the Swiss Ephemeris, with per-planet
observer Snellen-ratio parameters calibrated against Drik Panchang reference
dates for major Indian cities (Hyderabad 2026 dataset).  Typical accuracy:
within 1–2 days of Drik Panchang for Saturn, Jupiter, and Venus; within
1–5 days for Mars and Mercury.

Terminology
-----------
This function computes *heliacal* Asta/Udaya (sky-visibility criterion),
which is what Drik Panchang publishes.  Classical texts such as BPHS also
define fixed-elongation Maudhya thresholds; these are used by the Drik
engine's per-day combustion flag (``GrahaState.combust``), not here.

Location dependency
-------------------
Heliacal visibility depends on the observer's geographic position, so a
``Location`` (city) is required.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import swisseph as swe

from telugu_panchangam.engines.utils import jd_to_utc
from telugu_panchangam.models.panchangam_day import Location

# ── Planet catalogue ──────────────────────────────────────────────────────────

PLANET_NAMES: list[str] = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']

_OUTER = frozenset({'Mars', 'Jupiter', 'Saturn'})
_INNER = frozenset({'Mercury', 'Venus'})

# Approximate synodic periods in days (used for look-back window).
_SYNODIC: dict[str, int] = {
    'Mercury': 116,
    'Venus':   584,
    'Mars':    780,
    'Jupiter': 399,
    'Saturn':  378,
}

# Observer Snellen ratios per (planet, event-type), calibrated to Drik Panchang.
# Values > 1 = more acute than average; < 1 = below-average.
# Calibrated from 2026 Hyderabad reference dates; accuracy ≈ 1–2 days.
_SNELLEN: dict[str, dict[int, float]] = {
    'Saturn':  {
        swe.HELIACAL_SETTING: 5.0,   # 26 min from DP
        swe.HELIACAL_RISING:  1.0,   # 24 min from DP
        swe.MORNING_LAST:     5.0,
        swe.EVENING_FIRST:    1.0,
    },
    'Jupiter': {
        swe.HELIACAL_SETTING: 3.0,   # 47 min from DP
        swe.HELIACAL_RISING:  3.0,   # 23 h from DP (same day)
        swe.MORNING_LAST:     3.0,
        swe.EVENING_FIRST:    3.0,
    },
    'Mars': {
        swe.HELIACAL_SETTING: 5.0,
        swe.HELIACAL_RISING:  0.9,   # ~24 h from DP
        swe.MORNING_LAST:     5.0,
        swe.EVENING_FIRST:    0.9,
    },
    'Mercury': {
        swe.HELIACAL_SETTING: 3.0,
        swe.HELIACAL_RISING:  3.0,
        swe.MORNING_LAST:     3.0,
        swe.EVENING_FIRST:    3.0,
    },
    'Venus': {
        swe.HELIACAL_SETTING: 3.0,
        swe.HELIACAL_RISING:  3.0,
        swe.MORNING_LAST:     3.0,
        swe.EVENING_FIRST:    3.0,   # 7 min from DP
    },
}

_STD_ATMO: list[float] = [1013.25, 15.0, 40.0, 0.0]


# ── Output type ───────────────────────────────────────────────────────────────

@dataclass
class CombustionPeriod:
    planet: str
    enters: datetime          # UTC: planet becomes invisible (Asta)
    exits:  datetime | None   # UTC: planet re-emerges (Udaya); None = ongoing at range end


# ── Internal helpers ──────────────────────────────────────────────────────────

def _date_to_jd(d: date) -> float:
    return swe.julday(d.year, d.month, d.day, 0.0)


def _next_event(
    planet: str,
    jd_from: float,
    evt_type: int,
    geopos: list[float],
) -> float | None:
    snellen = _SNELLEN[planet][evt_type]
    observer = [36.0, snellen, 0.0, 0.0, 0.0, 0.0]
    try:
        result = swe.heliacal_ut(
            jd_from, geopos, _STD_ATMO, observer, planet, evt_type, swe.FLG_SWIEPH,
        )
        return float(result[0])
    except swe.Error:
        return None


def _outer_periods(
    planet: str,
    jd_from: float,
    jd_to: float,
    geopos: list[float],
) -> list[tuple[float, float | None]]:
    """Asta→Udaya pairs for one outer planet (one conjunction type)."""
    pairs: list[tuple[float, float | None]] = []
    jd_entry = _next_event(planet, jd_from, swe.HELIACAL_SETTING, geopos)
    while jd_entry is not None and jd_entry <= jd_to:
        jd_exit = _next_event(planet, jd_entry, swe.HELIACAL_RISING, geopos)
        pairs.append((jd_entry, jd_exit))
        next_from = (jd_exit if jd_exit else jd_entry) + 1.0
        jd_entry = _next_event(planet, next_from, swe.HELIACAL_SETTING, geopos)
    return pairs


def _inner_periods(
    planet: str,
    jd_from: float,
    jd_to: float,
    geopos: list[float],
) -> list[tuple[float, float | None]]:
    """Asta→Udaya pairs for one inner planet (both conjunction types)."""
    synodic_half = float(_SYNODIC[planet]) / 2.0
    pairs: list[tuple[float, float | None]] = []

    for entry_evt, exit_evt in (
        (swe.MORNING_LAST,     swe.EVENING_FIRST),   # around superior conjunction
        (swe.HELIACAL_SETTING, swe.HELIACAL_RISING),  # around inferior conjunction
    ):
        jd_entry = _next_event(planet, jd_from, entry_evt, geopos)
        while jd_entry is not None and jd_entry <= jd_to:
            jd_exit = _next_event(planet, jd_entry, exit_evt, geopos)
            pairs.append((jd_entry, jd_exit))
            next_from = (jd_exit if jd_exit else jd_entry) + synodic_half
            jd_entry = _next_event(planet, next_from, entry_evt, geopos)

    return pairs


# ── Public API ────────────────────────────────────────────────────────────────

def combustion_periods(
    start: date,
    end: date,
    city: Location,
    planets: list[str] | None = None,
) -> list[CombustionPeriod]:
    """Return Asta/Udaya periods within [start, end] for the given city.

    Parameters
    ----------
    start, end:
        Inclusive date range.
    city:
        Observer location (required — heliacal dates are location-dependent).
    planets:
        Subset of PLANET_NAMES; defaults to all five.

    Returns
    -------
    List of CombustionPeriod sorted by entry time.  If a planet enters Asta
    before *start* and exits within the range, ``enters`` will be before
    *start*.  If still Asta at *end*, ``exits`` is None.
    """
    if planets is None:
        planets = PLANET_NAMES
    else:
        bad = [p for p in planets if p not in set(PLANET_NAMES)]
        if bad:
            raise ValueError(f'Unknown planet(s): {bad}. Valid: {PLANET_NAMES}')

    geopos = [city.lon, city.lat, city.alt]
    jd_start = _date_to_jd(start)
    jd_end   = _date_to_jd(end) + 1.0

    results: list[CombustionPeriod] = []

    for planet in planets:
        # 120-day lookback: enough to capture any Asta that started before the
        # range but is still ongoing (Mars the extreme case at ~90 days), while
        # avoiding the *previous* synodic period's Asta which would cause the
        # search to chain through an extra iteration and introduce JD drift.
        jd_lookback = jd_start - 120.0

        if planet in _OUTER:
            raw = _outer_periods(planet, jd_lookback, jd_end, geopos)
        else:
            raw = _inner_periods(planet, jd_lookback, jd_end, geopos)

        for jd_entry, jd_exit in raw:
            # Filter: keep only periods overlapping [jd_start, jd_end]
            if jd_exit is not None and jd_exit < jd_start:
                continue   # ended before range
            if jd_entry > jd_end:
                continue   # starts after range

            results.append(CombustionPeriod(
                planet=planet,
                enters=jd_to_utc(jd_entry),
                exits=jd_to_utc(jd_exit) if jd_exit is not None else None,
            ))

    results.sort(key=lambda p: p.enters)
    return results
