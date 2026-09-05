# Sidereal positions of the nine grahas, with rasi, nakshatra,
# retrograde state and next sign ingress. Verified against
# drikpanchang.com sidereal planetary positions.
from datetime import date

import swisseph as swe

from telugu_panchangam.engines.utils import AYANAMSA_MODES
from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES, RASHI_NAMES

GRAHA_NAMES: list[str] = [
    'Surya', 'Chandra', 'Kuja', 'Budha', 'Guru', 'Shukra', 'Shani', 'Rahu', 'Ketu',
]

_GRAHA_BODIES = {
    'Surya': swe.SUN, 'Chandra': swe.MOON, 'Kuja': swe.MARS,
    'Budha': swe.MERCURY, 'Guru': swe.JUPITER, 'Shukra': swe.VENUS,
    'Shani': swe.SATURN, 'Rahu': swe.MEAN_NODE,
}

# Search horizon for the next ingress: Saturn can sit ~3 years in a sign;
# a stationing retrograde can stretch that further.
_MAX_INGRESS_DAYS = 2000.0


def _lon_speed(jd: float, graha: str) -> tuple[float, float]:
    """Sidereal longitude and daily speed (sid mode must be pre-set by caller)."""
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    if graha == 'Ketu':
        result, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags)
        return (result[0] + 180.0) % 360.0, result[3]
    result, _ = swe.calc_ut(jd, _GRAHA_BODIES[graha], flags)
    return result[0] % 360.0, result[3]


def _rasi_idx(lon: float) -> int:
    return int(lon / 30.0) % 12


def _next_ingress(jd: float, graha: str) -> tuple[float, int] | None:
    """JD and rasi index when the graha next changes sign (either direction)."""
    start_idx = _rasi_idx(_lon_speed(jd, graha)[0])
    t = jd
    while t < jd + _MAX_INGRESS_DAYS:
        lon, speed = _lon_speed(t, graha)
        deg_left = min((30.0 - lon % 30.0), lon % 30.0) or 0.01
        step = max(0.02, min(20.0, 0.5 * deg_left / max(abs(speed), 0.01)))
        t2 = t + step
        if _rasi_idx(_lon_speed(t2, graha)[0]) != start_idx:
            lo, hi = t, t2
            for _ in range(40):
                mid = (lo + hi) / 2.0
                if _rasi_idx(_lon_speed(mid, graha)[0]) != start_idx:
                    hi = mid
                else:
                    lo = mid
            return hi, _rasi_idx(_lon_speed(hi, graha)[0])
        t = t2
    return None


def _jd_to_date(jd: float, tz_offset_hours: float = 5.5) -> date:
    y, m, d, _ = swe.revjul(jd + tz_offset_hours / 24.0)
    return date(y, m, d)


def graha_positions(jd: float, ayanamsa: str = 'lahiri') -> list[dict]:
    """All nine grahas at instant `jd` (UT): longitude, rasi, nakshatra,
    pada, retrograde, and the date (IST) the graha enters its next rasi.

    Parameters
    ----------
    jd : float
        Julian Day (UT) at which to evaluate positions (typically sunrise).
    ayanamsa : str
        One of 'lahiri' (default), 'raman', 'krishnamurti', 'true_chitrapaksha'.
    """
    swe.set_sid_mode(AYANAMSA_MODES[ayanamsa])
    try:
        out = []
        for graha in GRAHA_NAMES:
            lon, speed = _lon_speed(jd, graha)
            retro = speed < 0
            ingress = _next_ingress(jd, graha)
            nak_pos = lon / (360.0 / 27.0)
            out.append({
                'graha': graha,
                'longitude': round(lon, 4),
                'rasi': RASHI_NAMES[_rasi_idx(lon)],
                'nakshatra': NAKSHATRA_NAMES[int(nak_pos) % 27],
                'pada': int(nak_pos * 4) % 4 + 1,
                'retrograde': retro,
                'rasi_until': _jd_to_date(ingress[0]).isoformat() if ingress else None,
                'next_rasi': RASHI_NAMES[ingress[1]] if ingress else None,
            })
        return out
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
