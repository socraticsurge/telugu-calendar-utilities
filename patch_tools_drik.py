import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

content = content.replace("        engine = _ENGINES[system]\n        tz = loc.timezone\n\n        slots = []",
"""        engine = _ENGINES[system]
        tz = loc.timezone

        # Cache sidereal_longitude during this API call to avoid N+1 computation
        import telugu_panchangam.engines.utils as engine_utils
        from functools import lru_cache
        orig_sidereal = engine_utils.sidereal_longitude
        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)

        try:
            slots = []
            dropped_days = []
            for i in range(days):
                day = engine.calculate(start + timedelta(days=i), loc, include_eclipse=True)
                day_results = day_slots(day, activity=activity,
                                        janma_nakshatras=janma_nakshatras,
                                        janma_rasis=janma_rasis,
                                        chandra_mode=chandra_mode,
                                        engine=engine)
                if not day_results:
                    reason = diagnose_day(day, activity=activity,
                                          janma_nakshatras=janma_nakshatras,
                                          janma_rasis=janma_rasis,
                                          chandra_mode=chandra_mode)
                    if reason:
                        dropped_days.append({'date': day.date.isoformat(), 'reason': reason})
                for s in day_results:
                    slots.append({**s, 'start': _fmt_time(s['start'], tz),
                                  'end': _fmt_time(s['end'], tz)})
        finally:
            # Restore original function
            engine_utils.sidereal_longitude = orig_sidereal

        # Re-tier across the whole search, not just one day""")

# remove original loop
content = re.sub(r"        slots = \[\].*?assign_tiers\(slots\)", "        assign_tiers(slots)", content, flags=re.DOTALL)

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
