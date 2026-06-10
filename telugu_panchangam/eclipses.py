from datetime import date, timedelta
import swisseph as swe

from telugu_panchangam.engines.utils import jd_to_utc, local_midnight_jd
from telugu_panchangam.models.panchangam_day import EclipseInfo, Location

_SOLAR_SUBTYPE_BITS = [
    (swe.ECL_TOTAL, 'Total'),
    (swe.ECL_ANNULAR_TOTAL, 'Annular'),
    (swe.ECL_ANNULAR, 'Annular'),
    (swe.ECL_PARTIAL, 'Partial'),
]

_LUNAR_SUBTYPE_BITS = [
    (swe.ECL_TOTAL, 'Total'),
    (swe.ECL_PARTIAL, 'Partial'),
    (swe.ECL_PENUMBRAL, 'Penumbral'),
]

_SUTAK_HOURS = {'Solar': 12.0, 'Lunar': 9.0}


def _subtype(retflag: int, bits: list[tuple[int, str]]) -> str:
    for bit, name in bits:
        if retflag & bit:
            return name
    return 'Partial'


def _solar_eclipse(jd_midnight: float, geopos: list[float]) -> dict | None:
    try:
        retflag, tret = swe.sol_eclipse_when_glob(jd_midnight, swe.FLG_SWIEPH, 0, False)
    except Exception:
        return None
    if retflag == 0:
        return None
    how_flag, _attr = swe.sol_eclipse_how(tret[0], geopos, swe.FLG_SWIEPH)
    return {
        'kind': 'Solar',
        'subtype': _subtype(retflag, _SOLAR_SUBTYPE_BITS),
        'visible': how_flag != 0,
        'jd_max': tret[0],
        'jd_start': tret[2],
        'jd_end': tret[3],
    }


def _lunar_eclipse(jd_midnight: float, geopos: list[float]) -> dict | None:
    try:
        retflag, tret = swe.lun_eclipse_when(jd_midnight, swe.FLG_SWIEPH, 0, False)
    except Exception:
        return None
    if retflag == 0:
        return None
    _how_flag, attr = swe.lun_eclipse_how(tret[0], geopos, swe.FLG_SWIEPH)
    jd_start, jd_end = (tret[2], tret[3]) if tret[2] else (tret[6], tret[7])
    return {
        'kind': 'Lunar',
        'subtype': _subtype(retflag, _LUNAR_SUBTYPE_BITS),
        'visible': attr[6] > 0,
        'jd_max': tret[0],
        'jd_start': jd_start,
        'jd_end': jd_end,
    }


def list_eclipses_in_range(jd_start: float, jd_end: float) -> list[dict]:
    """Return all solar and lunar eclipses whose maximum falls within [jd_start, jd_end].
    Each dict has: kind, subtype, jd_max, jd_start, jd_end.
    Does NOT compute per-location visibility — that is done in get_eclipse_from_precomputed."""
    eclipses: list[dict] = []

    jd = jd_start
    while True:
        try:
            retflag, tret = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
        except Exception:
            break
        if retflag == 0 or tret[0] > jd_end:
            break
        if tret[0] >= jd_start:
            eclipses.append({
                'kind': 'Solar',
                'subtype': _subtype(retflag, _SOLAR_SUBTYPE_BITS),
                'jd_max': tret[0],
                'jd_start': tret[2],
                'jd_end': tret[3],
            })
        jd = tret[0] + 1.0

    jd = jd_start
    while True:
        try:
            retflag, tret = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0, False)
        except Exception:
            break
        if retflag == 0 or tret[0] > jd_end:
            break
        jd_s, jd_e = (tret[2], tret[3]) if tret[2] else (tret[6], tret[7])
        if tret[0] >= jd_start:
            eclipses.append({
                'kind': 'Lunar',
                'subtype': _subtype(retflag, _LUNAR_SUBTYPE_BITS),
                'jd_max': tret[0],
                'jd_start': jd_s,
                'jd_end': jd_e,
            })
        jd = tret[0] + 1.0

    return eclipses


def get_eclipse_from_precomputed(
    d: date, precomputed: list[dict], location: Location
) -> 'EclipseInfo | None':
    """Look up whether day `d` has an eclipse from the precomputed list, then compute
    per-location visibility. Equivalent to get_eclipse_for_date() but avoids the global search."""
    geopos = [location.lon, location.lat, 0.0]
    jd_midnight = local_midnight_jd(d, location.timezone)
    jd_next_midnight = local_midnight_jd(d + timedelta(days=1), location.timezone)

    for result in precomputed:
        if not (jd_midnight <= result['jd_max'] < jd_next_midnight):
            continue
        if result['kind'] == 'Solar':
            how_flag, _attr = swe.sol_eclipse_how(result['jd_max'], geopos, swe.FLG_SWIEPH)
            visible = how_flag != 0
        else:
            _how_flag, attr = swe.lun_eclipse_how(result['jd_max'], geopos, swe.FLG_SWIEPH)
            visible = attr[6] > 0

        if visible:
            sutak_hours = _SUTAK_HOURS[result['kind']]
            sutak_start = jd_to_utc(result['jd_start'] - sutak_hours / 24.0)
            sutak_end = jd_to_utc(result['jd_end'])
        else:
            sutak_start = None
            sutak_end = None

        return EclipseInfo(
            kind=result['kind'],
            subtype=result['subtype'],
            visible=visible,
            start=jd_to_utc(result['jd_start']),
            end=jd_to_utc(result['jd_end']),
            sutak_start=sutak_start,
            sutak_end=sutak_end,
        )
    return None


def get_eclipse_for_date(d: date, location: Location) -> EclipseInfo | None:
    """Return eclipse details for the local calendar day `d`, or None if no
    solar or lunar eclipse reaches its maximum during that day."""
    geopos = [location.lon, location.lat, 0.0]
    jd_midnight = local_midnight_jd(d, location.timezone)
    jd_next_midnight = local_midnight_jd(d + timedelta(days=1), location.timezone)

    for finder in (_solar_eclipse, _lunar_eclipse):
        result = finder(jd_midnight, geopos)
        if result is None:
            continue
        if not (jd_midnight <= result['jd_max'] < jd_next_midnight):
            continue

        if result['visible']:
            sutak_hours = _SUTAK_HOURS[result['kind']]
            sutak_start = jd_to_utc(result['jd_start'] - sutak_hours / 24.0)
            sutak_end = jd_to_utc(result['jd_end'])
        else:
            sutak_start = None
            sutak_end = None

        return EclipseInfo(
            kind=result['kind'],
            subtype=result['subtype'],
            visible=result['visible'],
            start=jd_to_utc(result['jd_start']),
            end=jd_to_utc(result['jd_end']),
            sutak_start=sutak_start,
            sutak_end=sutak_end,
        )
    return None
