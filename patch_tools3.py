with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

content = content.replace("from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates", "from telugu_panchangam.mcp.location import resolve_location, timezone_for_coordinates\nfrom telugu_panchangam.engines.base import PanchangamEngine")
content = content.replace(
"""        for i in range(days):
            day = day_objects[i]""",
"""        # Create an engine proxy that uses our precalculated days
        class CachedEngineProxy:
            def __init__(self, engine, days_map):
                self.engine = engine
                self.days_map = days_map

            def facts_at(self, dt, location, vaaram=None):
                # The underlying engine's facts_at is still needed, but it shares the heavy SWE cache if we had one
                # Actually, day_slots does: facts = engine.facts_at(...)
                return self.engine.facts_at(dt, location, vaaram)

            def __getattr__(self, name):
                return getattr(self.engine, name)

        for i in range(days):
            day = day_objects[i]"""
)
with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
