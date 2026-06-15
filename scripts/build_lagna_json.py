"""Builds lagna.json for the static site's daily-lagna ribbon.

Lagna (rising sign) depends on latitude, longitude, and the exact
local sunrise — so unlike gochara.json (rashi-level, Hyderabad-only),
this file is per-city. One JSON per city is written to
``public/feeds/<slug>-lagna.json``.

Format keeps the file small: for each day we store the rashi index
(0..11) at sunrise and a list of minute-offsets-from-sunrise where
the rising sign next changes, paired with the new rashi index.

    {
      "city": "Hyderabad",
      "start": "YYYY-MM-DD",
      "rasis": ["Mesha", "Vrishabha", ...],
      "days": [
        { "sunrise": "HH:MM", "lagna0": 2,
          "transitions": [[114, 3], [231, 4], ...] }
      ]
    }

Hora is NOT precomputed — the static site derives it client-side from
sunrise / sunset / next-sunrise (already in the ICS feed) since the
hora sequence is fixed by weekday lord.
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.base import RASHI_NAMES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.personal.lagna_hora import get_lagna_transitions

DAYS_AHEAD = 90  # ~3 months; the ICS feed window is longer but lagna
                 # changes meaningfully day-to-day, so we keep it tighter.


def _slug(name: str) -> str:
    return name.lower().replace(' ', '-').replace(',', '')


def _minute_of_day(dt, sunrise) -> int:
    """Minutes from sunrise (rounded). Used to keep the JSON compact —
    each transition is two ints instead of an ISO timestamp."""
    delta = dt - sunrise
    return int(round(delta.total_seconds() / 60))


def build_for_city(loc, start: date, days: int) -> dict:
    engine = DrikGanitaEngine()
    tz = ZoneInfo(loc.timezone)
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        day = engine.calculate(d, loc, include_eclipse=False)
        transitions = get_lagna_transitions(day)
        if not transitions:
            continue
        sunrise_local = day.sunrise.astimezone(tz)
        # First lagna covers sunrise; subsequent windows mark transitions.
        first = transitions[0]
        lagna0 = RASHI_NAMES.index(first.name.replace(' Lagna', ''))
        # Each transition: minutes-from-sunrise of the NEW lagna's start,
        # plus the new lagna's rashi index. Times are timezone-naive
        # offsets — the site adds them to the local-time sunrise.
        tx = []
        for w in transitions[1:]:
            new_idx = RASHI_NAMES.index(w.name.replace(' Lagna', ''))
            tx.append([_minute_of_day(w.start, day.sunrise), new_idx])
        rows.append({
            'date': d.isoformat(),
            'sunrise': sunrise_local.strftime('%H:%M'),
            'lagna0': lagna0,
            'transitions': tx,
        })
    return {
        'city': loc.name,
        'start': start.isoformat(),
        'rasis': RASHI_NAMES,
        'days': rows,
    }


def main() -> None:
    out_dir = os.environ.get('LAGNA_OUT', 'public/feeds')
    os.makedirs(out_dir, exist_ok=True)
    start = date.today().replace(day=1)
    for loc in CITIES:
        data = build_for_city(loc, start, DAYS_AHEAD)
        path = os.path.join(out_dir, f'{_slug(loc.name)}-lagna.json')
        with open(path, 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        print(f'Wrote {path}: {len(data["days"])} days')


if __name__ == '__main__':
    main()
