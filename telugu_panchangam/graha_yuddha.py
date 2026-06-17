"""Graha Yuddha (planetary war) calendar.

Computes periods when any two of the five tara grahas — Mercury, Venus,
Mars, Jupiter, Saturn — come within 1° of each other in ecliptic longitude.
This is the classical Graha Yuddha criterion per Surya Siddhanta and Brihat
Parashara Hora Shastra. The Sun, Moon, Rahu, and Ketu are exempt by
classical convention.

Victor rule
-----------
The planet with the higher ecliptic latitude (more northerly) at closest
approach is declared the victor; the other is the vanquished. The vanquished
planet loses astrological strength for the duration of the war.

Algorithm
---------
A 0.25-day coarse scan detects when any pair crosses the 1° threshold.
Binary search pinpoints entry and exit to within seconds; ternary search
locates the exact minimum-separation moment. A 120-day lookback ensures
wars that began before the requested start date are still detected correctly.

Location independence
---------------------
Graha Yuddha is a purely geocentric celestial event; no observer city is
needed. The longitude difference between two planets is identical in both
tropical and sidereal frames (ayanamsa cancels in subtraction), so tropical
coordinates are used for efficiency.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from itertools import combinations

import swisseph as swe

from telugu_panchangam.engines.utils import jd_to_utc

YUDDHA_PLANETS: list[str] = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']

_SWE_BODY: dict[str, int] = {
    'Mercury': swe.MERCURY,
    'Venus':   swe.VENUS,
    'Mars':    swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn':  swe.SATURN,
}

THRESHOLD_DEG: float = 1.0   # classical 1° ecliptic longitude criterion
_STEP: float = 0.25          # 6-hour coarse scan (safe for Mercury's max ~2°/day)
_LOOKBACK: float = 120.0     # days; handles Jupiter-Saturn wars (~60-day max)
_LOOKAHEAD: float = 60.0     # days beyond end to detect exits of late-starting wars


@dataclass
class GrahaYuddha:
    planet1: str                  # first combatant (as passed in `planets` order)
    planet2: str                  # second combatant
    winner: str                   # higher ecliptic latitude at exact conjunction
    loser: str
    starts: datetime              # UTC: separation first drops below 1°
    exact: datetime               # UTC: minimum longitudinal separation
    ends: datetime | None         # UTC: separation rises above 1° again; None = ongoing
    min_separation_arcmin: float  # minimum separation at exact (arc-minutes)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _date_to_jd(d: date) -> float:
    return swe.julday(d.year, d.month, d.day, 0.0)


def _separation(jd: float, b1: int, b2: int) -> float:
    """Absolute ecliptic longitude difference in degrees [0, 180]."""
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    r1, _ = swe.calc_ut(jd, b1, flags)
    r2, _ = swe.calc_ut(jd, b2, flags)
    diff = abs(r1[0] - r2[0]) % 360.0
    return min(diff, 360.0 - diff)


def _latitude(jd: float, b: int) -> float:
    """Ecliptic latitude in degrees (positive = north)."""
    r, _ = swe.calc_ut(jd, b, swe.FLG_SWIEPH)
    return r[1]


def _bisect(jd_a: float, jd_b: float, b1: int, b2: int, entering: bool) -> float:
    """Find JD where separation crosses THRESHOLD_DEG.
    entering=True: searching the entry (separation going below threshold).
    """
    for _ in range(44):
        mid = (jd_a + jd_b) / 2.0
        below = _separation(mid, b1, b2) < THRESHOLD_DEG
        if below == entering:
            jd_b = mid
        else:
            jd_a = mid
    return (jd_a + jd_b) / 2.0


def _min_jd(jd_a: float, jd_b: float, b1: int, b2: int) -> float:
    """Ternary search for JD of minimum separation in [jd_a, jd_b]."""
    lo, hi = jd_a, jd_b
    for _ in range(50):
        m1 = lo + (hi - lo) / 3.0
        m2 = hi - (hi - lo) / 3.0
        if _separation(m1, b1, b2) < _separation(m2, b1, b2):
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2.0


def _record(
    p1: str, p2: str, b1: int, b2: int,
    jd_entry: float, jd_exit: float | None,
    jd_scan_end: float,
) -> GrahaYuddha:
    jd_search_end = jd_exit if jd_exit is not None else jd_scan_end
    jd_exact = _min_jd(jd_entry, jd_search_end, b1, b2)
    lat1 = _latitude(jd_exact, b1)
    lat2 = _latitude(jd_exact, b2)
    winner = p1 if lat1 >= lat2 else p2
    loser  = p2 if winner == p1 else p1
    min_sep = round(_separation(jd_exact, b1, b2) * 60.0, 3)
    return GrahaYuddha(
        planet1=p1, planet2=p2,
        winner=winner, loser=loser,
        starts=jd_to_utc(jd_entry),
        exact=jd_to_utc(jd_exact),
        ends=jd_to_utc(jd_exit) if jd_exit is not None else None,
        min_separation_arcmin=min_sep,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def graha_yuddha_periods(
    start: date,
    end: date,
    planets: list[str] | None = None,
) -> list[GrahaYuddha]:
    """Return Graha Yuddha periods overlapping [start, end].

    Parameters
    ----------
    start, end : date
        Inclusive date range.
    planets : list[str] | None
        Subset of YUDDHA_PLANETS to search; defaults to all five
        (producing all 10 planet-pair combinations).

    Returns
    -------
    List of GrahaYuddha sorted by start time.  A war that began before
    *start* but is still active is included (``starts`` precedes *start*).
    ``ends=None`` means the war was still ongoing at the scan horizon
    (*end* + 60 days).
    """
    if planets is None:
        planets = YUDDHA_PLANETS
    else:
        bad = [p for p in planets if p not in set(YUDDHA_PLANETS)]
        if bad:
            raise ValueError(f'Unknown planet(s): {bad}. Valid: {YUDDHA_PLANETS}')

    jd_req_start = _date_to_jd(start)
    jd_req_end   = _date_to_jd(end) + 1.0
    jd_scan_from = jd_req_start - _LOOKBACK
    jd_scan_to   = jd_req_end   + _LOOKAHEAD

    results: list[GrahaYuddha] = []

    for p1, p2 in combinations(planets, 2):
        b1, b2 = _SWE_BODY[p1], _SWE_BODY[p2]

        jd = jd_scan_from
        prev_in = _separation(jd, b1, b2) < THRESHOLD_DEG
        jd_entry: float | None = jd if prev_in else None

        while jd < jd_scan_to:
            jd_next = min(jd + _STEP, jd_scan_to)
            in_war = _separation(jd_next, b1, b2) < THRESHOLD_DEG

            if not prev_in and in_war:
                jd_entry = _bisect(jd, jd_next, b1, b2, entering=True)

            elif prev_in and not in_war:
                if jd_entry is not None:
                    jd_exit = _bisect(jd, jd_next, b1, b2, entering=False)
                    # Include if war overlaps the requested range
                    if jd_exit >= jd_req_start and jd_entry < jd_req_end:
                        results.append(_record(p1, p2, b1, b2, jd_entry, jd_exit, jd_scan_to))
                jd_entry = None

            prev_in = in_war
            jd = jd_next

        # Still in war at scan horizon
        if prev_in and jd_entry is not None and jd_entry < jd_req_end:
            results.append(_record(p1, p2, b1, b2, jd_entry, None, jd_scan_to))

    results.sort(key=lambda w: w.starts)
    return results
