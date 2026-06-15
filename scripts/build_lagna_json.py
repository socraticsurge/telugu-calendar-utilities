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
        { "date": "YYYY-MM-DD",
          "sunrise": "HH:MM", "lagna0": 2,
          "transitions": [[114, 3], [231, 4], ...],
          "cycleEnd": 1438 }
      ]
    }

The site uses ``cycleEnd`` (minute-offset from sunrise to next
sunrise) to compute the end time of the last visible rashi instead
of showing a duplicated trailing wrap cell.

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
        leading_name = first.name
        lagna0 = RASHI_NAMES.index(leading_name.replace(' Lagna', ''))
        # Each transition: minutes-from-sunrise of the NEW lagna's start,
        # plus the new lagna's rashi index. Times are timezone-naive
        # offsets — the site adds them to the local-time sunrise.
        #
        # The cycle wraps back to the leading rashi ~22h after sunrise,
        # but the 24h panchangam-day slice can capture 13 OR 14 engine
        # windows depending on whether the cycle had time to advance
        # past the leading rashi into the next one before next sunrise
        # (sidereal day is ~23h56m, so a 24h window can hold ~1.003
        # cycles). Detecting the wrap by NAME (where the leading rashi
        # next appears) is robust to both cases; slicing by [1:-1] was
        # not, and left the wrap window visible on the 14-window days.
        wrap_idx = None
        for i in range(1, len(transitions)):
            if transitions[i].name == leading_name:
                wrap_idx = i
                break
        if wrap_idx is None:
            # No wrap detected — keep everything after the leading.
            wrap_idx = len(transitions)
        visible = transitions[1:wrap_idx]
        tx = []
        for w in visible:
            new_idx = RASHI_NAMES.index(w.name.replace(' Lagna', ''))
            tx.append([_minute_of_day(w.start, day.sunrise), new_idx])
        # cycleEnd is the START of the trailing wrap — i.e. when the
        # last visible rashi actually ends. After this offset the
        # ribbon stops (the trailing wrap and any overflow into the
        # next rashi are hidden; see the panchangam-day footnote).
        if wrap_idx < len(transitions):
            cycle_end = _minute_of_day(transitions[wrap_idx].start, day.sunrise)
        else:
            cycle_end = _minute_of_day(transitions[-1].end, day.sunrise)
        rows.append({
            'date': d.isoformat(),
            'sunrise': sunrise_local.strftime('%H:%M'),
            'lagna0': lagna0,
            'transitions': tx,
            'cycleEnd': cycle_end,
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
