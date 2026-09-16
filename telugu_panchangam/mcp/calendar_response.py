"""Stable MCP projections of computed days; no engine calls or new rules."""

from datetime import datetime
from typing import Optional

import pytz

from telugu_panchangam.models.panchangam_day import PanchangamDay
from telugu_panchangam.panchangam_names import GANDA_MOOLA_NAKSHATRAS


def format_time(dt: datetime, tz_str: str) -> str:
    return dt.astimezone(pytz.timezone(tz_str)).strftime('%H:%M')


def span_to_dict(span, tz: str) -> dict:
    return {
        'name': span.name,
        'start': format_time(span.start, tz),
        'end': format_time(span.end, tz),
    }


def maudhya_to_dict(m) -> dict | None:
    if m is None:
        return None
    return {
        'graha': m.graha,
        'elongation_deg': round(m.elongation_deg, 3),
        'combust': m.combust,
        'threshold_deg': m.threshold_deg,
    }


def window_to_dict(window, tz: str) -> dict | None:
    if window is None:
        return None
    return {
        'start': format_time(window.start, tz),
        'end': format_time(window.end, tz),
    }


def panchaka_to_dict(p) -> dict | None:
    if p is None:
        return None
    return {
        'remainder': p.remainder,
        'name': p.name,
        'auspicious': p.auspicious,
        'avoid_for': p.avoid_for,
    }


def ghati_window_to_dict(gw, tz: str) -> dict | None:
    if gw is None:
        return None
    return {
        'name': gw.name,
        'start': format_time(gw.start, tz),
        'end': format_time(gw.end, tz),
        'start_ghati': round(gw.start_ghati, 4),
        'end_ghati': round(gw.end_ghati, 4),
    }


def eclipse_to_dict(eclipse, tz: str) -> Optional[dict]:
    if eclipse is None:
        return None
    return {
        'kind': eclipse.kind,
        'subtype': eclipse.subtype,
        'visible': eclipse.visible,
        'start': format_time(eclipse.start, tz),
        'end': format_time(eclipse.end, tz),
        'sutak': {
            'start': format_time(eclipse.sutak_start, tz),
            'end': format_time(eclipse.sutak_end, tz),
        }
        if eclipse.sutak_start is not None
        else None,
    }


def special_events(day: PanchangamDay) -> list[str]:
    events = list(day.festivals)
    if day.nakshatra.name in GANDA_MOOLA_NAKSHATRAS:
        events.append(f'Ganda Moola ({day.nakshatra.name})')
    if day.is_ekadashi:
        events.append('Ekadashi — fasting day')
    if day.is_amavasya:
        events.append('Amavasya')
    if day.is_pournami:
        events.append('Pournami')
    events.extend(_pradosham_events(day))
    events.extend(_sankramana_events(day))
    if day.eclipse:
        events.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
    return events


def _pradosham_events(day: PanchangamDay) -> list[str]:
    if day.is_shani_pradosham:
        return ['Shani Pradosham']
    if day.is_soma_pradosham:
        return ['Soma Pradosham']
    if day.is_pradosham:
        return ['Pradosham']
    return []


def _sankramana_events(day: PanchangamDay) -> list[str]:
    if not day.sankramanam:
        return []
    if day.sankramanam == 'Makara' and 'Makara Sankranti' in day.festivals:
        return []
    return [f'{day.sankramanam} Sankramanam']


