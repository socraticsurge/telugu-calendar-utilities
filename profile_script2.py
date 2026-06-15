from functools import lru_cache
import telugu_panchangam.engines.utils as utils

orig_moon_sun = utils.moon_sun_elongation

utils.moon_sun_elongation = lru_cache(maxsize=None)(orig_moon_sun)
utils.sun_longitude = lru_cache(maxsize=None)(utils.sun_longitude)
utils.moon_longitude = lru_cache(maxsize=None)(utils.moon_longitude)

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
print("moon_sun_elongation:", utils.moon_sun_elongation.cache_info())
print("sun_longitude:", utils.sun_longitude.cache_info())
print("moon_longitude:", utils.moon_longitude.cache_info())
