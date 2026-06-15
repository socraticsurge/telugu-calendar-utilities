import re
with open('telugu_panchangam/engines/utils.py', 'r') as f:
    content = f.read()

content = content.replace("import pytz\n", "import pytz\nfrom functools import lru_cache\n")
content = content.replace("def sidereal_longitude(jd: float, planet: int) -> float:\n", "@lru_cache(maxsize=16384)\ndef sidereal_longitude(jd: float, planet: int) -> float:\n")
content = content.replace("def tropical_sun_longitude(jd: float) -> float:\n", "@lru_cache(maxsize=4096)\ndef tropical_sun_longitude(jd: float) -> float:\n")

with open('telugu_panchangam/engines/utils.py', 'w') as f:
    f.write(content)
