from datetime import datetime, date
from functools import lru_cache
from telugu_panchangam.cities import CITIES
from telugu_panchangam.mcp.tools import tool_find_muhurta
import time

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
print(f"No cache time: {time.time() - start_time:.4f}s")
