import json
import calendar
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pytz

_log = logging.getLogger(__name__)
_MAX_NAME = 80   # max bytes accepted for city/nakshatra/rashi tokens

from telugu_panchangam.cities import CITIES
from telugu_panchangam.maudhya_calendar import combustion_periods, PLANET_NAMES
from telugu_panchangam.graha_yuddha import graha_yuddha_periods, YUDDHA_PLANETS
from telugu_panchangam.ingress import rashi_ingresses, INGRESS_PLANETS
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.panchangam_names import GANDA_MOOLA_NAKSHATRAS
from telugu_panchangam.personal.tarabalam import taras_for_day, _nak_index
from telugu_panchangam.personal.chandrabalam import chandra_position, chandra_verdict, _rasi_index
from telugu_panchangam.gochara.positions import graha_positions
from telugu_panchangam.gochara.rules import (
    GOCHARA_PROVENANCE, gochara_for, named_conditions,
)
from telugu_panchangam.personal.phalalu import rasi_phalalu
from telugu_panchangam.personal.muhurta import day_slots, night_slots, diagnose_day, assign_tiers, ACTIVITIES, TIER_NAMES
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES
from telugu_panchangam.panchangam_provenance import panchangam_provenance
from telugu_panchangam.engines.utils import get_sunrise, local_midnight_jd, jd_to_utc
from telugu_panchangam.models.panchangam_day import Location, PanchangamDay
from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates
from telugu_panchangam.eclipses import list_eclipses_in_range, get_eclipse_from_precomputed
from telugu_panchangam.panchanga_shuddhi import assess_shuddhi
from telugu_panchangam.personal.lagna_hora import get_horas, get_lagna_transitions

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

_MUHURTA_DISCLAIMER = (
    'Slots intersect good choghadiya blocks with every inauspicious '
    'window removed (Rahu Kalam, Gulika, Yamagandam, Varjyam, '
    'Durmuhurtham). Scoring: tarabalam +/-1 per person, chandrabalam '
    '+/-1 per person, tithi class (preferred +1 / activity-avoided -1 / '
    'Rikta -2; Pushya nakshatra cancels Rikta entirely, '
    'Sarvartha/Amrita Siddhi partially offsets it to -1), vara match +1, '
    'special-yoga bonuses (Sarvartha/Amrita Siddhi +2, Siddha Yoga +1, '
    'Dvipushkara/Tripushkara +1, Visha/Dagdha -2), '
    'Nitya yoga (auspicious +1, Vyatipata/Vaidhriti -2 + samskara skip, '
    'dosha-window -1), Abhijit/Amrita +2, activity bias +1. '
    'Eclipse days are skipped outright. '
    'Each slot carries a tier (Excellent/Good/Fair/Avoid), assigned '
    'relative to the highest/lowest score found across this search '
    '(so "Excellent" means the best of what turned up, not a fixed '
    'absolute bar), and a reason_groups breakdown '
    '(slot_quality, day_quality, group_fit, '
    'activity_match, notes) for transparent reasoning. '
    'personal_dosha (ashtama_chandra/chandra_avoid/chandra_remedial/null) '
    'flags an unrectified personal Moon caution, and day_dosha '
    '(rikta_tithi/visha_dagdha_yoga/vyatipata_vaidhriti/null) flags a '
    'day-level dosha: either keeps a slot capped below Excellent, and '
    'slots are ranked tier-first (Excellent > Good > '
    'Fair > Avoid), then by score, then preferring dosha-free slots. '
    'Tiers are relative to this search, not a universal standard — '
    '"Good"/"Fair" slots with personal_dosha and day_dosha both null are '
    'workable choices, not just runner-ups. When presenting results, '
    'surface personal_dosha/day_dosha and notes regardless of tier, and '
    'for weddings, major samskaras, or any caution the devotee is unsure '
    'about, recommend consulting their purohit.'
)


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
    if isinstance(city, str) and len(city) > _MAX_NAME:
        raise ValueError('City name too long.')
    if latitude is not None and longitude is not None:
        if not (-90.0 <= float(latitude) <= 90.0):
            raise ValueError('latitude must be between -90 and 90.')
        if not (-180.0 <= float(longitude) <= 180.0):
            raise ValueError('longitude must be between -180 and 180.')
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


