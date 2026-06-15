with open('telugu_panchangam/eclipses.py', 'r') as f:
    content = f.read()

content = content.replace("def _solar_visible(start_jd: float, end_jd: float, loc: Location) -> bool:", "from functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef _solar_visible(start_jd: float, end_jd: float, loc: Location) -> bool:")
content = content.replace("def _solar_eclipse(jd: float) -> Optional[tuple[float, float, str]]:", "@lru_cache(maxsize=128)\ndef _solar_eclipse(jd: float) -> Optional[tuple[float, float, str]]:")
content = content.replace("def _lunar_eclipse(jd: float) -> Optional[tuple[float, float, str]]:", "@lru_cache(maxsize=128)\ndef _lunar_eclipse(jd: float) -> Optional[tuple[float, float, str]]:")

# Loc hash fix
content = content.replace("@lru_cache(maxsize=128)\ndef _solar_visible(start_jd: float, end_jd: float, loc: Location) -> bool:",
"""@lru_cache(maxsize=128)
def _cached_solar_visible(start_jd: float, end_jd: float, lat: float, lon: float) -> bool:
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

def _solar_visible(start_jd: float, end_jd: float, loc: Location) -> bool:
    return _cached_solar_visible(start_jd, end_jd, loc.lat, loc.lon)""")

with open('telugu_panchangam/eclipses.py', 'w') as f:
    f.write(content)
