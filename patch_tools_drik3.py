import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

content = content.replace("from functools import lru_cache\n        orig_sidereal = engine_utils.sidereal_longitude\n        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)",
"from functools import lru_cache\n        orig_sidereal = engine_utils.sidereal_longitude\n        engine_utils.sidereal_longitude = lru_cache(maxsize=None)(orig_sidereal)\n        orig_tropical = engine_utils.tropical_sun_longitude\n        engine_utils.tropical_sun_longitude = lru_cache(maxsize=None)(orig_tropical)")

content = content.replace("engine_utils.sidereal_longitude = orig_sidereal", "engine_utils.sidereal_longitude = orig_sidereal\n            engine_utils.tropical_sun_longitude = orig_tropical")

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
