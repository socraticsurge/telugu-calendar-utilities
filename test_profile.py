import cProfile
import pstats
from telugu_panchangam.mcp.tools import tool_find_muhurta

def run():
    tool_find_muhurta(
        start_date='2024-05-01',
        days=14,
        activity='wedding',
        city='Hyderabad',
        system='drik',
        janma_nakshatras=['Ashvini'],
        janma_rasis=['Mesha']
    )

cProfile.run('run()', 'stats')
p = pstats.Stats('stats')
p.sort_stats('cumtime').print_stats(30)
