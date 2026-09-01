import re
from pathlib import Path

from telugu_panchangam.cities import CITIES

ROOT = Path(__file__).parents[1]


def test_browser_city_locations_match_python_authority():
    source = (ROOT / 'src' / 'data' / 'cities.ts').read_text(encoding='utf-8')
    for city in CITIES:
        escaped = re.escape(city.name)
        if ' ' in city.name:
            escaped = rf"'{escaped}'"
        pattern = (
            rf'{escaped}: \{{ latitude: {city.lat:.4f}, longitude: {city.lon:.4f}, '
            rf"timezone: '{re.escape(city.timezone)}' \}}"
        )
        assert re.search(pattern, source), city.name
