import re
with open('telugu_panchangam/engines/drik.py', 'r') as f:
    content = f.read()

content = content.replace("class DrikGanitaEngine(PanchangamEngine):", "from functools import lru_cache\n\nclass DrikGanitaEngine(PanchangamEngine):")

# Rename calculate to _compute_calculate and add a cached version
calc_start = "    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:"
calc_repl = """
    @lru_cache(maxsize=2048)
    def _cached_calculate(self, d_iso: str, loc_name: str, loc_lat: float, loc_lon: float, loc_tz: str, include_eclipse: bool) -> PanchangamDay:
        d = date.fromisoformat(d_iso)
        location = Location(name=loc_name, lat=loc_lat, lon=loc_lon, timezone=loc_tz)
        return self._compute_calculate(d, location, include_eclipse)

    def calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
        return self._cached_calculate(d.isoformat(), location.name, location.lat, location.lon, location.timezone, include_eclipse)

    def _compute_calculate(self, d: date, location: Location, include_eclipse: bool = True) -> PanchangamDay:
"""
content = content.replace(calc_start, calc_repl)

with open('telugu_panchangam/engines/drik.py', 'w') as f:
    f.write(content)
