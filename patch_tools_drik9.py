import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

orig_loop = """        import telugu_panchangam.engines.utils as engine_utils
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

        engine.facts_at = proxied_facts_at"""

new_loop = """        import telugu_panchangam.engines.utils as engine_utils
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

        # NOTE: get_eclipse_for_date receives geopos as a list, which is unhashable.
        orig_get_eclipse = eclipses_module.get_eclipse_for_date

        @lru_cache(maxsize=128)
        def cached_get_eclipse(d_iso, lat, lon):
            from datetime import date
            loc = _resolve_city(city, latitude, longitude, timezone) # just dummy
            return orig_get_eclipse(date.fromisoformat(d_iso), loc)

        def proxied_get_eclipse(d, location):
            return cached_get_eclipse(d.isoformat(), location.lat, location.lon)

        eclipses_module.get_eclipse_for_date = proxied_get_eclipse

        orig_facts_at = engine.facts_at

        @lru_cache(maxsize=4096)
        def cached_facts_at(dt_ts: float, loc_name: str, vaaram: str | None):
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(dt_ts, tz=timezone.utc)
            return orig_facts_at(dt, loc, vaaram=vaaram)

        def proxied_facts_at(dt, location, vaaram=None):
            return cached_facts_at(dt.timestamp(), location.name, vaaram)

        engine.facts_at = proxied_facts_at"""

content = content.replace(orig_loop, new_loop)

end_loop = """        finally:
            engine_utils.sidereal_longitude = orig_sidereal
            eclipses_module._solar_eclipse = orig_solar
            eclipses_module._lunar_eclipse = orig_lunar
            eclipses_module._solar_visible = orig_visible
            engine.facts_at = orig_facts_at"""

new_end_loop = """        finally:
            engine_utils.sidereal_longitude = orig_sidereal
            eclipses_module._solar_eclipse = orig_solar
            eclipses_module._lunar_eclipse = orig_lunar
            eclipses_module._solar_visible = orig_visible
            eclipses_module.get_eclipse_for_date = orig_get_eclipse
            engine.facts_at = orig_facts_at"""

content = content.replace(end_loop, new_end_loop)

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
