import calendar
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from inspect import signature
from typing import Optional

import pytz

from telugu_panchangam.cities import CITIES
from telugu_panchangam.eclipses import (
    get_eclipse_from_precomputed,
    list_eclipses_in_range,
)
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.utils import get_sunrise, jd_to_utc, local_midnight_jd
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.gochara.positions import graha_positions
from telugu_panchangam.gochara.rules import (
    GOCHARA_PROVENANCE,
    gochara_for,
    named_conditions,
)
from telugu_panchangam.graha_yuddha import YUDDHA_PLANETS, graha_yuddha_periods
from telugu_panchangam.ingress import INGRESS_PLANETS, rashi_ingresses
from telugu_panchangam.maudhya_calendar import PLANET_NAMES, combustion_periods
from telugu_panchangam.mcp.calendar_response import (
    format_time as _fmt_time,
)
from telugu_panchangam.mcp.calendar_response import (
    muhurta_details,
    panchangam_details,
    range_day,
    span_to_dict,
)
from telugu_panchangam.mcp.calendar_response import (
    special_events as _special_events,
)
from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates
from telugu_panchangam.mcp.muhurta_request import (
    FindMuhurtaRequest as _FindMuhurtaRequest,
)
from telugu_panchangam.mcp.muhurta_response import muhurta_response
from telugu_panchangam.models.panchangam_day import Location, PanchangamDay
from telugu_panchangam.panchanga_shuddhi import assess_shuddhi
from telugu_panchangam.panchangam_provenance import panchangam_provenance
from telugu_panchangam.personal.chandrabalam import (
    _rasi_index,
    chandra_position,
    chandra_verdict,
)
from telugu_panchangam.personal.lagna_hora import get_horas, get_lagna_transitions
from telugu_panchangam.personal.muhurta import (
    ACTIVITIES,
)
from telugu_panchangam.personal.muhurta_search import search_muhurta
from telugu_panchangam.personal.phalalu import rasi_phalalu
from telugu_panchangam.personal.search_contract import SearchOptions, SearchPeriod
from telugu_panchangam.personal.tarabalam import _nak_index, taras_for_day

_CALCULATION_FAILED_ERROR = (
    'Calculation failed. Please check your inputs and try again.'
)
_DATE_RANGE_LIMIT_ERROR = (
    'Date range exceeds 366-day limit. Use multiple calls for longer spans.'
)
_END_DATE_ORDER_ERROR = 'end_date must be >= start_date.'
_TOOL_CALL_FAILED_LOG = 'tool call failed'

_log = logging.getLogger(__name__)
_MAX_NAME = 80  # max bytes accepted for city/nakshatra/rashi tokens

_ENGINES = {
    'drik': DrikGanitaEngine(),
    'surya_siddhanta': SuryaSiddhantaEngine(),
    'vakya': VakyaEngine(),
}

_ENGINE_CLASSES = {
    'drik': DrikGanitaEngine,
    'surya_siddhanta': SuryaSiddhantaEngine,
    'vakya': VakyaEngine,
}


def _get_engine(system: str, ayanamsa: str = 'lahiri'):
    """Return the cached singleton for Lahiri; instantiate fresh for others."""
    if ayanamsa == 'lahiri':
        return _ENGINES[system]
    return _ENGINE_CLASSES[system](ayanamsa=ayanamsa)


_TIMEZONE_COUNTRY = {
    'Asia/Kolkata': 'India',
    'America/Chicago': 'USA',
    'America/Los_Angeles': 'USA',
    'America/New_York': 'USA',
    'Europe/London': 'UK',
    'Australia/Sydney': 'Australia',
    'Asia/Dubai': 'UAE',
}


def _parse_date(date_str: str) -> date:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date '{date_str}'. Expected YYYY-MM-DD.")


def _validate_system(system: str) -> None:
    if system not in _ENGINES:
        raise ValueError(
            f"Invalid system '{system}'. Must be one of: drik, surya_siddhanta, vakya."
        )


