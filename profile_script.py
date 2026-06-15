from functools import lru_cache
import telugu_panchangam.engines.utils as utils

orig_sidereal = utils.sidereal_longitude

hits = 0
misses = 0

def mocked_sidereal(jd, planet):
    global hits, misses
    # Let's check exact match
    return orig_sidereal(jd, planet)

utils.sidereal_longitude = lru_cache(maxsize=None)(orig_sidereal)

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
print(utils.sidereal_longitude.cache_info())
