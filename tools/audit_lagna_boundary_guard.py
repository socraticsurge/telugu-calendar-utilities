#!/usr/bin/env python3
"""Audit the published Lagna boundaries against DashaFlow's calculation.

The browser consumes minute-precision boundaries from ``lagna.json``.  The
election-chart sidecar derives Lagna with PySwissEph ``houses_ex`` in sidereal
Lahiri mode.  Those two legitimate calculations can disagree briefly at a
sign boundary, so chart screening uses a five-minute review band around every
published transition.

This tool makes the safety margin reproducible without importing DashaFlow:
the function used here is the exact Ascendant primitive and flags used by
DashaFlow's ``calculate_vedic_chart`` implementation.  It audits the 15th of
every month from 2025 through 2032 for every supported city.

Run from the repository root:

    python tools/audit_lagna_boundary_guard.py \
      --verify tests/fixtures/lagna-boundary-guard-audit.json

Omit ``--verify`` to print a freshly computed report as JSON.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from itertools import pairwise
from pathlib import Path
from time import perf_counter
from typing import Any
from zoneinfo import ZoneInfo

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The audit is also an executable repository tool, so the root path must be
# available before these project imports. Keep the exception local and explicit.
from scripts.build_lagna_json import build_for_city  # noqa: E402
from telugu_panchangam.cities import CITIES  # noqa: E402
from telugu_panchangam.panchangam_names import RASHI_NAMES  # noqa: E402

AUDIT_SCHEMA_VERSION = 1
START_YEAR = 2025
END_YEAR = 2032
SAMPLE_DAY = 15
GUARD_MINUTES = 5
FIRST_NEW_MINUTE_LIMIT = 2
SEARCH_RADIUS_MINUTES = GUARD_MINUTES
SIGN_TRANSITIONS_PER_CYCLE = 12

_DASHA_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED


def sample_dates() -> list[date]:
    """Return the fixed monthly audit grid."""

    return [
        date(year, month, SAMPLE_DAY)
        for year in range(START_YEAR, END_YEAR + 1)
        for month in range(1, 13)
    ]


def dashaflow_lagna_index(instant: datetime, latitude: float, longitude: float) -> int:
    """Return DashaFlow's sidereal-Lahiri Whole Sign Lagna index.

    DashaFlow converts the requested instant to UTC and calls
    ``swe.houses_ex(jd, lat, lon, b'W', FLG_SIDEREAL | FLG_SPEED)``.  We keep
    this small projection local so the audit does not depend on the sidecar
    package or network access.
    """

    utc = instant.astimezone(timezone.utc)
    utc_hour = (
        utc.hour
        + utc.minute / 60.0
        + utc.second / 3600.0
        + utc.microsecond / 3_600_000_000.0
    )
    julian_day = swe.julday(utc.year, utc.month, utc.day, utc_hour)
    _, ascmc = swe.houses_ex(
        julian_day,
        latitude,
        longitude,
        b'W',
        _DASHA_FLAGS,
    )
    return int(ascmc[0] / 30.0) % 12


def published_transition_instant(
    sampled_date: date,
    sunrise_text: str,
    minute_offset: int,
    timezone_name: str,
) -> datetime:
    """Recreate the exact minute instant used by the browser artifact."""

    local_sunrise = datetime.combine(
        sampled_date,
        time.fromisoformat(sunrise_text),
        tzinfo=ZoneInfo(timezone_name),
    )
    return local_sunrise + timedelta(minutes=minute_offset)


def first_new_minute_offset(
    published_transition: datetime,
    new_lagna_index: int,
    latitude: float,
    longitude: float,
) -> int | None:
    """Find the first T..T+2 minute carrying the published new Lagna."""

    for offset in range(FIRST_NEW_MINUTE_LIMIT + 1):
        instant = published_transition + timedelta(minutes=offset)
        if dashaflow_lagna_index(instant, latitude, longitude) == new_lagna_index:
            return offset
    return None


def continuous_boundary_delta_minutes(
    published_transition: datetime,
    new_lagna_index: int,
    latitude: float,
    longitude: float,
) -> float:
    """Locate the matching DashaFlow boundary within the five-minute band.

    The Lagna cannot traverse more than one sign in this ten-minute bracket.
    Bisection stops below one millisecond, far tighter than the minute-level
    product decision.
    """

    low = published_transition - timedelta(minutes=SEARCH_RADIUS_MINUTES)
    high = published_transition + timedelta(minutes=SEARCH_RADIUS_MINUTES)
    low_sign = dashaflow_lagna_index(low, latitude, longitude)
    high_sign = dashaflow_lagna_index(high, latitude, longitude)
    if low_sign == new_lagna_index or high_sign != new_lagna_index:
        raise AssertionError(
            'DashaFlow Lagna did not cross the expected published boundary '
            f'within +/-{SEARCH_RADIUS_MINUTES} minutes'
        )

    while (high - low).total_seconds() > 0.001:
        midpoint = low + (high - low) / 2
        if dashaflow_lagna_index(midpoint, latitude, longitude) == new_lagna_index:
            high = midpoint
        else:
            low = midpoint

    return (high - published_transition).total_seconds() / 60.0


def _rounded(value: float) -> float:
    return round(value, 6)


def generate_report(
    *,
    cities: list[Any] | None = None,
    dates: list[date] | None = None,
) -> dict[str, Any]:
    """Run the audit and return its stable, serialisable report."""

    selected_cities = list(CITIES if cities is None else cities)
    selected_dates = sample_dates() if dates is None else dates
    started = perf_counter()
    first_new_offsets: Counter[int] = Counter()
    transition_count = 0
    max_abs_delta = -1.0
    max_case: dict[str, Any] | None = None
    min_internal_dwell = math.inf
    min_dwell_case: dict[str, Any] | None = None

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    for city in selected_cities:
        for sampled_date in selected_dates:
            artifact = build_for_city(city, sampled_date, 1)
            if len(artifact['days']) != 1:
                raise AssertionError(
                    f'{city.name} {sampled_date}: expected exactly one artifact day'
                )
            day = artifact['days'][0]
            transitions = day['transitions']
            if len(transitions) < SIGN_TRANSITIONS_PER_CYCLE:
                raise AssertionError(
                    f'{city.name} {sampled_date}: artifact supplied only '
                    f'{len(transitions)} Lagna transitions'
                )
            # A sidereal day can expose a trailing wrap transition and the
            # generator's sunrise search can expose more than one cycle.  The
            # first 12 sign advances are one complete zodiac cycle and give
            # every distinct boundary exactly once for each city-date.
            audited_transitions = transitions[:SIGN_TRANSITIONS_PER_CYCLE]

            internal_offsets = [offset for offset, _ in audited_transitions]
            for previous, current in pairwise(internal_offsets):
                dwell = current - previous
                if dwell < min_internal_dwell:
                    min_internal_dwell = dwell
                    min_dwell_case = {
                        'city': city.name,
                        'date': sampled_date.isoformat(),
                        'minutes': dwell,
                        'from_offset': previous,
                        'to_offset': current,
                    }

            for minute_offset, new_lagna_index in audited_transitions:
                transition_count += 1
                published = published_transition_instant(
                    sampled_date,
                    day['sunrise'],
                    minute_offset,
                    city.timezone,
                )
                first_offset = first_new_minute_offset(
                    published,
                    new_lagna_index,
                    city.lat,
                    city.lon,
                )
                if first_offset is None:
                    raise AssertionError(
                        f'{city.name} {sampled_date} {published.isoformat()}: '
                        f'{RASHI_NAMES[new_lagna_index]} was not reached by T+2'
                    )
                first_new_offsets[first_offset] += 1

                delta = continuous_boundary_delta_minutes(
                    published,
                    new_lagna_index,
                    city.lat,
                    city.lon,
                )
                if abs(delta) > max_abs_delta:
                    max_abs_delta = abs(delta)
                    max_case = {
                        'city': city.name,
                        'date': sampled_date.isoformat(),
                        'published_local': published.isoformat(),
                        'published_new_lagna': RASHI_NAMES[new_lagna_index],
                        'dashaflow_delta_minutes': _rounded(delta),
                    }

    if max_case is None or min_dwell_case is None:
        raise AssertionError('audit scope did not contain Lagna transitions')

    elapsed = perf_counter() - started
    max_abs_delta = _rounded(max_abs_delta)
    return {
        'schema_version': AUDIT_SCHEMA_VERSION,
        'method': {
            'artifact_generator': 'scripts.build_lagna_json.build_for_city',
            'published_boundary': (
                'local HH:MM sunrise plus the emitted integer minute offset'
            ),
            'comparison': (
                "PySwissEph swe.houses_ex(jd, lat, lon, b'W', "
                'FLG_SIDEREAL | FLG_SPEED) with SIDM_LAHIRI'
            ),
            'relationship_to_sidecar': (
                'Matches the Ascendant primitive and flags in '
                'DashaFlow calculate_vedic_chart'
            ),
            'dashaflow_reference_version': '1.1.0',
            'continuous_search_resolution_seconds': 0.001,
            'transition_selection': (
                'first 12 emitted sign advances: one complete zodiac cycle '
                'with each distinct Lagna boundary represented once'
            ),
        },
        'scope': {
            'city_count': len(selected_cities),
            'cities': [city.name for city in selected_cities],
            'date_start': selected_dates[0].isoformat(),
            'date_end': selected_dates[-1].isoformat(),
            'date_pattern': '15th of every month, inclusive',
            'sampled_date_count': len(selected_dates),
            'city_date_count': len(selected_cities) * len(selected_dates),
            'sign_transitions_per_city_date': SIGN_TRANSITIONS_PER_CYCLE,
        },
        'guard': {
            'review_band_minutes_each_side': GUARD_MINUTES,
            'first_new_lagna_deadline_minutes': FIRST_NEW_MINUTE_LIMIT,
        },
        'results': {
            'transition_count': transition_count,
            'first_new_minute_offsets': {
                str(offset): first_new_offsets[offset]
                for offset in range(FIRST_NEW_MINUTE_LIMIT + 1)
            },
            'transitions_after_t_plus_2': 0,
            'max_abs_boundary_delta_minutes': max_abs_delta,
            'guard_margin_minutes': _rounded(GUARD_MINUTES - max_abs_delta),
            'max_delta_case': max_case,
            'minimum_internal_dwell_minutes': int(min_internal_dwell),
            'minimum_internal_dwell_case': min_dwell_case,
        },
        # Runtime varies by machine and is deliberately informational.  It is
        # excluded from fixture equality in verification mode.
        'runtime_seconds': _rounded(elapsed),
    }


def _without_runtime(report: dict[str, Any]) -> dict[str, Any]:
    stable = dict(report)
    stable.pop('runtime_seconds', None)
    return stable


def repository_fixture_path(value: str) -> Path:
    """Resolve an existing fixture without allowing a repository escape."""

    supplied = Path(value)
    try:
        candidate = (
            supplied if supplied.is_absolute() else ROOT / supplied
        ).resolve(strict=True)
    except OSError as error:
        raise argparse.ArgumentTypeError(
            f'Fixture does not exist: {value}'
        ) from error

    try:
        candidate.relative_to(ROOT)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            'Fixture must resolve to a file inside the repository.'
        ) from error
    if not candidate.is_file():
        raise argparse.ArgumentTypeError(f'Fixture is not a file: {value}')
    return candidate


def verify_fixture(actual: dict[str, Any], fixture_path: Path) -> None:
    expected = json.loads(fixture_path.read_text(encoding='utf-8'))
    if _without_runtime(actual) != _without_runtime(expected):
        print('Lagna boundary audit fixture is stale.', file=sys.stderr)
        print(json.dumps(actual, indent=2), file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--verify',
        type=repository_fixture_path,
        help='Compare stable audit fields with the committed JSON report.',
    )
    args = parser.parse_args()
    report = generate_report()
    if args.verify:
        verify_fixture(report, args.verify)
        print(
            'Lagna boundary guard audit passed: '
            f'{report["scope"]["city_date_count"]} city-dates, '
            f'{report["results"]["transition_count"]} transitions, '
            f'max delta {report["results"]["max_abs_boundary_delta_minutes"]} min '
            f'in {report["runtime_seconds"]} s.'
        )
    else:
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
