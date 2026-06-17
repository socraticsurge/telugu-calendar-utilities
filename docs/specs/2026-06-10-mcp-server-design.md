# MCP Server (panchangam-mcp) Design

> **For agentic workers:** Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Publish `mcp-server-panchangam` to PyPI — a stdio MCP server exposing four tools for Panchangam calculations, usable by Claude Desktop, Claude Code, and any MCP-compatible AI agent via `uvx mcp-server-panchangam`.

**Architecture:** Thin MCP tool layer over the existing engines. No new calculation logic. Any city name accepted — predefined 22 cities resolve instantly, any other city geocodes via Nominatim + timezonefinder. All tool responses return JSON.

**Tech Stack:** `mcp>=1.0`, `pyswisseph`, `pytz`, `geopy`, `timezonefinder`, `setuptools`, `python-build`, PyPI Trusted Publishers

---

## Package Rename

`src/` is renamed to `telugu_panchangam/` as part of this work. The PyPI package name is `mcp-server-panchangam`. All imports across `src/` and `tests/` change from `from src.` to `from telugu_panchangam.`.

The `python -m src.generate` command becomes `python -m telugu_panchangam.generate`. The GitHub Actions `generate.yml` workflow is updated accordingly.

---

## File Structure

**New files:**
- `telugu_panchangam/mcp/__init__.py`
- `telugu_panchangam/mcp/server.py` — registers tools, `main()` entry point
- `telugu_panchangam/mcp/tools.py` — tool implementations
- `telugu_panchangam/mcp/location.py` — city name → (lat, lon, tz) resolution
- `pyproject.toml` — package metadata and entry point
- `.github/workflows/publish.yml` — publish to PyPI on version tag
- `tests/test_mcp_tools.py`
- `tests/test_mcp_location.py`

**Renamed (src/ → telugu_panchangam/):**
- All files under `src/` move to `telugu_panchangam/` with imports updated

**Modified:**
- All `tests/*.py` — `from src.` → `from telugu_panchangam.`
- `pytest.ini` — update testpaths if needed
- `.github/workflows/generate.yml` — `python -m src.generate` → `python -m telugu_panchangam.generate`
- `scripts/build_landing_page.py` — update imports
- `requirements.txt` — add `geopy`, `timezonefinder`

---

## Tools

### `list_supported_cities()`
No parameters. Returns the 22 pre-configured cities. An AI should call this first to get exact city names for the other tools, though any free-text city name is accepted.

**Response:**
```json
[
  {"name": "Hyderabad", "latitude": 17.385, "longitude": 78.487, "timezone": "Asia/Kolkata", "country": "India"},
  ...
]
```

---

### `get_panchangam(date, city, system)`
**Parameters:**
- `date` (str): ISO format `"YYYY-MM-DD"`
- `city` (str): city name — predefined name for instant lookup, or any free-text city for geocoded lookup
- `system` (str, default `"drik"`): `"drik"` | `"surya_siddhanta"` | `"vakya"`

**Response:**
```json
{
  "date": "2026-06-10",
  "city": "Hyderabad",
  "system": "drik",
  "metadata": {
    "samvatsara": "Jaya",
    "maasam": "Jyeshtha",
    "paksham": "Krishna",
    "vaaram": "Budhavaram",
    "solar_sign": "Vrishabha",
    "lunar_sign": "Vrischika"
  },
  "pancha_anga": {
    "tithi":     {"name": "Krishna Dashami",   "start": "03:25", "end": "05:49"},
    "nakshatra": {"name": "Uttara Bhadrapada", "start": "16:12", "end": "19:08"},
    "yoga":      {"name": "Ayushman",          "start": "05:24", "end": "06:19"},
    "karana":    [{"name": "Kaulava", "start": "03:25", "end": "16:37"}]
  },
  "sky": {
    "sunrise": "05:40", "sunset": "18:46", "moonrise": "19:49", "moonset": "06:04"
  },
  "auspicious": {
    "brahma_muhurta":  {"start": "04:04", "end": "04:52"},
    "abhijit_muhurta": {"start": "12:00", "end": "12:27"},
    "amrita_kalam":    [{"start": "20:12", "end": "20:16"}]
  },
  "inauspicious": {
    "rahu_kalam":   {"start": "07:19", "end": "08:57"},
    "gulika_kalam": {"start": "13:52", "end": "15:30"},
    "yamagandam":   {"start": "08:57", "end": "10:35"},
    "varjyam":      [{"start": "09:48", "end": "09:52"}],
    "durmuhurtham": [{"start": "08:18", "end": "08:44"}, {"start": "11:47", "end": "12:13"}]
  },
  "choghadiya": [
    {"name": "Amrit", "start": "05:40"},
    {"name": "Kaal",  "start": "07:19"}
  ],
  "special_days": [],
  "is_special": false
}
```

---

### `get_muhurta(date, city, system)`
Same parameters as `get_panchangam`. Returns only the auspicious and inauspicious windows — for "is this a good time?" queries without the full Pancha Anga overhead.

