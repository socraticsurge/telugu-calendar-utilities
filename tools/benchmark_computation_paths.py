#!/usr/bin/env python3
"""Measure existing engine bulk and slot-fact paths without changing them.

This is a comparison aid, not a CI performance threshold. Results depend on
hardware, Python and cache warmth; architecture decisions should record the
environment and compare like with like.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from datetime import date, timedelta
from pathlib import Path
from statistics import median
from time import perf_counter

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine

ROOT = Path(__file__).resolve().parents[1]

_ENGINES = {
    'drik': DrikGanitaEngine,
    'surya_siddhanta': SuryaSiddhantaEngine,
    'vakya': VakyaEngine,
}


def _source_commit() -> str:
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def benchmark(
    start: date,
    days: int = 30,
    runs: int = 3,
    facts_per_day: int = 4,
) -> dict:
    """Return timings for all three existing engines on Hyderabad data."""
    if days < 1 or runs < 1 or facts_per_day < 1:
        raise ValueError('days, runs and facts_per_day must all be positive')
    location = next(city for city in CITIES if city.name == 'Hyderabad')
    systems = []
    for system, engine_class in _ENGINES.items():
        engine = engine_class()
        bulk_runs = []
        calculated_days = []
        for _ in range(runs):
            started = perf_counter()
            calculated_days = engine.calculate_bulk(
                start, days, location, include_eclipse=False,
            )
            bulk_runs.append(perf_counter() - started)

        offsets = [24 * index / facts_per_day for index in range(facts_per_day)]
        started = perf_counter()
        for calculated_day in calculated_days:
            for offset in offsets:
                engine.facts_at(
                    calculated_day.sunrise + timedelta(hours=offset),
                    location,
                    vaaram=calculated_day.vaaram,
                )
        facts_seconds = perf_counter() - started
        warm_runs = bulk_runs[1:] or bulk_runs
        systems.append({
            'system': system,
            'bulk_seconds_by_run': [round(value, 6) for value in bulk_runs],
            'bulk_warm_median_seconds': round(median(warm_runs), 6),
            'facts_evaluations': days * facts_per_day,
            'facts_seconds': round(facts_seconds, 6),
        })
    return {
        'source_commit': _source_commit(),
        'environment': {
            'python': platform.python_version(),
            'platform': platform.platform(),
        },
        'parameters': {
            'start': start.isoformat(),
            'days': days,
            'runs': runs,
            'facts_per_day': facts_per_day,
            'location': location.name,
            'include_eclipse': False,
        },
        'systems': systems,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=date.fromisoformat, default=date(2026, 1, 1))
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--facts-per-day', type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(benchmark(
        args.start, args.days, args.runs, args.facts_per_day,
    ), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
