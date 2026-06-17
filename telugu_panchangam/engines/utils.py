from datetime import datetime, timezone
from datetime import date as date_type
import swisseph as swe
import pytz


AYANAMSA_MODES = {
    'lahiri':            swe.SIDM_LAHIRI,
    'raman':             swe.SIDM_RAMAN,
    'krishnamurti':      swe.SIDM_KRISHNAMURTI,
    'true_chitrapaksha': swe.SIDM_TRUE_CITRA,
}


def _validate_ayanamsa(name: str) -> int:
    if name not in AYANAMSA_MODES:
        raise ValueError(
            'ayanamsa must be one of: ' + ', '.join(sorted(AYANAMSA_MODES))
        )
    return AYANAMSA_MODES[name]


def sidereal_longitude_with_ayanamsa(jd: float, planet: int, ayanamsa: str) -> float:
    """Sidereal longitude under the named ayanamsa. The existing
    sidereal_longitude (Lahiri-only) is kept for backward compatibility
    with cached/hot paths.
    """
    mode = _validate_ayanamsa(ayanamsa)
    swe.set_sid_mode(mode)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    result, _ = swe.calc_ut(jd, planet, flags)
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # restore Lahiri so cached Lahiri callers see correct mode
    return result[0] % 360.0


def datetime_to_jd(dt: datetime) -> float:
    """Convert UTC datetime to Julian Day Number."""
    utc = dt.astimezone(timezone.utc)
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    return swe.julday(utc.year, utc.month, utc.day, hour)


def jd_to_utc(jd: float) -> datetime:
    """Convert Julian Day Number to UTC datetime."""
    year, month, day, hour = swe.revjul(jd)
    h = int(hour)
    m = int((hour - h) * 60)
    s = int(((hour - h) * 60 - m) * 60)
    return datetime(int(year), int(month), int(day), h, m, s, tzinfo=timezone.utc)


def local_midnight_jd(d: date_type, tz_str: str) -> float:
    """JD for local midnight (00:00) of date d in given timezone."""
    tz = pytz.timezone(tz_str)
    midnight_local = tz.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    return datetime_to_jd(midnight_local)


def sidereal_longitude(jd: float, planet: int) -> float:
    """Sidereal longitude (Lahiri ayanamsa) for a planet at JD."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    result, _ = swe.calc_ut(jd, planet, flags)
    return result[0] % 360.0


from functools import lru_cache

@lru_cache(maxsize=1024)
def sun_longitude(jd: float) -> float:
    return sidereal_longitude(jd, swe.SUN)


@lru_cache(maxsize=1024)
def moon_longitude(jd: float) -> float:
    return sidereal_longitude(jd, swe.MOON)


@lru_cache(maxsize=1024)
def tropical_sun_longitude(jd: float) -> float:
    """Tropical (sayana) sun longitude — used for season (rituvu) reckoning."""
    result, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    return result[0] % 360.0


@lru_cache(maxsize=1024)
def moon_sun_elongation(jd: float) -> float:
    """Moon - Sun longitude in [0, 360)."""
    return (moon_longitude(jd) - sun_longitude(jd)) % 360.0


def find_crossing(
    func,
    target: float,
    jd_start: float,
    jd_end: float,
    tolerance: float = 1e-8,
) -> float:
    """Binary search: find JD in [jd_start, jd_end] where func(jd) == target (mod 360).
    func must be monotonically increasing (or decreasing) within the interval.
    """
    for _ in range(60):
        if jd_end - jd_start < tolerance:
            break
        jd_mid = (jd_start + jd_end) / 2.0
        val_start = (func(jd_start) - target) % 360.0
        val_mid = (func(jd_mid) - target) % 360.0
        if val_start > 180.0:
            val_start -= 360.0
        if val_mid > 180.0:
            val_mid -= 360.0
        if val_start * val_mid <= 0:
            jd_end = jd_mid
        else:
            jd_start = jd_mid
    return (jd_start + jd_end) / 2.0


def previous_new_moon(elongation_func, jd: float) -> float:
    """JD of the most recent new moon (elongation 0 crossing) at or before jd.

    find_crossing cannot be used directly with a month-wide window: its signed
    difference wraps at target+180° (the full moon), so bisection can converge
    there instead. This iterates with the mean elongation rate, which always
    lands on the nearest crossing behind jd.
    """
    jd_nm = jd - (elongation_func(jd) % 360.0) / 12.19
    for _ in range(10):
        offset = (elongation_func(jd_nm) + 180.0) % 360.0 - 180.0
        jd_nm -= offset / 12.19
    if jd_nm > jd:
        jd_nm -= 29.530589
    return jd_nm


def next_new_moon(elongation_func, jd: float) -> float:
    """JD of the first new moon strictly after jd."""
    return previous_new_moon(elongation_func, previous_new_moon(elongation_func, jd) + 35.0)


def get_sunrise(jd_start: float, geopos: list[float]) -> float:
    """JD of next sunrise after jd_start for geopos=[lon, lat, alt_m]."""
    ret, tret = swe.rise_trans(
        jd_start, swe.SUN, swe.CALC_RISE, geopos, 1013.25, 15.0,
    )
    return tret[0]


def get_sunset(jd_start: float, geopos: list[float]) -> float:
    """JD of next sunset after jd_start."""
    ret, tret = swe.rise_trans(
        jd_start, swe.SUN, swe.CALC_SET, geopos, 1013.25, 15.0,
    )
    return tret[0]


def get_moonrise(jd_start: float, geopos: list[float]) -> float:
    """JD of next moonrise after jd_start."""
    ret, tret = swe.rise_trans(
        jd_start, swe.MOON, swe.CALC_RISE, geopos, 1013.25, 15.0,
    )
    return tret[0]


def get_moonset(jd_start: float, geopos: list[float]) -> float:
    """JD of next moonset after jd_start."""
    ret, tret = swe.rise_trans(
        jd_start, swe.MOON, swe.CALC_SET, geopos, 1013.25, 15.0,
    )
    return tret[0]
