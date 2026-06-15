import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

orig_loop = """        slots = []
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

new_loop = """        slots = []
        dropped_days = []

        import telugu_panchangam.engines.utils as engine_utils
        from functools import lru_cache
        orig_sidereal = engine_utils.sidereal_longitude
        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)

        orig_facts = engine.facts_at
        @lru_cache(maxsize=None)
        def cached_facts_at(dt_ts: float, loc_name: str, vaaram: str | None):
            return orig_facts(datetime.fromtimestamp(dt_ts, tz=pytz.UTC), loc, vaaram=vaaram)

        class EngineProxy:
            def facts_at(self, dt: datetime, location: Location, vaaram: str | None = None):
                return cached_facts_at(dt.timestamp(), location.name, vaaram)
            def calculate(self, *args, **kwargs):
                return engine.calculate(*args, **kwargs)

        engine_proxy = EngineProxy()

        try:
            for i in range(days):
                day = engine_proxy.calculate(start + timedelta(days=i), loc, include_eclipse=True)
                day_results = day_slots(day, activity=activity,
                                        janma_nakshatras=janma_nakshatras,
                                        janma_rasis=janma_rasis,
                                        chandra_mode=chandra_mode,
                                        engine=engine_proxy)
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

content = content.replace(orig_loop, new_loop)

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
