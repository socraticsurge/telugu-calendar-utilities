import json
import calendar
from datetime import date, datetime, timedelta
from typing import Optional

import pytz

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.engines.base import GANDA_MOOLA_NAKSHATRAS
from telugu_panchangam.personal.tarabalam import taras_for_day, _nak_index
from telugu_panchangam.personal.chandrabalam import chandra_position, chandra_verdict, _rasi_index
from telugu_panchangam.models.panchangam_day import Location, PanchangamDay
from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates

_ENGINES = {
    'drik': DrikGanitaEngine(),
    'surya_siddhanta': SuryaSiddhantaEngine(),
    'vakya': VakyaEngine(),
}

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
    if latitude is not None and longitude is not None:
        if timezone is None:
            timezone = timezone_for_coordinates(float(latitude), float(longitude))
        return Location(name=city or 'Custom', lat=float(latitude), lon=float(longitude), timezone=timezone)
    lat, lon, tz = resolve_location(city)
    return Location(name=city, lat=lat, lon=lon, timezone=tz)


def _fmt_time(dt: datetime, tz_str: str) -> str:
    return dt.astimezone(pytz.timezone(tz_str)).strftime('%H:%M')


def _span_to_dict(span, tz: str) -> dict:
    return {
        'name': span.name,
        'start': _fmt_time(span.start, tz),
        'end': _fmt_time(span.end, tz),
    }


def _window_to_dict(window, tz: str) -> dict:
    return {
        'start': _fmt_time(window.start, tz),
        'end': _fmt_time(window.end, tz),
    }


def _eclipse_to_dict(eclipse, tz: str) -> Optional[dict]:
    if eclipse is None:
        return None
    return {
        'kind': eclipse.kind,
        'subtype': eclipse.subtype,
        'visible': eclipse.visible,
        'start': _fmt_time(eclipse.start, tz),
        'end': _fmt_time(eclipse.end, tz),
        'sutak': {
            'start': _fmt_time(eclipse.sutak_start, tz),
            'end': _fmt_time(eclipse.sutak_end, tz),
        } if eclipse.sutak_start is not None else None,
    }


def _special_events(day: PanchangamDay) -> list[str]:
    events = list(day.festivals)
    if day.nakshatra.name in GANDA_MOOLA_NAKSHATRAS:
        events.append(f'Ganda Moola ({day.nakshatra.name})')
    if day.is_ekadashi:         events.append('Ekadashi — fasting day')
    if day.is_amavasya:         events.append('Amavasya')
    if day.is_pournami:         events.append('Pournami')
    if day.is_shani_pradosham:  events.append('Shani Pradosham')
    elif day.is_soma_pradosham: events.append('Soma Pradosham')
    elif day.is_pradosham:      events.append('Pradosham')
    if day.sankramanam and not (day.sankramanam == 'Makara'
                                and 'Makara Sankranti' in day.festivals):
        events.append(f'{day.sankramanam} Sankramanam')
    if day.eclipse:             events.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
    return events


def tool_list_supported_cities() -> str:
    return json.dumps([
        {
            'name': c.name,
            'latitude': c.lat,
            'longitude': c.lon,
            'timezone': c.timezone,
            'country': _TIMEZONE_COUNTRY.get(c.timezone, 'Unknown'),
        }
        for c in CITIES
    ])


