import re

with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

orig_block = """        slots = []
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
                              'end': _fmt_time(s['end'], tz)})"""

new_block = """        slots = []
        dropped_days = []

        # Optimization: locally cache astronomical computations during this 14-day sweep
        import telugu_panchangam.engines.utils as engine_utils
        from functools import lru_cache
        orig_sidereal = engine_utils.sidereal_longitude
        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)

        try:
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
            engine_utils.sidereal_longitude = orig_sidereal"""

content = content.replace(orig_block, new_block)

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