def _resolve_city(
    city: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> Location:
    _validate_city_name(city)
    if latitude is not None and longitude is not None:
        return _coordinate_location(city, latitude, longitude, timezone)
    return _named_location(city)


def _validate_city_name(city) -> None:
    if isinstance(city, str) and len(city) > _MAX_NAME:
        raise ValueError('City name too long.')


def _coordinate_location(city, latitude, longitude, timezone) -> Location:
    if not (-90.0 <= float(latitude) <= 90.0):
        raise ValueError('latitude must be between -90 and 90.')
    if not (-180.0 <= float(longitude) <= 180.0):
        raise ValueError('longitude must be between -180 and 180.')
    if timezone is None:
        timezone = timezone_for_coordinates(float(latitude), float(longitude))
    return Location(
        name=city or 'Custom',
        lat=float(latitude),
        lon=float(longitude),
        timezone=timezone,
    )


def _named_location(city) -> Location:
    lat, lon, tz = resolve_location(city)
    return Location(name=city, lat=lat, lon=lon, timezone=tz)


def _date_interval(start_date, end_date, max_days, limit_error):
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if end < start:
        raise ValueError(_END_DATE_ORDER_ERROR)
    if (end - start).days > max_days:
        raise ValueError(limit_error)
    return start, end


def _validate_planets(planets, valid) -> None:
    if planets is None:
        return
    bad = [planet for planet in planets if planet not in set(valid)]
    if bad:
        raise ValueError(f'Unknown planet(s): {bad}. Valid: {valid}')


def _validate_name(value, kind) -> None:
    if not isinstance(value, str) or len(value) > _MAX_NAME:
        raise ValueError(f'Invalid {kind} name.')


def tool_list_supported_cities() -> str:
    return json.dumps(
        [
            {
                'name': c.name,
                'latitude': c.lat,
                'longitude': c.lon,
                'timezone': c.timezone,
                'country': _TIMEZONE_COUNTRY.get(c.timezone, 'Unknown'),
            }
            for c in CITIES
        ]
    )


@dataclass(frozen=True)
class _DayRequest:
    date_str: str
    city: str
    system: str
    latitude: Optional[float]
    longitude: Optional[float]
    timezone: Optional[str]
    ayanamsa: str = 'lahiri'


def _run_day_tool(request: _DayRequest, project, include_ayanamsa=False) -> str:
    """One validation/calculation/error boundary for daily projections."""
    try:
        d = _parse_date(request.date_str)
        _validate_system(request.system)
        loc = _resolve_city(
            request.city, request.latitude, request.longitude, request.timezone
        )
        day = _get_engine(request.system, request.ayanamsa).calculate(d, loc)
        result = {
            'date': request.date_str,
            'city': request.city,
            'system': request.system,
        }
        if include_ayanamsa:
            result['ayanamsa'] = request.ayanamsa
        result.update(project(day, loc.timezone))
        return json.dumps(result)
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def _daily_panchangam(day, tz):
    return {
        **panchangam_details(day, tz),
        'provenance': panchangam_provenance(day.system),
    }


def _daily_muhurta(day, tz):
    return {**muhurta_details(day, tz), 'provenance': panchangam_provenance(day.system)}


def _daily_horas(day, tz):
    return {'horas': [span_to_dict(window, tz) for window in get_horas(day)]}


def _daily_lagnas(day, tz):
    return {
        'lagnas': [span_to_dict(window, tz) for window in get_lagna_transitions(day)]
    }


def tool_get_panchangam(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    ayanamsa: str = 'lahiri',
) -> str:
    request = _DayRequest(
        date_str, city, system, latitude, longitude, timezone, ayanamsa
    )
    return _run_day_tool(request, _daily_panchangam, include_ayanamsa=True)


def tool_get_muhurta(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    request = _DayRequest(date_str, city, system, latitude, longitude, timezone)
    return _run_day_tool(request, _daily_muhurta)


def tool_get_daily_horas(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    request = _DayRequest(date_str, city, system, latitude, longitude, timezone)
    return _run_day_tool(request, _daily_horas)


def tool_get_lagna_transitions(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    request = _DayRequest(date_str, city, system, latitude, longitude, timezone)
    return _run_day_tool(request, _daily_lagnas)


def tool_get_panchangam_range(
    start_date: str,
    end_date: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    ayanamsa: str = 'lahiri',
) -> str:
    """Return a compact Panchangam summary for each day in [start_date, end_date]. Maximum span: 31 days."""
    try:
        start, end = _date_interval(
            start_date,
            end_date,
            30,
            'Date range exceeds 31-day limit. Use multiple calls for longer spans.',
        )
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _get_engine(system, ayanamsa)
        tz = loc.timezone

        days_count = (end - start).days + 1
        calculated_days = engine.calculate_bulk(start, days_count, loc)

        days = []
        for d, day in zip(
            [start + timedelta(days=i) for i in range(days_count)], calculated_days
        ):
            days.append(range_day(d, day, tz))

        return json.dumps(
            {
                'start_date': start_date,
                'end_date': end_date,
                'city': city,
                'system': system,
                'ayanamsa': ayanamsa,
                'days': days,
                'provenance': panchangam_provenance(system),
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def _is_notable_day(day: PanchangamDay) -> bool:
    return any(
        (
            day.is_ekadashi,
            day.is_amavasya,
            day.is_pournami,
            day.is_pradosham,
            day.is_sankranti,
            day.eclipse is not None,
        )
    )


def _month_eclipses(year: int, month: int, timezone: str):
    start = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return list_eclipses_in_range(
        local_midnight_jd(start, timezone), local_midnight_jd(next_month, timezone)
    )


def tool_get_special_days(
    year: int,
    month: int,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        if not 1 <= month <= 12:
            raise ValueError(f'Invalid month {month}. Must be 1–12.')
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]
        _, days_in_month = calendar.monthrange(year, month)

        precomputed_eclipses = _month_eclipses(year, month, loc.timezone)

        special_days = []
        for day_num in range(1, days_in_month + 1):
            d = date(year, month, day_num)
            day = engine.calculate(d, loc, include_eclipse=False)
            day.eclipse = get_eclipse_from_precomputed(d, precomputed_eclipses, loc)

            if _is_notable_day(day):
                events = _special_events(day)
                special_days.append(
                    {
                        'date': d.isoformat(),
                        'tithi': day.tithi.name,
                        'events': events,
                        'special_yogas': day.special_yogas,
                    }
                )
        return json.dumps(
            {
                'year': year,
                'month': month,
                'city': city,
                'system': system,
                'special_days': special_days,
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def _validate_tarabalam_rashis(
    janma_rasis: Optional[list],
    janma_nakshatras: list,
) -> None:
    if janma_rasis is None:
        return
    if len(janma_rasis) != len(janma_nakshatras):
        raise ValueError(
            'janma_rasis must align with janma_nakshatras '
            '(use null for people whose rashi is unknown).'
        )
    for rashi in janma_rasis:
        if not rashi:
            continue
        _validate_name(rashi, 'rashi')
        _rasi_index(rashi)


def _validate_tarabalam_inputs(
    janma_nakshatras: list,
    janma_rasis: Optional[list],
    days: int,
    chandra_mode: str,
) -> None:
    if chandra_mode not in ('stars', 'puja_ok', 'strict'):
        raise ValueError("chandra_mode must be 'stars', 'puja_ok' or 'strict'.")
    if not 1 <= len(janma_nakshatras) <= 4:
        raise ValueError('Provide 1 to 4 janma nakshatras.')
    if not 1 <= days <= 60:
        raise ValueError('days must be between 1 and 60.')
    for nakshatra in janma_nakshatras:
        _validate_name(nakshatra, 'nakshatra')
        _nak_index(nakshatra)
    _validate_tarabalam_rashis(janma_rasis, janma_nakshatras)


def _tarabalam_is_good(tara: dict, chandra_mode: str) -> bool:
    if not tara['auspicious']:
        return False
    verdict = tara.get('chandra', {}).get('verdict')
    if verdict is None or chandra_mode == 'stars':
        return True
    if chandra_mode == 'puja_ok':
        return verdict != 'bad'
    return verdict == 'good'


def _annotate_chandra(
    taras: list, janma_rasis: Optional[list], lunar_sign: str
) -> None:
    if janma_rasis is None:
        return
    for tara, rasi in zip(taras, janma_rasis):
        if not rasi:
            continue
        position = chandra_position(rasi, lunar_sign)
        tara['chandra'] = {
            'position': position,
            'verdict': chandra_verdict(position),
        }


def tool_find_tarabalam_days(
    janma_nakshatras: list,
    start_date: str,
    days: int = 14,
    city: str = 'Hyderabad',
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    janma_rasis: Optional[list] = None,
    chandra_mode: str = 'stars',
) -> str:
    try:
        _validate_tarabalam_inputs(janma_nakshatras, janma_rasis, days, chandra_mode)
        start = _parse_date(start_date)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]

        out_days = []
        good_dates = []
        calculated_days = engine.calculate_bulk(start, days, loc, include_eclipse=False)
        for i, day in enumerate(calculated_days):
            d = start + timedelta(days=i)
            nak = day.nakshatra.name
            taras = taras_for_day(nak, janma_nakshatras)
            _annotate_chandra(taras, janma_rasis, day.lunar_sign)
            all_good = all(_tarabalam_is_good(tara, chandra_mode) for tara in taras)
            if all_good:
                good_dates.append(d.isoformat())
            out_days.append(
                {
                    'date': d.isoformat(),
                    'vaaram': day.vaaram,
                    'nakshatra': nak,
                    'nakshatra_until': _fmt_time(day.nakshatra.end, loc.timezone),
                    'tithi': day.tithi.name,
                    'taras': taras,
                    'good_for_all': all_good,
                }
            )
        return json.dumps(
            {
                'janma_nakshatras': list(janma_nakshatras),
                'city': city,
                'system': system,
                'tara_convention': 'auspicious: 2 Sampat, 4 Kshema, 6 Sadhana, 8 Mitra, 9 Parama Mitra; '
                'avoid: 1 Janma, 3 Vipat, 5 Pratyak, 7 Naidhana. '
                'Day labelled by the sunrise nakshatra; it changes at nakshatra_until.',
                'chandra_convention': 'when janma_rasis given: positions 1,3,6,7,10,11 good; '
                '2,5,9 workable with remedial puja; 4,8,12 avoid (8 is Ashtama Chandra). '
                f'chandra_mode={chandra_mode}: stars=chandra annotates only, '
                'puja_ok=moon-avoid days dropped, strict=moon must be good.',
                'days': out_days,
                'good_for_all_dates': good_dates,
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_get_graha_positions(
    date_str: str,
    city: str = 'Hyderabad',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    ayanamsa: str = 'lahiri',
) -> str:
    try:
        from telugu_panchangam.engines.utils import _validate_ayanamsa

        _validate_ayanamsa(ayanamsa)
        d = _parse_date(date_str)
        loc = _resolve_city(city, latitude, longitude, timezone)
        geopos = [loc.lon, loc.lat, 0.0]
        jd_sunrise = get_sunrise(local_midnight_jd(d, loc.timezone), geopos)
        return json.dumps(
            {
                'date': date_str,
                'city': city,
                'at': 'sunrise',
                'sunrise': _fmt_time(jd_to_utc(jd_sunrise), loc.timezone),
                'ayanamsa': ayanamsa,
                'grahas': graha_positions(jd_sunrise, ayanamsa),
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_get_gochara(
    date_str: str,
    janma_rasi: str,
    city: str = 'Hyderabad',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    ayanamsa: str = 'lahiri',
) -> str:
    try:
        from telugu_panchangam.engines.utils import _validate_ayanamsa

        _validate_ayanamsa(ayanamsa)
        _rasi_index(janma_rasi)
        d = _parse_date(date_str)
        loc = _resolve_city(city, latitude, longitude, timezone)
        jd_sunrise = get_sunrise(
            local_midnight_jd(d, loc.timezone), [loc.lon, loc.lat, 0.0]
        )
        positions = graha_positions(jd_sunrise, ayanamsa)
        sky = {p['graha']: p['rasi'] for p in positions}
        verdicts = {v['graha']: v for v in gochara_for(janma_rasi, sky)}
        merged = []
        for p in positions:
            v = verdicts[p['graha']]
            merged.append(
                {
                    **p,
                    'position_from_janma_rasi': v['position'],
                    'verdict': v['verdict'],
                    'vedha_by': v['vedha_by'],
                }
            )
        return json.dumps(
            {
                'date': date_str,
                'city': city,
                'janma_rasi': janma_rasi,
                'convention': 'Transit houses are counted from the natal Moon sign. '
                'Brihat Samhita 104.4 supports favourable houses for the '
                'seven classical grahas. Phaladeepika 26.3-8 supports '
                'the Vedha pairs and classical exemptions. The configured '
                'Rahu/Ketu houses (3, 6, 11) conflict with Phaladeepika '
                '26.2, which treats both like Surya and therefore includes '
                'the 10th; node Vedha remains unverified. Phaladeepika '
                '26.1 and 26.22-23 support the Moon-sign reference and '
                'underlying Shani-house effects, not the conventional '
                'condition names, phase labels or advice. '
                'Positions are at sunrise. Gochara is one factor — not a muhurta.',
                'provenance': GOCHARA_PROVENANCE,
                'conditions': named_conditions(janma_rasi, sky),
                'gochara': merged,
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_get_rasi_phalalu(
    date_str: str,
    janma_rasi: str,
    city: str = 'Hyderabad',
    janma_nakshatra: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    ayanamsa: str = 'lahiri',
) -> str:
    try:
        from telugu_panchangam.engines.utils import _validate_ayanamsa

        _validate_ayanamsa(ayanamsa)
        _rasi_index(janma_rasi)
        if janma_nakshatra:
            _nak_index(janma_nakshatra)
        d = _parse_date(date_str)
        loc = _resolve_city(city, latitude, longitude, timezone)
        jd_sunrise = get_sunrise(
            local_midnight_jd(d, loc.timezone), [loc.lon, loc.lat, 0.0]
        )
        positions = graha_positions(jd_sunrise, ayanamsa)
        sky = {p['graha']: p['rasi'] for p in positions}
        day_nak = next(p['nakshatra'] for p in positions if p['graha'] == 'Chandra')
        out = rasi_phalalu(
            janma_rasi,
            sky,
            janma_nakshatra=janma_nakshatra,
            day_nakshatra=day_nak if janma_nakshatra else None,
        )
        out.update(
            {
                'date': date_str,
                'city': city,
                'day_nakshatra': day_nak,
                'disclaimer': 'Every line is rendered from computed gochara/chandrabalam/'
                'tarabalam facts (Brihat Samhita conventions, sunrise positions). '
                'This is a daily reading, not a horoscope consultation or a muhurta.',
            }
        )
        return json.dumps(out)
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def _resolve_city_with_alt(
    city: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> Location:
    """Like _resolve_city but preserves altitude from the CITIES list for heliacal accuracy."""
    _validate_city_name(city)
    if latitude is not None and longitude is not None:
        return _coordinate_location(city, latitude, longitude, timezone)
    known = next((c for c in CITIES if c.name.lower() == (city or '').lower()), None)
    if known:
        return known
    return _named_location(city)


def tool_get_combustion_calendar(
    start_date: str,
    end_date: str,
    city: str = 'Hyderabad',
    planets: Optional[list] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    """Return Asta (combustion entry) and Udaya (emergence) periods for the five classical planets."""
    try:
        start, end = _date_interval(start_date, end_date, 365, _DATE_RANGE_LIMIT_ERROR)
        _validate_planets(planets, PLANET_NAMES)
        loc = _resolve_city_with_alt(city, latitude, longitude, timezone)
        tz_str = loc.timezone

        periods = combustion_periods(start, end, loc, planets=planets)

        def _fmt_dt(dt, tz_s):
            if dt is None:
                return None
            return dt.astimezone(pytz.timezone(tz_s)).strftime('%Y-%m-%d %H:%M')

        return json.dumps(
            {
                'start_date': start_date,
                'end_date': end_date,
                'city': city,
                'timezone': tz_str,
                'note': (
                    'Heliacal Asta (planet becomes invisible near the Sun) and Udaya '
                    '(re-emergence) computed via Swiss Ephemeris sky-visibility criterion. '
                    'This matches the Drik Panchang Asta/Udaya calendar, not the fixed '
                    'BPHS elongation Maudhya thresholds used in per-day combustion flags. '
                    'Accuracy: within 1-2 days of Drik Panchang for most events; '
                    'Mars ±2 days. ongoing=true means the planet is still combust at end_date.'
                ),
                'periods': [
                    {
                        'planet': p.planet,
                        'asta': _fmt_dt(p.enters, tz_str),
                        'udaya': _fmt_dt(p.exits, tz_str) if p.exits else None,
                        'ongoing': p.exits is None,
                    }
                    for p in periods
                ],
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def _validate_nakshatras(values: Optional[list]) -> None:
    if not values:
        return
    if len(values) > 4:
        raise ValueError('Provide at most 4 janma nakshatras.')
    for value in values:
        _validate_name(value, 'nakshatra')
        _nak_index(value)


def _validate_aligned_rashis(
    label: str,
    values: Optional[list],
    janma_nakshatras: Optional[list],
) -> None:
    if values is None:
        return
    unknown_kind = 'lagna' if label == 'janma_lagnas' else 'rashi'
    if not janma_nakshatras or len(values) != len(janma_nakshatras):
        raise ValueError(
            f'{label} must align with janma_nakshatras '
            f'(use null for people whose {unknown_kind} is unknown).'
        )
    kind = 'lagna rashi' if label == 'janma_lagnas' else 'rashi'
    for value in values:
        if value is None:
            continue
        _validate_name(value, kind)
        _rasi_index(value)


def _validate_muhurta_inputs(
    days: int,
    activity: str,
    chandra_mode: str,
    janma_nakshatras: Optional[list],
    janma_rasis: Optional[list],
    janma_lagnas: Optional[list] = None,
) -> None:
    if not 1 <= days <= 14:
        raise ValueError('days must be between 1 and 14.')
    if activity not in ACTIVITIES:
        raise ValueError(f'activity must be one of {ACTIVITIES}.')
    if chandra_mode not in ('stars', 'puja_ok', 'strict'):
        raise ValueError("chandra_mode must be 'stars', 'puja_ok' or 'strict'.")
    _validate_nakshatras(janma_nakshatras)
    _validate_aligned_rashis('janma_rasis', janma_rasis, janma_nakshatras)
    _validate_aligned_rashis('janma_lagnas', janma_lagnas, janma_nakshatras)


def _run_find_muhurta(request: _FindMuhurtaRequest) -> str:
    try:
        _validate_muhurta_inputs(
            request.days,
            request.activity,
            request.chandra_mode,
            request.janma_nakshatras,
            request.janma_rasis,
            request.janma_lagnas,
        )
        start = _parse_date(request.start_date)
        _validate_system(request.system)
        loc = _resolve_city(
            request.city, request.latitude, request.longitude, request.timezone
        )
        engine = _get_engine(request.system, request.ayanamsa)
        options = SearchOptions(
            activity=request.activity,
            janma_nakshatras=request.janma_nakshatras,
            janma_rasis=request.janma_rasis,
            janma_lagnas=request.janma_lagnas,
            chandra_mode=request.chandra_mode,
            travel_direction=request.travel_direction,
            include_night=request.include_night,
        )
        result = search_muhurta(SearchPeriod(start, request.days), loc, engine, options)
        slots = [
            {
                **slot,
                'start': _fmt_time(slot['start'], loc.timezone),
                'end': _fmt_time(slot['end'], loc.timezone),
            }
            for slot in result.slots
        ]
        return muhurta_response(request, slots, result.dropped_days)
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_find_muhurta(*args, **kwargs) -> str:
    """When janma_lagnas[i] is provided, strict Lagna Shuddhi is used
    for that person — kendra/trikona/Ashtama count from the natal
    ascendant. Otherwise we fall back to counting from janma_rasis[i]
    (Chandra-Rashi-as-lagna tradition). Mode is per-person.

    travel_direction: optional cardinal direction ('North', 'South',
    'East', 'West'). When activity='travel' and this is supplied, days
    whose Disha Shoola blocks that direction are excluded entirely.

    include_night: when True, night choghadiya slots (sunset→next sunrise)
    are scored and included alongside daytime slots. Night slots use the
    same panchangam factors (tithi, nakshatra, yoga, tarabalam, chandrabalam)
    but exclude Rahu Kalam / Gulika Kalam / Yamagandam (daytime-only) and
    Abhijit Muhurta. Brahma Muhurta (+2) and Nishita Kala (+2) are added
    as night-specific bonuses.
    """
    return _run_find_muhurta(_FindMuhurtaRequest(*args, **kwargs))


tool_find_muhurta.__signature__ = signature(_FindMuhurtaRequest, eval_str=True).replace(
    return_annotation=str
)


def tool_get_graha_yuddha(
    start_date: str,
    end_date: str,
    planets: Optional[list] = None,
) -> str:
    """Return Graha Yuddha (planetary war) periods in a date range."""
    try:
        start, end = _date_interval(start_date, end_date, 365, _DATE_RANGE_LIMIT_ERROR)
        _validate_planets(planets, YUDDHA_PLANETS)

        wars = graha_yuddha_periods(start, end, planets=planets)

        def _fmt(dt):
            return dt.strftime('%Y-%m-%d %H:%M UTC') if dt else None

        return json.dumps(
            {
                'start_date': start_date,
                'end_date': end_date,
                'threshold': '1° ecliptic longitude',
                'victor_rule': 'higher ecliptic latitude at closest approach',
                'note': (
                    'Graha Yuddha (planetary war) occurs when two of the five tara '
                    'grahas come within 1° of each other in ecliptic longitude. The '
                    'vanquished planet loses astrological strength for the duration. '
                    'Sun, Moon, Rahu, and Ketu are exempt by classical convention. '
                    'ongoing=true means the war extends beyond the scan horizon.'
                ),
                'wars': [
                    {
                        'planet1': w.planet1,
                        'planet2': w.planet2,
                        'winner': w.winner,
                        'loser': w.loser,
                        'starts': _fmt(w.starts),
                        'exact': _fmt(w.exact),
                        'ends': _fmt(w.ends),
                        'ongoing': w.ends is None,
                        'min_separation_arcmin': w.min_separation_arcmin,
                    }
                    for w in wars
                ],
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_get_rashi_ingresses(
    start_date: str,
    end_date: str,
    planets: Optional[list] = None,
    ayanamsa: str = 'lahiri',
) -> str:
    """Return all rashi ingress (sign-change) events in a date range."""
    try:
        from telugu_panchangam.engines.utils import _validate_ayanamsa

        _validate_ayanamsa(ayanamsa)
        start, end = _date_interval(start_date, end_date, 365, _DATE_RANGE_LIMIT_ERROR)
        _validate_planets(planets, INGRESS_PLANETS)

        events = rashi_ingresses(start, end, planets=planets, ayanamsa=ayanamsa)

        def _fmt(dt):
            return dt.strftime('%Y-%m-%d %H:%M UTC') if dt else None

        return json.dumps(
            {
                'start_date': start_date,
                'end_date': end_date,
                'ayanamsa': ayanamsa,
                'note': (
                    'Sidereal (Lahiri) rashi ingresses — when each planet crosses a '
                    'sign boundary. Retrograde ingresses (planet re-enters a sign it '
                    'recently left) are included. exits = next sign change for that '
                    'planet, even if it falls outside the requested range; null if '
                    'the planet stays in the same sign for > 3 years.'
                ),
                'ingresses': [
                    {
                        'planet': e.planet,
                        'rashi': e.rashi,
                        'enters': _fmt(e.enters),
                        'exits': _fmt(e.exits),
                    }
                    for e in events
                ],
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_get_eclipse_calendar(
    start_date: str,
    end_date: str,
    city: str = 'Hyderabad',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    """Return all solar and lunar eclipses in a date range with per-city visibility."""
    try:
        import pytz as _pytz

        start, end = _date_interval(
            start_date, end_date, 730, 'Date range exceeds 730-day limit.'
        )
        loc = _resolve_city(city, latitude, longitude, timezone)

        jd_start = local_midnight_jd(start, loc.timezone)
        jd_end = local_midnight_jd(end, loc.timezone) + 1.0
        precomputed = list_eclipses_in_range(jd_start, jd_end)

        tz_obj = _pytz.timezone(loc.timezone)
        out = []
        for ec in precomputed:
            local_max = jd_to_utc(ec['jd_max']).astimezone(tz_obj)
            eclipse_date = local_max.date()
            info = get_eclipse_from_precomputed(eclipse_date, [ec], loc)
            if info is None:
                # eclipse exists globally but couldn't be processed — still include
                info_dict = {
                    'kind': ec['kind'],
                    'subtype': ec['subtype'],
                    'visible': False,
                    'start': _fmt_time(jd_to_utc(ec['jd_start']), loc.timezone),
                    'end': _fmt_time(jd_to_utc(ec['jd_end']), loc.timezone),
                    'sutak': None,
                }
            else:
                info_dict = {
                    'kind': info.kind,
                    'subtype': info.subtype,
                    'visible': info.visible,
                    'start': _fmt_time(info.start, loc.timezone),
                    'end': _fmt_time(info.end, loc.timezone),
                    'sutak': {
                        'start': _fmt_time(info.sutak_start, loc.timezone),
                        'end': _fmt_time(info.sutak_end, loc.timezone),
                    }
                    if info.sutak_start
                    else None,
                }
            out.append({'date': eclipse_date.isoformat(), **info_dict})

        return json.dumps(
            {
                'start_date': start_date,
                'end_date': end_date,
                'city': city,
                'note': (
                    'visible=true means the eclipse is observable from the given city. '
                    'sutak (ritual impurity period) is only populated for visible eclipses: '
                    '12 hours before a Solar eclipse, 9 hours before a Lunar eclipse.'
                ),
                'eclipses': out,
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})


def tool_get_panchanga_shuddhi(
    date_str: str,
    city: str = 'Hyderabad',
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    """Panchanga Shuddhi — five-limb purity assessment for muhurta planning."""
    try:
        d = _parse_date(date_str)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _get_engine(system)
        day = engine.calculate(d, loc)
        result = assess_shuddhi(day)
        return json.dumps(
            {
                'date': date_str,
                'city': city,
                'system': system,
                'verdict': result.verdict,
                'shuddha_count': result.shuddha_count,
                'note': (
                    'Panchanga Shuddhi measures the purity of each of the five Panchangam '
                    'limbs at sunrise. shuddha_count (0-5) is the number of pure limbs; '
                    'Sarva Shuddha (5) is ideal for auspicious works. '
                    'Values marked "mixed" neither help nor harm; "ashuddha" are to be avoided.'
                ),
                'limbs': [
                    {
                        'limb': lb.limb,
                        'value': lb.value,
                        'quality': lb.quality,
                        'shuddha': lb.shuddha,
                        'reason': lb.reason,
                    }
                    for lb in result.limbs
                ],
            }
        )
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception(_TOOL_CALL_FAILED_LOG)
        return json.dumps({'error': _CALCULATION_FAILED_ERROR})
