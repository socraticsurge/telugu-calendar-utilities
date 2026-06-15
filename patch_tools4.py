with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

content = content.replace("from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates", "from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates\nfrom functools import lru_cache")

# Wrap engine.facts_at in a cached function within tool_find_muhurta
repl_target = """        engine = _ENGINES[system]
        tz = loc.timezone

        slots = []"""
repl_with = """        engine = _ENGINES[system]
        tz = loc.timezone

        # Cache engine.facts_at for the duration of this request
        # This mitigates N+1 computation of identical overlapping astronomical data
        orig_facts_at = engine.facts_at

        @lru_cache(maxsize=None)
        def cached_facts_at(dt_ts, loc_name, vaaram):
            dt = datetime.fromtimestamp(dt_ts, tz=pytz.UTC)
            return orig_facts_at(dt, loc, vaaram=vaaram)

        class CachedEngine:
            def facts_at(self, dt, location, vaaram=None):
                return cached_facts_at(dt.timestamp(), location.name, vaaram)
            def calculate(self, *args, **kwargs):
                return engine.calculate(*args, **kwargs)

        cached_engine = CachedEngine()

        slots = []"""

content = content.replace(repl_target, repl_with)

content = content.replace("day = engine.calculate(start + timedelta(days=i), loc, include_eclipse=True)", "day = cached_engine.calculate(start + timedelta(days=i), loc, include_eclipse=True)")
content = content.replace("engine=engine)", "engine=cached_engine)")

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
