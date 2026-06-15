import re
with open('telugu_panchangam/engines/base.py', 'r') as f:
    content = f.read()

content = content.replace("class PanchangamEngine(ABC):\n", "from functools import lru_cache\n\nclass PanchangamEngine(ABC):\n")
content = content.replace("    def facts_at(self, dt: datetime, location: Location,\n", "    @lru_cache(maxsize=4096)\n    def facts_at(self, dt: datetime, location: Location,\n")

with open('telugu_panchangam/engines/base.py', 'w') as f:
    f.write(content)