def tool_get_panchangam(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        d = _parse_date(date_str)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        day = _ENGINES[system].calculate(d, loc)
        tz = loc.timezone
        specials = _special_events(day)
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'metadata': {
                'samvatsara': day.samvatsara,
                'ayanam': day.ayanam,
                'rituvu': day.rituvu,
                'maasam': day.maasam,
                'paksham': day.paksham,
                'vaaram': day.vaaram,
                'solar_sign': day.solar_sign,
                'lunar_sign': day.lunar_sign,
            },
            'pancha_anga': {
                'tithi':     _span_to_dict(day.tithi, tz),
                'nakshatra': _span_to_dict(day.nakshatra, tz),
                'yoga':      _span_to_dict(day.yoga, tz),
                'karana':    [_span_to_dict(k, tz) for k in day.karana],
            },
            'sky': {
                'sunrise':  _fmt_time(day.sunrise, tz),
                'sunset':   _fmt_time(day.sunset, tz),
                'moonrise': _fmt_time(day.moonrise, tz),
                'moonset':  _fmt_time(day.moonset, tz),
            },
            'auspicious': {
                'brahma_muhurta':  _window_to_dict(day.brahma_muhurta, tz),
                'abhijit_muhurta': _window_to_dict(day.abhijit_muhurta, tz) if day.abhijit_muhurta else None,
                'amrita_kalam':    [_window_to_dict(w, tz) for w in day.amrita_kalam],
            },
            'inauspicious': {
                'rahu_kalam':   _window_to_dict(day.rahu_kalam, tz),
                'gulika_kalam': _window_to_dict(day.gulika_kalam, tz),
                'yamagandam':   _window_to_dict(day.yamagandam, tz),
                'varjyam':      [_window_to_dict(w, tz) for w in day.varjyam],
                'durmuhurtham': [_window_to_dict(w, tz) for w in day.durmuhurtham],
            },
            'choghadiya': [
                {'name': w.name, 'start': _fmt_time(w.start, tz), 'end': _fmt_time(w.end, tz)}
                for w in day.choghadiya
            ],
            'eclipse': _eclipse_to_dict(day.eclipse, tz),
            'special_yogas': day.special_yogas,
            'special_days': specials,
            'is_special': bool(specials),
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})


def tool_get_muhurta(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        d = _parse_date(date_str)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        day = _ENGINES[system].calculate(d, loc)
        tz = loc.timezone
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'auspicious': {
                'brahma_muhurta':  _window_to_dict(day.brahma_muhurta, tz),
                'abhijit_muhurta': _window_to_dict(day.abhijit_muhurta, tz) if day.abhijit_muhurta else None,
                'amrita_kalam':    [_window_to_dict(w, tz) for w in day.amrita_kalam],
            },
            'inauspicious': {
                'rahu_kalam':   _window_to_dict(day.rahu_kalam, tz),
                'gulika_kalam': _window_to_dict(day.gulika_kalam, tz),
                'yamagandam':   _window_to_dict(day.yamagandam, tz),
                'varjyam':      [_window_to_dict(w, tz) for w in day.varjyam],
                'durmuhurtham': [_window_to_dict(w, tz) for w in day.durmuhurtham],
            },
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})


