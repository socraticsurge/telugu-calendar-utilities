"""Lossless run-length encoding of selected-engine facts at every UTC minute.

This is a discrete candidate-start contract, not an interpolation of continuous
transition instants. Every represented minute is evaluated, including minutes on
either side of a model discontinuity. Frozen engines remain the public owners.
"""
from datetime import timedelta, timezone

from telugu_panchangam.cities import CITIES
from telugu_panchangam.personal.homa import solar_nakshatra_at

FIELDS = ('nakshatra', 'tithi', 'yoga', 'karana', 'lunar_sign', 'solar_nakshatra')


def _epoch_minute(instant):
    if instant.tzinfo is None or instant.timestamp() % 60:
        raise ValueError('Slot-fact bounds must identify a whole UTC minute')
    return int(instant.timestamp() // 60)


def _values_at(engine, instant):
    facts = engine.facts_at(instant, CITIES[0], vaaram='Somavaram')
    return [
        *(getattr(facts, field) for field in FIELDS[:-1]),
        solar_nakshatra_at(instant, engine),
    ]


def build_slot_fact_table(engine, system, start, end):
    """Encode [start, end), querying every minute; special Yogas use caller vara."""
    start_minute, end_minute = _epoch_minute(start), _epoch_minute(end)
    if end_minute <= start_minute:
        raise ValueError('Slot-fact range must contain at least one minute')
    start = start.astimezone(timezone.utc)
    rows = []
    previous = None
    for offset in range(end_minute - start_minute):
        values = _values_at(engine, start + timedelta(minutes=offset))
        if values != previous:
            rows.append([offset, *values])
            previous = values
    return {
        'schemaVersion': 1,
        'system': system,
        'startMinute': start_minute,
        'endMinute': end_minute,
        'stepSeconds': 60,
        'fields': list(FIELDS),
        'rows': rows,
    }
