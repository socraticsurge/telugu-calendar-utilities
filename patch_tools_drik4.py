import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

content = content.replace("orig_tropical = engine_utils.tropical_sun_longitude\n        engine_utils.tropical_sun_longitude = lru_cache(maxsize=None)(orig_tropical)",
"orig_tropical = engine_utils.tropical_sun_longitude\n        engine_utils.tropical_sun_longitude = lru_cache(maxsize=None)(orig_tropical)\n        orig_facts_at = engine.facts_at\n        engine.facts_at = lru_cache(maxsize=None)(orig_facts_at)")

content = content.replace("engine_utils.tropical_sun_longitude = orig_tropical", "engine_utils.tropical_sun_longitude = orig_tropical\n            engine.facts_at = orig_facts_at")

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
