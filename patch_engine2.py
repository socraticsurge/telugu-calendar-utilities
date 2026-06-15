import re
with open('telugu_panchangam/engines/base.py', 'r') as f:
    content = f.read()

# Add lru_cache
content = content.replace("class PanchangamEngine(ABC):\n", "from functools import lru_cache\n\nclass PanchangamEngine(ABC):\n")

# Make facts_at use a cached private method instead
cache_method = """
    @lru_cache(maxsize=4096)
    def _cached_facts_at(self, dt: datetime, loc_name: str, loc_lat: float, loc_lon: float, loc_tz: str, vaaram: str | None) -> SlotFacts:
        location = Location(name=loc_name, lat=loc_lat, lon=loc_lon, timezone=loc_tz)
        return self._compute_facts_at(dt, location, vaaram)

    def facts_at(self, dt: datetime, location: Location, vaaram: str | None = None) -> SlotFacts:
        return self._cached_facts_at(dt, location.name, location.lat, location.lon, location.timezone, vaaram)

    def _compute_facts_at(self, dt: datetime, location: Location, vaaram: str | None = None) -> SlotFacts:
"""

content = content.replace("    def facts_at(self, dt: datetime, location: Location,\n                 vaaram: str | None = None) -> SlotFacts:\n", cache_method)
content = content.replace("        The vaaram of the panchangam day", "        \"\"\"Return the panchangam facts active at `dt` for this engine.\n\n        The vaaram of the panchangam day")
content = content.replace("    def facts_at(self, dt: datetime, location: Location, vaaram: str | None = None) -> SlotFacts:\n        return self._cached_facts_at(dt, location.name, location.lat, location.lon, location.timezone, vaaram)\n\n    def _compute_facts_at(self, dt: datetime, location: Location, vaaram: str | None = None) -> SlotFacts:\n        \"\"\"Return the panchangam facts active at `dt` for this engine.", "    def facts_at(self, dt: datetime, location: Location, vaaram: str | None = None) -> SlotFacts:\n        \"\"\"Return the panchangam facts active at `dt` for this engine.\n        \"\"\"\n        return self._cached_facts_at(dt, location.name, location.lat, location.lon, location.timezone, vaaram)\n\n    def _compute_facts_at(self, dt: datetime, location: Location, vaaram: str | None = None) -> SlotFacts:")

with open('telugu_panchangam/engines/base.py', 'w') as f:
    f.write(content)
