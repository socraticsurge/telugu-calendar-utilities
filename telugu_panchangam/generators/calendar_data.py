"""Versioned browser day data projected directly from PanchangamDay.

The human-readable ICS payload remains available for unmigrated consumers.
Its text is never parsed to obtain calculation inputs. Clock strings preserve
the existing minute precision and civil-date +/-1 display convention.
"""

import json
from datetime import timedelta
from itertools import pairwise

import pytz
from icalendar import Calendar

from telugu_panchangam.engines.base import ekadashi_name
from telugu_panchangam.generators.ics import ICSGenerator
from telugu_panchangam.models.panchangam_day import Window
from telugu_panchangam.panchangam_names import GANDA_MOOLA_NAKSHATRAS
from telugu_panchangam.personal.muhurta import _NIGHT_CHOGHADIYA


def _clock(instant, timezone):
    return instant.astimezone(timezone).strftime("%H:%M")


def _flag(instant, timezone, day_date):
    local_date = instant.astimezone(timezone).date()
    if local_date == day_date:
        return None
    return "+1" if local_date > day_date else "-1"


def _entry(window, timezone, day_date, name=None):
    return {
        "name": name or window.name,
        "start": _clock(window.start, timezone),
        "end": _clock(window.end, timezone),
        "sflag": _flag(window.start, timezone, day_date),
        "eflag": _flag(window.end, timezone, day_date),
    }


def _clock_entry(window, timezone):
    return {
        "name": window.name,
        "start": _clock(window.start, timezone),
        "end": _clock(window.end, timezone),
    }


def _relative_clock(instant, timezone, day_date):
    flag = _flag(instant, timezone, day_date)
    return _clock(instant, timezone) + (f" ({flag})" if flag else "")


def _tithi_label(day):
    if day.is_ekadashi:
        name = ekadashi_name(day.maasam, day.paksham, day.solar_sign)
        if name:
            return f"{name} Ekadashi"
    return day.tithi.name


def _pradosham_label(day):
    if day.is_shani_pradosham:
        return "Shani Pradosham"
    if day.is_soma_pradosham:
        return "Soma Pradosham"
    return "Pradosham" if day.is_pradosham else None


def _sankramanam_label(day):
    if not day.sankramanam:
        return None
    if day.sankramanam == "Makara" and "Makara Sankranti" in day.festivals:
        return None
    return f"{day.sankramanam} Sankramanam"


def _specials(day):
    labels = list(day.festivals)
    for enabled, label in (
        (
            day.nakshatra.name in GANDA_MOOLA_NAKSHATRAS,
            f"Ganda Moola ({day.nakshatra.name})",
        ),
        (day.is_ekadashi, f"{_tithi_label(day)} — fasting day"),
        (day.is_amavasya, "Amavasya"),
        (day.is_pournami, "Pournami"),
    ):
        if enabled:
            labels.append(label)
    labels.extend(filter(None, (_pradosham_label(day), _sankramanam_label(day))))
    if day.eclipse:
        labels.append(f"{day.eclipse.kind} Eclipse ({day.eclipse.subtype})")
    return labels


def _eclipse(day, timezone):
    eclipse = day.eclipse
    if eclipse is None:
        return None

    def time_range(start, end):
        def display(instant):
            if instant is None:
                return "—"
            local = instant.astimezone(timezone)
            prefix = "Previous day " if local.date() < day.date else ""
            return prefix + local.strftime("%H:%M")

        return {"start": display(start), "end": display(end)}

    return {
        "kind": eclipse.kind,
        "subtype": eclipse.subtype,
        "visible": eclipse.visible,
        "window": time_range(eclipse.start, eclipse.end),
        "sutak": time_range(eclipse.sutak_start, eclipse.sutak_end)
        if eclipse.visible
        else None,
    }