def window_fields(day: PanchangamDay, tz: str) -> dict:
    return {
        'auspicious': {
            'brahma_muhurta': window_to_dict(day.brahma_muhurta, tz),
            'abhijit_muhurta': window_to_dict(day.abhijit_muhurta, tz)
            if day.abhijit_muhurta
            else None,
            'amrita_kalam': [window_to_dict(w, tz) for w in day.amrita_kalam],
        },
        'inauspicious': {
            'rahu_kalam': window_to_dict(day.rahu_kalam, tz),
            'gulika_kalam': window_to_dict(day.gulika_kalam, tz),
            'yamagandam': window_to_dict(day.yamagandam, tz),
            'varjyam': [window_to_dict(w, tz) for w in day.varjyam],
            'durmuhurtham': [window_to_dict(w, tz) for w in day.durmuhurtham],
            'vishaghati': [ghati_window_to_dict(w, tz) for w in day.vishaghati],
        },
        'bhadra_mukha': ghati_window_to_dict(day.bhadra_mukha, tz),
        'bhadra_puchha': ghati_window_to_dict(day.bhadra_puchha, tz),
        'sankramana_avoidance': window_to_dict(day.sankramana_avoidance, tz),
    }


def day_flags(day: PanchangamDay) -> dict:
    return {
        'in_panchaka_nakshatra': day.in_panchaka_nakshatra,
        'is_khar_maasa': day.is_khar_maasa,
        'khar_maasa_name': day.khar_maasa_name,
        'is_pitru_paksha': day.is_pitru_paksha,
        'simha_stha_guru': day.simha_stha_guru,
        'simha_stha_shukra': day.simha_stha_shukra,
        'guru_maudhya': maudhya_to_dict(day.guru_maudhya),
        'shukra_maudhya': maudhya_to_dict(day.shukra_maudhya),
        'anandadi_yoga': day.anandadi_yoga,
        'disha_shoola_direction': day.disha_shoola_direction,
        'nakshatra_mukha': day.nakshatra_mukha,
        'panchaka_rahita': panchaka_to_dict(day.panchaka_rahita),
    }


def ghati_clock(clock, tz: str) -> dict | None:
    if clock is None:
        return None
    return {
        'sunrise': format_time(clock.sunrise, tz),
        'next_sunrise': format_time(clock.next_sunrise, tz),
        'seconds_per_ghati': clock.seconds_per_ghati,
    }


def special_fields(day: PanchangamDay, tz: str) -> dict:
    specials = special_events(day)
    return {
        'eclipse': eclipse_to_dict(day.eclipse, tz),
        'special_yogas': day.special_yogas,
        'special_days': specials,
        'is_special': bool(specials),
    }


def panchangam_details(day: PanchangamDay, tz: str) -> dict:
    return {
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
            'tithi': span_to_dict(day.tithi, tz),
            'nakshatra': span_to_dict(day.nakshatra, tz),
            'nakshatra_pada': day.nakshatra_pada,
            'yoga': span_to_dict(day.yoga, tz),
            'karana': [span_to_dict(k, tz) for k in day.karana],
        },
        'sky': {
            'sunrise': format_time(day.sunrise, tz),
            'sunset': format_time(day.sunset, tz),
            'moonrise': format_time(day.moonrise, tz),
            'moonset': format_time(day.moonset, tz),
        },
        **window_fields(day, tz),
        'choghadiya': [span_to_dict(w, tz) for w in day.choghadiya],
        **special_fields(day, tz),
        'ghati_clock': ghati_clock(day.ghati_clock, tz),
        **day_flags(day),
    }


def muhurta_details(day: PanchangamDay, tz: str) -> dict:
    return {
        **window_fields(day, tz),
        'nakshatra_pada': day.nakshatra_pada,
        'ghati_clock': ghati_clock(day.ghati_clock, tz),
        **day_flags(day),
    }


def range_day(d, day: PanchangamDay, tz: str) -> dict:
    return {
        'date': d.isoformat(),
        'vaaram': day.vaaram,
        'tithi': day.tithi.name,
        'nakshatra': day.nakshatra.name,
        'yoga': day.yoga.name,
        'sunrise': format_time(day.sunrise, tz),
        'sunset': format_time(day.sunset, tz),
        **window_fields(day, tz),
        'nakshatra_pada': day.nakshatra_pada,
        'ghati_clock': ghati_clock(day.ghati_clock, tz),
        **special_fields(day, tz),
        **day_flags(day),
    }