**Response:**
```json
{
  "date": "2026-06-10",
  "city": "Hyderabad",
  "system": "drik",
  "auspicious": {
    "brahma_muhurta":  {"start": "04:04", "end": "04:52"},
    "abhijit_muhurta": {"start": "12:00", "end": "12:27"},
    "amrita_kalam":    [{"start": "20:12", "end": "20:16"}]
  },
  "inauspicious": {
    "rahu_kalam":   {"start": "07:19", "end": "08:57"},
    "gulika_kalam": {"start": "13:52", "end": "15:30"},
    "yamagandam":   {"start": "08:57", "end": "10:35"},
    "varjyam":      [{"start": "09:48", "end": "09:52"}],
    "durmuhurtham": [{"start": "08:18", "end": "08:44"}, {"start": "11:47", "end": "12:13"}]
  }
}
```

---

### `get_special_days(year, month, city, system)`
**Parameters:**
- `year` (int): e.g. `2026`
- `month` (int): 1–12
- `city` (str): same as above
- `system` (str, default `"drik"`): same as above

Runs `engine.calculate()` for each day in the month, returns only days where `is_special=True`.

**Response:**
```json
{
  "year": 2026,
  "month": 6,
  "city": "Hyderabad",
  "system": "drik",
  "special_days": [
    {"date": "2026-06-06", "tithi": "Shukla Ekadashi",  "events": ["Ekadashi — fasting day"]},
    {"date": "2026-06-11", "tithi": "Shukla Pournami",  "events": ["Pournami"]},
    {"date": "2026-06-21", "tithi": "Krishna Ekadashi", "events": ["Ekadashi — fasting day"]},
    {"date": "2026-06-25", "tithi": "Krishna Amavasya", "events": ["Amavasya"]}
  ]
}
```

---

## Location Resolution (`location.py`)

```python
def resolve_location(city: str) -> tuple[float, float, str]:
    """Returns (latitude, longitude, timezone). Raises ValueError if unresolvable."""
```

Resolution order:
1. Case-insensitive match against the 22 predefined cities → instant, no network
2. Nominatim geocoder via `geopy` → lat/lon, then `timezonefinder` → timezone
3. If geocoding fails → raise `ValueError("Unknown city: '{city}'. Try list_supported_cities() for pre-configured cities.")`

All tools also accept explicit `latitude: float`, `longitude: float`, `timezone: str` parameters to bypass geocoding entirely.

---

## Error Responses

All errors return `{"error": "<message>"}`:

| Condition | Message |
|-----------|---------|
| Unknown city, geocoding failed | `"Unknown city: 'Xyz'. Call list_supported_cities() for pre-configured cities, or pass latitude/longitude/timezone directly."` |
| Bad date format | `"Invalid date 'abc'. Expected YYYY-MM-DD."` |
| Invalid system | `"Invalid system 'foo'. Must be one of: drik, surya_siddhanta, vakya."` |
| Invalid month | `"Invalid month 13. Must be 1–12."` |

---

## Packaging (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "mcp-server-panchangam"
version = "1.0.0"
description = "MCP server for Panchangam calculations — Tithi, Nakshatra, Yoga, Muhurtas for any city"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0",
    "pyswisseph>=2.10",
    "pytz",
    "geopy",
    "timezonefinder",
]

[project.scripts]
mcp-server-panchangam = "telugu_panchangam.mcp.server:main"

[tool.setuptools.packages.find]
include = ["telugu_panchangam*"]
```

---

## CI/CD (`.github/workflows/publish.yml`)

Triggers on `push` to tags matching `v*.*.*`. Uses PyPI Trusted Publishers (OIDC) — no API token secret needed, configured once on PyPI.

Steps: checkout → setup Python → install build → `python -m build` → publish via `pypa/gh-action-pypi-publish`.

---

## Testing

**`tests/test_mcp_tools.py`**
- `list_supported_cities()` → 22 entries, each has `name`, `latitude`, `longitude`, `timezone`, `country`
- `get_panchangam("2026-06-10", "Hyderabad", "drik")` → assert all top-level keys present, times are HH:MM strings
- `get_panchangam` with all 3 systems → no errors
- `get_muhurta("2026-06-10", "Hyderabad", "drik")` → has `auspicious` and `inauspicious`, no `pancha_anga`
- `get_special_days(2026, 6, "Hyderabad", "drik")` → list contains at least one entry, each has `date`, `tithi`, `events`
- Invalid date → `{"error": ...}`
- Invalid system → `{"error": ...}`

**`tests/test_mcp_location.py`**
- "Hyderabad" resolves to ~(17.38, 78.48, "Asia/Kolkata") without network call
- "hyderabad" (lowercase) resolves same as "Hyderabad"
- "London" geocodes via Nominatim to ~(51.5, -0.12, "Europe/London")
- "xyznotacity123" raises ValueError with helpful message
- Raw lat/lon/tz bypasses geocoding
