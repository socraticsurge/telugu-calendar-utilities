# src/generate.py
"""Entry point: generate all Panchangam ICS feeds."""
from datetime import date, timedelta
import os
import sys

from src.cities import CITIES
from src.engines.drik import DrikGanitaEngine
from src.engines.surya_siddhanta import SuryaSiddhantaEngine
from src.engines.vakya import VakyaEngine
from src.generators.ics import ICSGenerator

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
                days.append(engine.calculate(d, location))
                d += timedelta(days=1)

            raw = generator.generate(days, system)
            filename = f'{city_slug(location.name)}-{system.replace("_", "-")}.ics'
            path = os.path.join(output_dir, filename)
            with open(path, 'wb') as f:
                f.write(raw)


if __name__ == '__main__':
    today = date.today()
    start = date(today.year, today.month, 1)
    end_year = today.year + (today.month + 17) // 12
    end_month = (today.month + 17) % 12 or 12
    import calendar
    end_day = calendar.monthrange(end_year, end_month)[1]
    end = date(end_year, end_month, end_day)

    print(f'Generating feeds: {start} → {end}')
    generate_feeds(output_dir='feeds', start=start, end=end)
    print('Done.')
