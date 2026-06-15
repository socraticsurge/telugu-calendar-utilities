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
        import telugu_panchangam.eclipses as eclipses_module
        from functools import lru_cache

        orig_sidereal = engine_utils.sidereal_longitude
        engine_utils.sidereal_longitude = lru_cache(maxsize=16384)(orig_sidereal)

        orig_solar = eclipses_module._solar_eclipse
        eclipses_module._solar_eclipse = lru_cache(maxsize=128)(orig_solar)

        orig_lunar = eclipses_module._lunar_eclipse
        eclipses_module._lunar_eclipse = lru_cache(maxsize=128)(orig_lunar)

        orig_visible = eclipses_module._solar_visible
        @lru_cache(maxsize=128)
        def cached_visible(start_jd, end_jd, lat, lon):
            import swisseph as swe
            geopos = [lon, lat, 0.0]
            jd_check = start_jd
            step = (end_jd - start_jd) / 10.0
            for _ in range(11):
                res = swe.sol_eclipse_when_loc(jd_check - 1.0, swe.FLG_SWIEPH, geopos, backward=False)
                if res and res[1][0] >= start_jd and res[1][0] <= end_jd:
                    return True
                jd_check += step
            return False

        def proxied_visible(start_jd, end_jd, location):
            return cached_visible(start_jd, end_jd, location.lat, location.lon)

        eclipses_module._solar_visible = proxied_visible

        orig_facts_at = engine.facts_at

        @lru_cache(maxsize=4096)
        def cached_facts_at(dt_ts: float, loc_name: str, vaaram: str | None):
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(dt_ts, tz=timezone.utc)
            return orig_facts_at(dt, loc, vaaram=vaaram)

        def proxied_facts_at(dt, location, vaaram=None):
            return cached_facts_at(dt.timestamp(), location.name, vaaram)

        engine.facts_at = proxied_facts_at

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
            engine_utils.sidereal_longitude = orig_sidereal
            eclipses_module._solar_eclipse = orig_solar
            eclipses_module._lunar_eclipse = orig_lunar
            eclipses_module._solar_visible = orig_visible
            engine.facts_at = orig_facts_at"""

content = content.replace(orig_loop, new_loop)

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