def _maudhya_to_dict(m) -> dict | None:
    if m is None:
        return None
    return {
        'graha': m.graha,
        'elongation_deg': round(m.elongation_deg, 3),
        'combust': m.combust,
        'threshold_deg': m.threshold_deg,
    }


def _window_to_dict(window, tz: str) -> dict | None:
    if window is None:
        return None
    return {
        'start': _fmt_time(window.start, tz),
        'end': _fmt_time(window.end, tz),
    }


def _panchaka_to_dict(p) -> dict | None:
    if p is None:
        return None
    return {
        'remainder': p.remainder,
        'name': p.name,
        'auspicious': p.auspicious,
        'avoid_for': p.avoid_for,
    }


def _ghati_window_to_dict(gw, tz: str) -> dict | None:
    if gw is None:
        return None
    return {
        'name': gw.name,
        'start': _fmt_time(gw.start, tz),
        'end': _fmt_time(gw.end, tz),
        'start_ghati': round(gw.start_ghati, 4),
        'end_ghati': round(gw.end_ghati, 4),
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
    ayanamsa: str = 'lahiri',
) -> str:
    try:
        d = _parse_date(date_str)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _get_engine(system, ayanamsa)
        day = engine.calculate(d, loc)
        tz = loc.timezone
        specials = _special_events(day)
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'ayanamsa': ayanamsa,
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
                'tithi':          _span_to_dict(day.tithi, tz),
                'nakshatra':      _span_to_dict(day.nakshatra, tz),
                'nakshatra_pada': day.nakshatra_pada,
                'yoga':           _span_to_dict(day.yoga, tz),
                'karana':         [_span_to_dict(k, tz) for k in day.karana],
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
                'vishaghati':   [_ghati_window_to_dict(w, tz) for w in day.vishaghati],
            },
            'bhadra_mukha':  _ghati_window_to_dict(day.bhadra_mukha, tz),
            'bhadra_puchha': _ghati_window_to_dict(day.bhadra_puchha, tz),
            'sankramana_avoidance': _window_to_dict(day.sankramana_avoidance, tz),
            'choghadiya': [
                {'name': w.name, 'start': _fmt_time(w.start, tz), 'end': _fmt_time(w.end, tz)}
                for w in day.choghadiya
            ],
            'eclipse': _eclipse_to_dict(day.eclipse, tz),
            'special_yogas': day.special_yogas,
            'special_days': specials,
            'is_special': bool(specials),
            'ghati_clock': (
                {
                    'sunrise': _fmt_time(day.ghati_clock.sunrise, tz),
                    'next_sunrise': _fmt_time(day.ghati_clock.next_sunrise, tz),
                    'seconds_per_ghati': day.ghati_clock.seconds_per_ghati,
                } if day.ghati_clock else None
            ),
            'in_panchaka_nakshatra': day.in_panchaka_nakshatra,
            'is_khar_maasa': day.is_khar_maasa,
            'khar_maasa_name': day.khar_maasa_name,
            'is_pitru_paksha': day.is_pitru_paksha,
            'simha_stha_guru': day.simha_stha_guru,
            'simha_stha_shukra': day.simha_stha_shukra,
            'guru_maudhya': _maudhya_to_dict(day.guru_maudhya),
            'shukra_maudhya': _maudhya_to_dict(day.shukra_maudhya),
            'anandadi_yoga': day.anandadi_yoga,
            'disha_shoola_direction': day.disha_shoola_direction,
            'nakshatra_mukha': day.nakshatra_mukha,
            'panchaka_rahita': _panchaka_to_dict(day.panchaka_rahita),
            'provenance': panchangam_provenance(system),
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
                'vishaghati':   [_ghati_window_to_dict(w, tz) for w in day.vishaghati],
            },
            'bhadra_mukha':  _ghati_window_to_dict(day.bhadra_mukha, tz),
            'bhadra_puchha': _ghati_window_to_dict(day.bhadra_puchha, tz),
            'sankramana_avoidance': _window_to_dict(day.sankramana_avoidance, tz),
            'nakshatra_pada': day.nakshatra_pada,
            'ghati_clock': (
                {
                    'sunrise': _fmt_time(day.ghati_clock.sunrise, tz),
                    'next_sunrise': _fmt_time(day.ghati_clock.next_sunrise, tz),
                    'seconds_per_ghati': day.ghati_clock.seconds_per_ghati,
                } if day.ghati_clock else None
            ),
            'in_panchaka_nakshatra': day.in_panchaka_nakshatra,
            'is_khar_maasa': day.is_khar_maasa,
            'khar_maasa_name': day.khar_maasa_name,
            'is_pitru_paksha': day.is_pitru_paksha,
            'simha_stha_guru': day.simha_stha_guru,
            'simha_stha_shukra': day.simha_stha_shukra,
            'guru_maudhya': _maudhya_to_dict(day.guru_maudhya),
            'shukra_maudhya': _maudhya_to_dict(day.shukra_maudhya),
            'anandadi_yoga': day.anandadi_yoga,
            'disha_shoola_direction': day.disha_shoola_direction,
            'nakshatra_mukha': day.nakshatra_mukha,
            'panchaka_rahita': _panchaka_to_dict(day.panchaka_rahita),
            'provenance': panchangam_provenance(system),
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


