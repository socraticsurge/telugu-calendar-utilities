"""Thin serializers over the existing computation-tool contract."""

import json
from datetime import timedelta
from threading import Lock
from typing import Callable

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.utils import AYANAMSA_MODES
from telugu_panchangam.mcp.tools import (
    tool_find_muhurta,
    tool_find_tarabalam_days,
    tool_get_daily_horas,
    tool_get_lagna_transitions,
    tool_get_panchangam,
    tool_get_panchangam_range,
    tool_get_rasi_phalalu,
)
from telugu_panchangam.panchangam_names import NAKSHATRA_NAMES, RASHI_NAMES
from telugu_panchangam.personal.activity_rules import ACTIVITIES, get_activity_rules

# Swiss Ephemeris exposes process-global sidereal mode. FastAPI executes sync
# handlers in worker threads, so adapter calls are serialized inside one warm
# function instance to prevent cross-request ayanamsa contamination.
_COMPUTE_LOCK = Lock()


class CalculationError(RuntimeError):
    """A safe boundary error; raw tool errors are never sent to clients."""


def _decode(result: str) -> dict:
    try:
        payload = json.loads(result)
    except (TypeError, json.JSONDecodeError) as exc:
        raise CalculationError("invalid computation response") from exc
    if not isinstance(payload, dict) or "error" in payload:
        raise CalculationError("calculation rejected")
    return payload


def _call(tool: Callable[..., str], **kwargs) -> dict:
    return _decode(tool(**kwargs))


def catalog() -> dict:
    activities = []
    for key in ACTIVITIES:
        rules = get_activity_rules(key)
        activities.append({
            "id": key,
            "label": rules["label"],
            "manual_prerequisites": bool(rules.get("manual_prerequisites")),
        })
    return {
        "cities": [
            {
                "name": city.name,
                "latitude": city.lat,
                "longitude": city.lon,
                "timezone": city.timezone,
            }
            for city in CITIES
        ],
        "systems": ["drik", "surya_siddhanta", "vakya"],
        "ayanamsas": list(AYANAMSA_MODES),
        "rasis": list(RASHI_NAMES),
        "nakshatras": list(NAKSHATRA_NAMES),
        "activities": activities,
        "limits": {
            "panchangam_range_days": 31,
            "tarabalam_days": 90,
            "muhurtam_days": 14,
            "participants": 4,
            "request_bytes": 65536,
        },
    }


def panchangam_day(request) -> dict:
    common = request.location_kwargs()
    with _COMPUTE_LOCK:
        day = _call(
            tool_get_panchangam,
            date_str=request.date.isoformat(),
            system=request.system,
            ayanamsa=request.ayanamsa,
            **common,
        )
        horas = _call(
            tool_get_daily_horas,
            date_str=request.date.isoformat(),
            system=request.system,
            **common,
        )["horas"]
        lagnas = _call(
            tool_get_lagna_transitions,
            date_str=request.date.isoformat(),
            system=request.system,
            **common,
        )["lagnas"]
    day["horas"] = horas
    day["lagna_transitions"] = lagnas
    return day


def panchangam_range(request) -> dict:
    with _COMPUTE_LOCK:
        return _call(
            tool_get_panchangam_range,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            system=request.system,
            ayanamsa=request.ayanamsa,
            **request.location_kwargs(),
        )


def rasi_phalalu(request) -> dict:
    with _COMPUTE_LOCK:
        return _call(
            tool_get_rasi_phalalu,
            date_str=request.date.isoformat(),
            janma_rasi=request.janma_rasi,
            janma_nakshatra=request.janma_nakshatra,
            ayanamsa=request.ayanamsa,
            **request.location_kwargs(),
        )


def tarabalam(request) -> dict:
    stars = [participant.janma_nakshatra for participant in request.participants]
    rasis = [participant.janma_rasi for participant in request.participants]
    # The established MCP boundary is capped at 60 days. Preserve it and join
    # at most two canonical responses to provide the HTTP contract's 90 days.
    remaining = request.days
    start = request.start_date
    chunks = []
    with _COMPUTE_LOCK:
        while remaining:
            size = min(remaining, 60)
            chunks.append(_call(
                tool_find_tarabalam_days,
                janma_nakshatras=stars,
                janma_rasis=rasis,
                start_date=start.isoformat(),
                days=size,
                system=request.system,
                chandra_mode=request.chandra_mode,
                **request.location_kwargs(),
            ))
            remaining -= size
            start += timedelta(days=size)

    first = chunks[0]
    first["days"] = [day for chunk in chunks for day in chunk["days"]]
    first["good_for_all_dates"] = [
        day for chunk in chunks for day in chunk["good_for_all_dates"]
    ]
    first["participants"] = [participant.label for participant in request.participants]
    first["requested_days"] = request.days
    first["ayanamsa"] = "lahiri"
    return first


def muhurtam(request) -> dict:
    participants = request.participants
    kwargs = request.location_kwargs()
    kwargs.update({
        "start_date": request.start_date.isoformat(),
        "days": request.days,
        "activity": request.activity,
        "system": request.system,
        "ayanamsa": request.ayanamsa,
        "janma_nakshatras": [p.janma_nakshatra for p in participants] or None,
        "janma_rasis": [p.janma_rasi for p in participants] if participants else None,
        "janma_lagnas": [p.janma_lagna for p in participants] if participants else None,
        "chandra_mode": request.chandra_mode,
        "travel_direction": request.travel_direction,
        "include_night": request.include_night,
    })
    with _COMPUTE_LOCK:
        data = _call(tool_find_muhurta, **kwargs)
    data["participants"] = [participant.label for participant in participants]
    return data
