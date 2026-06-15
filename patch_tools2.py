import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

# I also want to cache engine.facts_at for this specific call since it uses `unhashable type: 'Location'`.
# So I'll override `facts_at` on the `engine` object directly (just for the instance).

orig_loop = """        slots = []
        dropped_days = []

        import telugu_panchangam.engines.utils as engine_utils
        from functools import lru_cache
        orig_sidereal = engine_utils.sidereal_longitude
        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)

        try:
            for i in range(days):"""

new_loop = """        slots = []
        dropped_days = []

        import telugu_panchangam.engines.utils as engine_utils
        from functools import lru_cache
        orig_sidereal = engine_utils.sidereal_longitude
        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)

        orig_facts_at = engine.facts_at

        @lru_cache(maxsize=4096)
        def cached_facts_at(dt_ts: float, loc_name: str, vaaram: str | None):
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(dt_ts, tz=timezone.utc)
            return orig_facts_at(dt, loc, vaaram=vaaram)

        def proxied_facts_at(dt, location, vaaram=None):
            return cached_facts_at(dt.timestamp(), location.name, vaaram)

        engine.facts_at = proxied_facts_at

        try:
            for i in range(days):"""

content = content.replace(orig_loop, new_loop)

end_loop = """        finally:
            engine_utils.sidereal_longitude = orig_sidereal"""

new_end_loop = """        finally:
            engine_utils.sidereal_longitude = orig_sidereal
            engine.facts_at = orig_facts_at"""

content = content.replace(end_loop, new_end_loop)

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