def tool_get_panchangam_range(
    start_date: str,
    end_date: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    """Return a compact Panchangam summary for each day in [start_date, end_date]. Maximum span: 31 days."""
    try:
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError("end_date must be >= start_date.")
        if (end - start).days > 30:
            raise ValueError("Date range exceeds 31-day limit. Use multiple calls for longer spans.")
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]
        tz = loc.timezone

        days = []
        d = start
        while d <= end:
            day = engine.calculate(d, loc)
            specials = _special_events(day)
            days.append({
                'date': d.isoformat(),
                'vaaram': day.vaaram,
                'tithi': day.tithi.name,
                'nakshatra': day.nakshatra.name,
                'yoga': day.yoga.name,
                'sunrise': _fmt_time(day.sunrise, tz),
                'sunset': _fmt_time(day.sunset, tz),
                'auspicious': {
                    'brahma_muhurta':  _window_to_dict(day.brahma_muhurta, tz),
                    'abhijit_muhurta': _window_to_dict(day.abhijit_muhurta, tz) if day.abhijit_muhurta else None,
                    'amrita_kalam':    [_window_to_dict(w, tz) for w in day.amrita_kalam],
                },
                'inauspicious': {
                    'rahu_kalam':   _window_to_dict(day.rahu_kalam, tz),
                    'gulika_kalam': _window_to_dict(day.gulika_kalam, tz),
                    'yamagandam':   _window_to_dict(day.yamagandam, tz),
                    'varjyam':      [_window_to_dict(w, tz) for w in day.varjyam],
                    'durmuhurtham': [_window_to_dict(w, tz) for w in day.durmuhurtham],
                },
                'eclipse': _eclipse_to_dict(day.eclipse, tz),
                'special_yogas': day.special_yogas,
                'special_days': specials,
                'is_special': bool(specials),
            })
            d += timedelta(days=1)

        return json.dumps({
            'start_date': start_date,
            'end_date': end_date,
            'city': city,
            'system': system,
            'days': days,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})


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
            raise ValueError(f"Invalid month {month}. Must be 1–12.")
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]
        _, days_in_month = calendar.monthrange(year, month)
        special_days = []
        for day_num in range(1, days_in_month + 1):
            d = date(year, month, day_num)
            day = engine.calculate(d, loc)
            is_notable = (
                day.is_ekadashi or day.is_amavasya or day.is_pournami
                or day.is_pradosham or day.is_sankranti or day.eclipse is not None
            )
            if is_notable:
                events = _special_events(day)
                special_days.append({
                    'date': d.isoformat(),
                    'tithi': day.tithi.name,
                    'events': events,
                    'special_yogas': day.special_yogas,
                })
        return json.dumps({
            'year': year,
            'month': month,
            'city': city,
            'system': system,
            'special_days': special_days,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})


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
        if chandra_mode not in ('stars', 'puja_ok', 'strict'):
            raise ValueError("chandra_mode must be 'stars', 'puja_ok' or 'strict'.")
        if not 1 <= len(janma_nakshatras) <= 4:
            raise ValueError('Provide 1 to 4 janma nakshatras.')
        if not 1 <= days <= 60:
            raise ValueError('days must be between 1 and 60.')
        for nak in janma_nakshatras:
            _nak_index(nak)  # raises with the canonical list on a misspelling
        if janma_rasis is not None:
            if len(janma_rasis) != len(janma_nakshatras):
                raise ValueError('janma_rasis must align with janma_nakshatras '
                                 '(use null for people whose rashi is unknown).')
            for r in janma_rasis:
                if r:
                    _rasi_index(r)
        start = _parse_date(start_date)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]

        out_days = []
        good_dates = []
        for i in range(days):
            d = start + timedelta(days=i)
            day = engine.calculate(d, loc, include_eclipse=False)
            nak = day.nakshatra.name
            taras = taras_for_day(nak, janma_nakshatras)
            if janma_rasis is not None:
                for t, rasi in zip(taras, janma_rasis):
                    if rasi:
                        pos = chandra_position(rasi, day.lunar_sign)
                        t['chandra'] = {'position': pos, 'verdict': chandra_verdict(pos)}
            def _ok(t):
                if not t['auspicious']:
                    return False
                v = t.get('chandra', {}).get('verdict')
                if v is None or chandra_mode == 'stars':
                    return True
                if chandra_mode == 'puja_ok':
                    return v != 'bad'
                return v == 'good'
            all_good = all(_ok(t) for t in taras)
            if all_good:
                good_dates.append(d.isoformat())
            out_days.append({
                'date': d.isoformat(),
                'vaaram': day.vaaram,
                'nakshatra': nak,
                'nakshatra_until': _fmt_time(day.nakshatra.end, loc.timezone),
                'tithi': day.tithi.name,
                'taras': taras,
                'good_for_all': all_good,
            })
        return json.dumps({
            'janma_nakshatras': list(janma_nakshatras),
            'city': city, 'system': system,
            'tara_convention': 'auspicious: 2 Sampat, 4 Kshema, 6 Sadhana, 8 Mitra, 9 Parama Mitra; '
                               'avoid: 1 Janma, 3 Vipat, 5 Pratyak, 7 Naidhana. '
                               'Day labelled by the sunrise nakshatra; it changes at nakshatra_until.',
            'chandra_convention': 'when janma_rasis given: positions 1,3,6,7,10,11 good; '
                                  '2,5,9 workable with remedial puja; 4,8,12 avoid (8 is Ashtama Chandra). '
                                  f'chandra_mode={chandra_mode}: stars=chandra annotates only, '
                                  'puja_ok=moon-avoid days dropped, strict=moon must be good.',
            'days': out_days,
            'good_for_all_dates': good_dates,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})
