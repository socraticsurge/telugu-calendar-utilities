# src/generate.py
"""Entry point: generate all Panchangam ICS feeds."""
from datetime import date, timedelta
import os
import sys

from telugu_panchangam.cities import CITIES
from telugu_panchangam.eclipses import list_eclipses_in_range, get_eclipse_from_precomputed
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.engines.utils import local_midnight_jd
from telugu_panchangam.generators.ics import ICSGenerator

ENGINES = {
    'drik': DrikGanitaEngine,
    'surya_siddhanta': SuryaSiddhantaEngine,
    'vakya': VakyaEngine,
}


def city_slug(name: str) -> str:
    return name.lower().replace(' ', '-').replace(',', '')


def generate_feeds(
    output_dir: str,
    start: date,
    end: date,
    systems: list[str] | None = None,
    city_names: list[str] | None = None,
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    systems = systems or list(ENGINES.keys())
    locations = [c for c in CITIES if city_names is None or c.name in city_names]
    generator = ICSGenerator()

    jd_start = local_midnight_jd(start - timedelta(days=1), 'Asia/Kolkata')
    jd_end = local_midnight_jd(end + timedelta(days=2), 'UTC')
    print('  Pre-computing eclipses for the generation window...')
    precomputed_eclipses = list_eclipses_in_range(jd_start, jd_end)
    print(f'  Found {len(precomputed_eclipses)} eclipse(s).')

    for system in systems:
        if system not in ENGINES:
            print(f'Unknown system: {system}', file=sys.stderr)
            continue
        engine = ENGINES[system]()
        for location in locations:
            print(f'  Generating {location.name} / {system}...')
            days = []
            d = start
            while d <= end:
                day = engine.calculate(d, location, include_eclipse=False)
                day.eclipse = get_eclipse_from_precomputed(d, precomputed_eclipses, location)
                days.append(day)
                d += timedelta(days=1)

            raw = generator.generate(days, system)
            filename = f'{city_slug(location.name)}-{system.replace("_", "-")}.ics'
            path = os.path.join(output_dir, filename)
            with open(path, 'wb') as f:
                f.write(raw)


def default_feed_window(today: date) -> tuple[date, date]:
    """Feed window: 1st of the current month through the last day of month +17."""
    import calendar
    start = date(today.year, today.month, 1)
    months_from_epoch = today.year * 12 + (today.month - 1) + 17
    end_year, end_month = months_from_epoch // 12, months_from_epoch % 12 + 1
    end = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
    return start, end


if __name__ == '__main__':
    start, end = default_feed_window(date.today())
    print(f'Generating feeds: {start} → {end}')
    generate_feeds(output_dir='feeds', start=start, end=end)
    print('Done.')
