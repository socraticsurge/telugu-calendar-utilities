"""Builds gochara.json: daily graha rasis for the static site's Gochara tab.

Positions are taken at Hyderabad sunrise (rasi-level data varies by
minutes across cities — far below the one-day resolution shown).
Format keeps the file small; the page derives ingress dates by scanning:

    { "start": "YYYY-MM-DD", "days": [[rasiIdx*9 ints], ...],
      "retro": [[9 bools], ...], "grahas": [names] }
"""
import json
import os
from datetime import date, timedelta

from telugu_panchangam.panchangam_names import RASHI_NAMES
from telugu_panchangam.engines.utils import get_sunrise, local_midnight_jd
from telugu_panchangam.gochara.positions import graha_positions, GRAHA_NAMES

HYD_GEO = [78.4744, 17.3850, 0.0]
DAYS_AHEAD = 550  # ~18 months, matching the feed window


def build(start: date, days: int) -> dict:
    day_rows, retro_rows = [], []
    for i in range(days):
        d = start + timedelta(days=i)
        jd = get_sunrise(local_midnight_jd(d, 'Asia/Kolkata'), HYD_GEO)
        positions = graha_positions(jd)
        day_rows.append([RASHI_NAMES.index(p['rasi']) for p in positions])
        retro_rows.append([1 if p['retrograde'] else 0 for p in positions])
    return {
        'start': start.isoformat(),
        'grahas': GRAHA_NAMES,
        'rasis': RASHI_NAMES,
        'days': day_rows,
        'retro': retro_rows,
    }


if __name__ == '__main__':
    out_dir = os.environ.get('GOCHARA_OUT', 'public')
    os.makedirs(out_dir, exist_ok=True)
    data = build(date.today().replace(day=1), DAYS_AHEAD)
    path = os.path.join(out_dir, 'gochara.json')
    with open(path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print(f'Wrote {path}: {len(data["days"])} days from {data["start"]}')
