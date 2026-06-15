from functools import lru_cache
import telugu_panchangam.engines.base as base

orig_facts_at = base.PanchangamEngine.facts_at

base.PanchangamEngine.facts_at = lru_cache(maxsize=None)(orig_facts_at)

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
print("facts_at:", base.PanchangamEngine.facts_at.cache_info())
