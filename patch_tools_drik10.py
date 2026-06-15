import re
with open('telugu_panchangam/mcp/tools.py', 'r') as f:
    content = f.read()

content = content.replace("loc = _resolve_city(city, latitude, longitude, timezone) # just dummy", "")
content = content.replace("return orig_get_eclipse(date.fromisoformat(d_iso), loc)", "return orig_get_eclipse(date.fromisoformat(d_iso), Location(name=city, lat=lat, lon=lon, timezone=timezone))")
content = content.replace("eclipses_module.get_eclipse_for_date = proxied_get_eclipse", "eclipses_module.get_eclipse_for_date = proxied_get_eclipse\n        \n        orig_visible_inner = eclipses_module._solar_visible\n        @lru_cache(maxsize=128)\n        def cached_visible_inner(start_jd, end_jd, lat, lon):\n            import swisseph as swe\n            geopos = [lon, lat, 0.0]\n            jd_check = start_jd\n            step = (end_jd - start_jd) / 10.0\n            for _ in range(11):\n                res = swe.sol_eclipse_when_loc(jd_check - 1.0, swe.FLG_SWIEPH, geopos, backward=False)\n                if res and res[1][0] >= start_jd and res[1][0] <= end_jd:\n                    return True\n                jd_check += step\n            return False\n        eclipses_module._solar_visible = lambda start_jd, end_jd, loc: cached_visible_inner(start_jd, end_jd, loc.lat, loc.lon)")

with open('telugu_panchangam/mcp/tools.py', 'w') as f:
    f.write(content)
