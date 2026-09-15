"""Search orchestration over the existing, protected engine outputs.

No MCP, JSON serialization, presentation text or result truncation belongs here.
"""

from datetime import date, timedelta

import pytz

from telugu_panchangam.eclipses import (
    get_eclipse_from_precomputed,
    list_eclipses_in_range,
)
from telugu_panchangam.engines.utils import local_midnight_jd
from telugu_panchangam.models.panchangam_day import Location
from telugu_panchangam.personal.activity_rules import get_activity_rules
from telugu_panchangam.personal.muhurta import (
    TIER_NAMES,
    assign_tiers,
    day_slots,
    diagnose_day,
    karnavedha_daylight_assessment,
    night_slots,
)
from telugu_panchangam.personal.search_contract import (
    SearchOptions,
    SearchPeriod,
    SearchResult,
)


def _calculate_days(start: date, count: int, location: Location, engine):
    first = local_midnight_jd(start, location.timezone)
    last = local_midnight_jd(start + timedelta(days=count), location.timezone)
    eclipses = list_eclipses_in_range(first, last)
    days = []
    for index in range(count):
        current = start + timedelta(days=index)
        day = engine.calculate(current, location, include_eclipse=False)
        day.eclipse = get_eclipse_from_precomputed(current, eclipses, location)
        days.append(day)
    return days


def _day_results(day, next_day, options: SearchOptions, engine):
    assessment = None
    if options.activity == "karnavedha":
        assessment = karnavedha_daylight_assessment(
            day, get_activity_rules(options.activity), options.activity
        )
    arguments = options.slot_arguments()
    slots = day_slots(day, **arguments, engine=engine, _daylight_assessment=assessment)
    if options.include_night:
        slots += night_slots(day, next_day, **arguments, engine=engine)
    return slots, assessment


def _dropped_day(day, options: SearchOptions, assessment):
    arguments = options.slot_arguments()
    arguments.pop("janma_lagnas")  # Diagnostics intentionally use the existing API.
    reason = diagnose_day(day, **arguments, _daylight_assessment=assessment)
    if not reason:
        return None
    dropped = {"date": day.date.isoformat(), "reason": reason}
    if assessment is not None:
        dropped["daylight_outcomes"] = assessment["outcomes"]
    return dropped


def _collect_results(calculated, options, engine):
    result = SearchResult()
    search_days = calculated[:-1] if options.include_night else calculated
    for day, next_day in zip(search_days, [*calculated[1:], None]):
        slots, assessment = _day_results(day, next_day, options, engine)
        if not slots:
            dropped = _dropped_day(day, options, assessment)
            if dropped is not None:
                result.dropped_days.append(dropped)
        result.slots.extend(slots)
    return result


def search_muhurta(
    period: SearchPeriod, location: Location, engine, options: SearchOptions
) -> SearchResult:
    """Return all ranked candidates; callers choose their display limit.

    Ties preserve the established local clock ordering, including night slots.
    Sorting by absolute instant instead would silently change the legacy API.
    """
    if not 1 <= period.days <= 14:
        raise ValueError("days must be between 1 and 14.")
    calculated = _calculate_days(
        period.start, period.days + int(options.include_night), location, engine
    )
    result = _collect_results(calculated, options, engine)
    assign_tiers(result.slots)
    timezone = pytz.timezone(location.timezone)
    result.slots.sort(
        key=lambda slot: (
            -TIER_NAMES.index(slot["tier"]),
            -slot["score"],
            slot["personal_dosha"] is not None,
            slot["date"],
            slot["start"].astimezone(timezone).strftime("%H:%M"),
        )
    )
    return result
