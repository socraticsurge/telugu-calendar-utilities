"""Planet rashi ingress calendar.

Returns every sign change (rashi ingress) for the classical planets over a
date range. Each entry records when a planet enters a rashi and when it leaves
(next ingress), making it easy to see gochara period boundaries.

Includes retrograde ingresses — Mercury and Venus can enter a sign, station,
and retreat to the previous sign before re-entering. All transitions appear.

Sidereal coordinates (ayanamsa-configurable, Lahiri by default).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import swisseph as swe

from telugu_panchangam.engines.base import RASHI_NAMES
from telugu_panchangam.engines.utils import AYANAMSA_MODES, jd_to_utc

INGRESS_PLANETS: list[str] = [
    'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu',
]

_SWE_BODY: dict[str, int] = {
    'Sun':     swe.SUN,
    'Mercury': swe.MERCURY,
    'Venus':   swe.VENUS,
    'Mars':    swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn':  swe.SATURN,
    'Rahu':    swe.MEAN_NODE,
    'Ketu':    swe.MEAN_NODE,   # Ketu = Rahu + 180°
}

_MAX_INGRESS_DAYS: float = 1200.0   # Saturn can sit ~900 days in one sign


@dataclass
class RashiIngress:
    planet: str
    enters: datetime       # UTC: moment the planet crosses into this rashi
    rashi: str             # the rashi being entered
    exits: datetime | None # UTC: next sign change; None if > _MAX_INGRESS_DAYS away


# ── Internal helpers ──────────────────────────────────────────────────────────

def _date_to_jd(d: date) -> float:
    return swe.julday(d.year, d.month, d.day, 0.0)


def _sidereal_lon_speed(jd: float, planet: str) -> tuple[float, float]:
    """Sidereal longitude and daily speed (sid mode must be pre-set by caller)."""
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    r, _ = swe.calc_ut(jd, _SWE_BODY[planet], flags)
    lon = (r[0] + 180.0) % 360.0 if planet == 'Ketu' else r[0] % 360.0
    return lon, r[3]


def _rasi_idx(lon: float) -> int:
    return int(lon / 30.0) % 12


def _find_next_ingress(
    jd_from: float,
    planet: str,
    max_days: float = _MAX_INGRESS_DAYS,
) -> tuple[float, int] | None:
    """Return (jd, rashi_idx) of the next sign change after jd_from, or None."""
    start_idx = _rasi_idx(_sidereal_lon_speed(jd_from, planet)[0])
    t = jd_from
    end = jd_from + max_days
    while t < end:
        lon, speed = _sidereal_lon_speed(t, planet)
        deg_in_sign = lon % 30.0
        dist = max(min(deg_in_sign, 30.0 - deg_in_sign), 0.01)
        step = max(0.02, min(15.0, 0.4 * dist / max(abs(speed), 0.01)))
        t2 = t + step
        if _rasi_idx(_sidereal_lon_speed(t2, planet)[0]) != start_idx:
            lo, hi = t, t2
            for _ in range(44):
                mid = (lo + hi) / 2.0
                if _rasi_idx(_sidereal_lon_speed(mid, planet)[0]) != start_idx:
                    hi = mid
                else:
                    lo = mid
            return hi, _rasi_idx(_sidereal_lon_speed(hi, planet)[0])
        t = t2
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def rashi_ingresses(
    start: date,
    end: date,
    planets: list[str] | None = None,
    ayanamsa: str = 'lahiri',
) -> list[RashiIngress]:
    """Return all rashi ingress events within [start, end].

    Parameters
    ----------
    start, end : date
        Inclusive date range.
    planets : list[str] | None
        Subset of INGRESS_PLANETS; defaults to all eight.
    ayanamsa : str
        One of 'lahiri' (default), 'raman', 'krishnamurti', 'true_chitrapaksha'.

    Returns
    -------
    List of RashiIngress sorted by entry time.  Retrograde ingresses (a planet
    re-entering a sign it recently left) are included — caller can check the
    graha_positions retrograde flag for context.  ``exits`` is the next sign
    change for the planet (may fall outside the requested range); it is None
    if no further ingress is found within ``_MAX_INGRESS_DAYS``.
    """
    if planets is None:
        planets = INGRESS_PLANETS
    else:
        bad = [p for p in planets if p not in set(INGRESS_PLANETS)]
        if bad:
            raise ValueError(f'Unknown planet(s): {bad}. Valid: {INGRESS_PLANETS}')

    jd_start = _date_to_jd(start)
    jd_end   = _date_to_jd(end) + 1.0

    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    try:
        results: list[RashiIngress] = []

        for planet in planets:
            # Start the scan from jd_start to find all ingresses within range.
            jd = jd_start
            while True:
                result = _find_next_ingress(jd, planet)
                if result is None:
                    break
                jd_ingress, rashi_idx = result
                if jd_ingress > jd_end:
                    break
                # Find when this rashi period ends (the following ingress).
                exit_result = _find_next_ingress(jd_ingress + 0.01, planet)
                jd_exit = exit_result[0] if exit_result else None
                results.append(RashiIngress(
                    planet=planet,
                    enters=jd_to_utc(jd_ingress),
                    rashi=RASHI_NAMES[rashi_idx],
                    exits=jd_to_utc(jd_exit) if jd_exit else None,
                ))
                jd = jd_ingress + 0.01  # just past this ingress to find the next
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    results.sort(key=lambda r: r.enters)
    return results