def tool_get_daily_horas(
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
        horas = get_horas(day)
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'horas': [
                {'name': w.name, 'start': _fmt_time(w.start, tz), 'end': _fmt_time(w.end, tz)}
                for w in horas
            ]
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


def tool_get_lagna_transitions(
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
        lagnas = get_lagna_transitions(day)
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'lagnas': [
                {'name': w.name, 'start': _fmt_time(w.start, tz), 'end': _fmt_time(w.end, tz)}
                for w in lagnas
            ]
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError("end_date must be >= start_date.")
        if (end - start).days > 30:
            raise ValueError("Date range exceeds 31-day limit. Use multiple calls for longer spans.")
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _get_engine(system, ayanamsa)
        tz = loc.timezone

        days_count = (end - start).days + 1
        calculated_days = engine.calculate_bulk(start, days_count, loc)

        days = []
        for d, day in zip([start + timedelta(days=i) for i in range(days_count)], calculated_days):
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
                    'vishaghati':   [_ghati_window_to_dict(w, tz) for w in day.vishaghati],
                },
                'bhadra_mukha':  _ghati_window_to_dict(day.bhadra_mukha, tz),
                'bhadra_puchha': _ghati_window_to_dict(day.bhadra_puchha, tz),
                'sankramana_avoidance': _window_to_dict(day.sankramana_avoidance, tz),
                'nakshatra_pada': day.nakshatra_pada,
                'ghati_clock': (
                    {
                        'sunrise': _fmt_time(day.ghati_clock.sunrise, tz),
                        'next_sunrise': _fmt_time(day.ghati_clock.next_sunrise, tz),
                        'seconds_per_ghati': day.ghati_clock.seconds_per_ghati,
                    } if day.ghati_clock else None
                ),
                'eclipse': _eclipse_to_dict(day.eclipse, tz),
                'special_yogas': day.special_yogas,
                'special_days': specials,
                'is_special': bool(specials),
                'in_panchaka_nakshatra': day.in_panchaka_nakshatra,
                'is_khar_maasa': day.is_khar_maasa,
                'khar_maasa_name': day.khar_maasa_name,
                'is_pitru_paksha': day.is_pitru_paksha,
                'simha_stha_guru': day.simha_stha_guru,
                'simha_stha_shukra': day.simha_stha_shukra,
                'guru_maudhya': _maudhya_to_dict(day.guru_maudhya),
                'shukra_maudhya': _maudhya_to_dict(day.shukra_maudhya),
                'anandadi_yoga': day.anandadi_yoga,
                'disha_shoola_direction': day.disha_shoola_direction,
                'nakshatra_mukha': day.nakshatra_mukha,
                'panchaka_rahita': _panchaka_to_dict(day.panchaka_rahita),
            })

        return json.dumps({
            'start_date': start_date,
            'end_date': end_date,
            'city': city,
            'system': system,
            'ayanamsa': ayanamsa,
            'days': days,
            'provenance': panchangam_provenance(system),
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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

        jd_start = local_midnight_jd(date(year, month, 1), loc.timezone)
        if month == 12:
            next_month_date = date(year + 1, 1, 1)
        else:
            next_month_date = date(year, month + 1, 1)
        jd_end = local_midnight_jd(next_month_date, loc.timezone)
        precomputed_eclipses = list_eclipses_in_range(jd_start, jd_end)

        special_days = []
        for day_num in range(1, days_in_month + 1):
            d = date(year, month, day_num)
            day = engine.calculate(d, loc, include_eclipse=False)
            day.eclipse = get_eclipse_from_precomputed(d, precomputed_eclipses, loc)

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
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
            if not isinstance(nak, str) or len(nak) > _MAX_NAME:
                raise ValueError('Invalid nakshatra name.')
            _nak_index(nak)  # raises with the canonical list on a misspelling
        if janma_rasis is not None:
            if len(janma_rasis) != len(janma_nakshatras):
                raise ValueError('janma_rasis must align with janma_nakshatras '
                                 '(use null for people whose rashi is unknown).')
            for r in janma_rasis:
                if r:
                    if not isinstance(r, str) or len(r) > _MAX_NAME:
                        raise ValueError('Invalid rashi name.')
                    _rasi_index(r)
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
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        return json.dumps({
            'date': date_str,
            'city': city,
            'at': 'sunrise',
            'sunrise': _fmt_time(jd_to_utc(jd_sunrise), loc.timezone),
            'ayanamsa': ayanamsa,
            'grahas': graha_positions(jd_sunrise, ayanamsa),
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        jd_sunrise = get_sunrise(local_midnight_jd(d, loc.timezone), [loc.lon, loc.lat, 0.0])
        positions = graha_positions(jd_sunrise, ayanamsa)
        sky = {p['graha']: p['rasi'] for p in positions}
        verdicts = {v['graha']: v for v in gochara_for(janma_rasi, sky)}
        merged = []
        for p in positions:
            v = verdicts[p['graha']]
            merged.append({**p, 'position_from_janma_rasi': v['position'],
                           'verdict': v['verdict'], 'vedha_by': v['vedha_by']})
        return json.dumps({
            'date': date_str, 'city': city, 'janma_rasi': janma_rasi,
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
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        jd_sunrise = get_sunrise(local_midnight_jd(d, loc.timezone), [loc.lon, loc.lat, 0.0])
        positions = graha_positions(jd_sunrise, ayanamsa)
        sky = {p['graha']: p['rasi'] for p in positions}
        day_nak = next(p['nakshatra'] for p in positions if p['graha'] == 'Chandra')
        out = rasi_phalalu(janma_rasi, sky,
                           janma_nakshatra=janma_nakshatra,
                           day_nakshatra=day_nak if janma_nakshatra else None)
        out.update({
            'date': date_str, 'city': city, 'day_nakshatra': day_nak,
            'disclaimer': 'Every line is rendered from computed gochara/chandrabalam/'
                          'tarabalam facts (Brihat Samhita conventions, sunrise positions). '
                          'This is a daily reading, not a horoscope consultation or a muhurta.',
        })
        return json.dumps(out)
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


def _resolve_city_with_alt(
    city: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> Location:
    """Like _resolve_city but preserves altitude from the CITIES list for heliacal accuracy."""
    if isinstance(city, str) and len(city) > _MAX_NAME:
        raise ValueError('City name too long.')
    if latitude is not None and longitude is not None:
        if not (-90.0 <= float(latitude) <= 90.0):
            raise ValueError('latitude must be between -90 and 90.')
        if not (-180.0 <= float(longitude) <= 180.0):
            raise ValueError('longitude must be between -180 and 180.')
        if timezone is None:
            timezone = timezone_for_coordinates(float(latitude), float(longitude))
        return Location(name=city or 'Custom', lat=float(latitude), lon=float(longitude), timezone=timezone)
    known = next((c for c in CITIES if c.name.lower() == (city or '').lower()), None)
    if known:
        return known
    lat, lon, tz = resolve_location(city)
    return Location(name=city, lat=lat, lon=lon, timezone=tz)


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
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError('end_date must be >= start_date.')
        if (end - start).days > 365:
            raise ValueError('Date range exceeds 366-day limit. Use multiple calls for longer spans.')
        if planets is not None:
            bad = [p for p in planets if p not in set(PLANET_NAMES)]
            if bad:
                raise ValueError(f'Unknown planet(s): {bad}. Valid: {PLANET_NAMES}')
        loc = _resolve_city_with_alt(city, latitude, longitude, timezone)
        tz_str = loc.timezone

        periods = combustion_periods(start, end, loc, planets=planets)

        def _fmt_dt(dt, tz_s):
            if dt is None:
                return None
            return dt.astimezone(pytz.timezone(tz_s)).strftime('%Y-%m-%d %H:%M')

        return json.dumps({
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
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
    if janma_nakshatras:
        if len(janma_nakshatras) > 4:
            raise ValueError('Provide at most 4 janma nakshatras.')
        for nak in janma_nakshatras:
            if not isinstance(nak, str) or len(nak) > _MAX_NAME:
                raise ValueError('Invalid nakshatra name.')
            _nak_index(nak)
    if janma_rasis is not None:
        if not janma_nakshatras or len(janma_rasis) != len(janma_nakshatras):
            raise ValueError('janma_rasis must align with janma_nakshatras '
                             '(use null for people whose rashi is unknown).')
        for r in janma_rasis:
            if r is not None:
                if not isinstance(r, str) or len(r) > _MAX_NAME:
                    raise ValueError('Invalid rashi name.')
                _rasi_index(r)
    if janma_lagnas is not None:
        if not janma_nakshatras or len(janma_lagnas) != len(janma_nakshatras):
            raise ValueError('janma_lagnas must align with janma_nakshatras '
                             '(use null for people whose lagna is unknown).')
        for l in janma_lagnas:
            if l is not None:
                if not isinstance(l, str) or len(l) > _MAX_NAME:
                    raise ValueError('Invalid lagna rashi name.')
                _rasi_index(l)


def _gather_muhurta_slots(
    start: date,
    days: int,
    loc: Location,
    engine: object,
    activity: str,
    janma_nakshatras: Optional[list],
    janma_rasis: Optional[list],
    chandra_mode: str,
    janma_lagnas: Optional[list] = None,
    travel_direction: Optional[str] = None,
    include_night: bool = False,
) -> tuple[list, list]:
    slots = []
    dropped_days = []
    tz = loc.timezone

    # When include_night=True we need the day after the last requested day
    # to get next_sunrise for the final night's blocks.
    extra = 1 if include_night else 0
    end_date = start + timedelta(days=days - 1)
    jd_start_range = local_midnight_jd(start, loc.timezone)
    jd_end_range = local_midnight_jd(end_date + timedelta(days=1 + extra), loc.timezone)
    eclipses_in_range = list_eclipses_in_range(jd_start_range, jd_end_range)

    # Pre-calculate all needed days (+ one extra when include_night=True)
    calculated_days = {}
    for i in range(days + extra):
        d = start + timedelta(days=i)
        pd = engine.calculate(d, loc, include_eclipse=False)
        pd.eclipse = get_eclipse_from_precomputed(d, eclipses_in_range, loc)
        calculated_days[i] = pd

    for i in range(days):
        day = calculated_days[i]
        day_results = day_slots(day, activity=activity,
                                janma_nakshatras=janma_nakshatras,
                                janma_rasis=janma_rasis,
                                janma_lagnas=janma_lagnas,
                                chandra_mode=chandra_mode,
                                travel_direction=travel_direction,
                                engine=engine)
        night_results = []
        if include_night:
            next_pd = calculated_days[i + 1]
            night_results = night_slots(day, next_pd, activity=activity,
                                        janma_nakshatras=janma_nakshatras,
                                        janma_rasis=janma_rasis,
                                        janma_lagnas=janma_lagnas,
                                        chandra_mode=chandra_mode,
                                        travel_direction=travel_direction,
                                        engine=engine)
        if not day_results and not night_results:
            reason = diagnose_day(day, activity=activity,
                                  janma_nakshatras=janma_nakshatras,
                                  janma_rasis=janma_rasis,
                                  chandra_mode=chandra_mode,
                                  travel_direction=travel_direction)
            if reason:
                dropped_days.append({'date': day.date.isoformat(), 'reason': reason})
        for s in day_results + night_results:
            slots.append({**s, 'start': _fmt_time(s['start'], tz),
                          'end': _fmt_time(s['end'], tz)})
    return slots, dropped_days


def tool_find_muhurta(
    start_date: str,
    days: int = 7,
    activity: str = 'any',
    city: str = 'Hyderabad',
    system: str = 'drik',
    janma_nakshatras: Optional[list] = None,
    janma_rasis: Optional[list] = None,
    janma_lagnas: Optional[list] = None,
    chandra_mode: str = 'stars',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
    ayanamsa: str = 'lahiri',
    travel_direction: Optional[str] = None,
    include_night: bool = False,
) -> str:
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
    try:
        _validate_muhurta_inputs(days, activity, chandra_mode,
                                 janma_nakshatras, janma_rasis,
                                 janma_lagnas)
        start = _parse_date(start_date)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _get_engine(system, ayanamsa)

        slots, dropped_days = _gather_muhurta_slots(
            start, days, loc, engine, activity, janma_nakshatras, janma_rasis, chandra_mode,
            janma_lagnas=janma_lagnas,
            travel_direction=travel_direction,
            include_night=include_night,
        )

        # Re-tier across the whole search, not just one day — "Excellent"
        # means the best of what turned up over the full date range.
        assign_tiers(slots)
        slots.sort(key=lambda x: (-TIER_NAMES.index(x['tier']), -x['score'],
                                  x['personal_dosha'] is not None,
                                  x['date'], x['start']))
        rules = ACTIVITY_RULES[activity]
        constraint_fields = (
            'allowed_maasams', 'allowed_varas', 'avoid_vara_paksha',
            'allowed_solar_classes', 'allowed_nakshatras', 'avoid_nakshatras',
            'prefer_nakshatras',
            'allowed_tithi_numbers', 'avoid_tithi_numbers',
            'required_lagna_class',
            'allowed_lagnas', 'caution_lagna_solar',
            'daytime_only', 'forenoon_only', 'allowed_pakshams',
            'allowed_solar_signs', 'allowed_tithi_names', 'skip_on_combust',
        )
        return json.dumps({
            'start_date': start_date, 'days': days, 'activity': activity,
            'city': city, 'system': system, 'chandra_mode': chandra_mode,
            'ayanamsa': ayanamsa,
            'slots': slots[:12],
            'dropped_days': dropped_days,
            'activity_profile': {
                'source_claim': rules.get('source_claim'),
                'audit_claim': rules.get('audit_claim'),
                'heuristic_claim': rules.get('heuristic_claim'),
                'automated_constraints': {
                    field: rules[field]
                    for field in constraint_fields if field in rules
                },
                'manual_checks': rules.get('manual_checks', []),
            },
            'disclaimer': _MUHURTA_DISCLAIMER,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


def tool_get_graha_yuddha(
    start_date: str,
    end_date: str,
    planets: Optional[list] = None,
) -> str:
    """Return Graha Yuddha (planetary war) periods in a date range."""
    try:
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError('end_date must be >= start_date.')
        if (end - start).days > 365:
            raise ValueError('Date range exceeds 366-day limit. Use multiple calls for longer spans.')
        if planets is not None:
            bad = [p for p in planets if p not in set(YUDDHA_PLANETS)]
            if bad:
                raise ValueError(f'Unknown planet(s): {bad}. Valid: {YUDDHA_PLANETS}')

        wars = graha_yuddha_periods(start, end, planets=planets)

        def _fmt(dt):
            return dt.strftime('%Y-%m-%d %H:%M UTC') if dt else None

        return json.dumps({
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
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError('end_date must be >= start_date.')
        if (end - start).days > 365:
            raise ValueError('Date range exceeds 366-day limit. Use multiple calls for longer spans.')
        if planets is not None:
            bad = [p for p in planets if p not in set(INGRESS_PLANETS)]
            if bad:
                raise ValueError(f'Unknown planet(s): {bad}. Valid: {INGRESS_PLANETS}')

        events = rashi_ingresses(start, end, planets=planets, ayanamsa=ayanamsa)

        def _fmt(dt):
            return dt.strftime('%Y-%m-%d %H:%M UTC') if dt else None

        return json.dumps({
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
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        start = _parse_date(start_date)
        end = _parse_date(end_date)
        if end < start:
            raise ValueError('end_date must be >= start_date.')
        if (end - start).days > 730:
            raise ValueError('Date range exceeds 730-day limit.')
        loc = _resolve_city(city, latitude, longitude, timezone)

        jd_start = local_midnight_jd(start, loc.timezone)
        jd_end   = local_midnight_jd(end, loc.timezone) + 1.0
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
                    'end':   _fmt_time(jd_to_utc(ec['jd_end']),   loc.timezone),
                    'sutak': None,
                }
            else:
                info_dict = {
                    'kind': info.kind,
                    'subtype': info.subtype,
                    'visible': info.visible,
                    'start': _fmt_time(info.start, loc.timezone),
                    'end':   _fmt_time(info.end,   loc.timezone),
                    'sutak': {
                        'start': _fmt_time(info.sutak_start, loc.timezone),
                        'end':   _fmt_time(info.sutak_end,   loc.timezone),
                    } if info.sutak_start else None,
                }
            out.append({'date': eclipse_date.isoformat(), **info_dict})

        return json.dumps({
            'start_date': start_date,
            'end_date': end_date,
            'city': city,
            'note': (
                'visible=true means the eclipse is observable from the given city. '
                'sutak (ritual impurity period) is only populated for visible eclipses: '
                '12 hours before a Solar eclipse, 9 hours before a Lunar eclipse.'
            ),
            'eclipses': out,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})


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
        return json.dumps({
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
                    'limb':    lb.limb,
                    'value':   lb.value,
                    'quality': lb.quality,
                    'shuddha': lb.shuddha,
                    'reason':  lb.reason,
                }
                for lb in result.limbs
            ],
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception:
        _log.exception('tool call failed')
        return json.dumps({'error': 'Calculation failed. Please check your inputs and try again.'})
