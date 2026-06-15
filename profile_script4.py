import functools
import telugu_panchangam.engines.utils as utils

orig_sidereal = utils.sidereal_longitude

def cached_sidereal():
    cache = {}
    def wrapper(jd, planet):
        key = (jd, planet)
        if key not in cache:
            cache[key] = orig_sidereal(jd, planet)
        return cache[key]
    wrapper.cache = cache
    return wrapper

utils.sidereal_longitude = cached_sidereal()

import time
from telugu_panchangam.mcp.tools import tool_find_muhurta

start_time = time.time()
res = tool_find_muhurta(
    start_date='2024-05-01',
    days=14,
    activity='wedding',
    city='Hyderabad',
    system='drik',
    janma_nakshatras=['Ashvini'],
    janma_rasis=['Mesha']
)
end_time = time.time()

print(f"Time taken: {end_time - start_time:.4f} seconds")
print(f"Cache size: {len(utils.sidereal_longitude.cache)}")