def _day_windows(day, timezone):
    auspicious = [(day.brahma_muhurta, "Brahma Muhurta")]
    if day.abhijit_muhurta:
        auspicious.append((day.abhijit_muhurta, "Abhijit Muhurta"))
    auspicious.extend((window, "Amrita Kalam") for window in day.amrita_kalam)
    bad = [
        (day.rahu_kalam, "Rahu Kalam"),
        (day.gulika_kalam, "Gulika Kalam"),
        (day.yamagandam, "Yamagandam"),
    ]
    bad.extend((window, "Varjyam") for window in day.varjyam)
    bad.extend((window, "Durmuhurtham") for window in day.durmuhurtham)
    return {
        "auspicious": [_entry(w, timezone, day.date, name) for w, name in auspicious],
        "inauspicious": [_entry(w, timezone, day.date, name) for w, name in bad],
    }


def _night_choghadiya(day, next_day, timezone):
    if next_day is None:
        return []
    block = (next_day.sunrise - day.sunset) / 8
    names = _NIGHT_CHOGHADIYA[(day.date.weekday() + 1) % 7]
    return [
        _clock_entry(
            Window(name, day.sunset + i * block, day.sunset + (i + 1) * block),
            timezone,
        )
        for i, name in enumerate(names)
    ]


def _karana_text(day, timezone):
    karanas = [
        f"{k.name} {_relative_clock(k.start, timezone, day.date)}–"
        f"{_relative_clock(k.end, timezone, day.date)}"
        for k in day.karana
    ]
    return "  /  ".join(karanas) or None


def day_view(day, next_day=None):
    """Compatibility view for the first migrated browser journeys, without regex."""
    timezone = pytz.timezone(day.location.timezone)
    return {
        "meta": f"{day.samvatsara} Nama Samvatsara · {day.maasam} Maasam · "
        f"{day.paksham} Paksham · {day.vaaram}",
        "samvatsara": day.samvatsara,
        "maasam": day.maasam,
        "paksham": day.paksham,
        "vaaram": day.vaaram,
        "ayanam": day.ayanam,
        "rituvu": day.rituvu,
        "solarSign": day.solar_sign,
        "lunarSign": day.lunar_sign,
        "sunrise": _clock(day.sunrise, timezone),
        "sunset": _clock(day.sunset, timezone),
        "moonrise": _clock(day.moonrise, timezone),
        "moonset": _clock(day.moonset, timezone),
        "tithi": _entry(day.tithi, timezone, day.date, _tithi_label(day)),
        "nakshatra": _entry(day.nakshatra, timezone, day.date),
        "yoga": _entry(day.yoga, timezone, day.date),
        "karana": _karana_text(day, timezone),
        **_day_windows(day, timezone),
        "choghadiya": [_clock_entry(w, timezone) for w in day.choghadiya],
        "nightChoghadiya": _night_choghadiya(day, next_day, timezone),
        "eclipse": _eclipse(day, timezone),
        "yogas": list(day.special_yogas),
        "special": _specials(day),
    }


def _validate_consecutive_days(days):
    if any(
        right.date != left.date + timedelta(days=1) for left, right in pairwise(days)
    ):
        raise ValueError("Calendar days must be consecutive and ordered.")


def _validate_days(days, system):
    if not days:
        raise ValueError("Calendar data needs at least one day.")
    if any(day.system != system or day.location != days[0].location for day in days):
        raise ValueError("Calendar days must share a system and location.")
    _validate_consecutive_days(days)


def _display_events(days, system, raw_ics):
    # Only opaque display strings are carried over from the subscriber feed.
    # All structured values below are projected from the engine objects.
    calendar = Calendar.from_ical(raw_ics or ICSGenerator().generate(days, system))
    return {
        event.decoded("dtstart").strftime("%Y%m%d"): event
        for event in calendar.walk("VEVENT")
    }


def calendar_feed(days, system, raw_ics=None):
    _validate_days(days, system)
    events = _display_events(days, system, raw_ics)
    records = {}
    for day, next_day in zip(days, [*days[1:], None]):
        key = day.date.strftime("%Y%m%d")
        event = events[key]
        records[key] = {
            "summary": str(event["summary"]),
            "description": str(event["description"]),
            "day": day_view(day, next_day),
        }
    return {
        "schemaVersion": 1,
        "system": system,
        "city": days[0].location.name,
        "timezone": days[0].location.timezone,
        "days": records,
    }


def calendar_json(days, system, raw_ics=None):
    return json.dumps(
        calendar_feed(days, system, raw_ics), ensure_ascii=False, separators=(",", ":")
    )
