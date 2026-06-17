# MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish `mcp-server-panchangam` to PyPI — a stdio MCP server with four tools (list_supported_cities, get_panchangam, get_muhurta, get_special_days) that any MCP-compatible AI agent can use.

**Architecture:** Rename `src/` → `telugu_panchangam/`, add an `mcp/` subpackage with location resolution (predefined cities + Nominatim fallback), tool functions returning JSON strings, and a FastMCP server entry point. Package via `pyproject.toml`, publish to PyPI on version tag via GitHub Actions Trusted Publishers.

**Tech Stack:** `mcp>=1.0` (FastMCP), `pyswisseph`, `pytz`, `geopy`, `timezonefinder`, `setuptools`, `python-build`, PyPI Trusted Publishers (OIDC)

---

## File Map

**Rename:**
- `src/` → `telugu_panchangam/` (all files move, all `from src.` imports become `from telugu_panchangam.`)

**Create:**
- `telugu_panchangam/mcp/__init__.py`
- `telugu_panchangam/mcp/location.py` — city name → (lat, lon, tz); predefined 22 cities + Nominatim fallback
- `telugu_panchangam/mcp/tools.py` — four tool functions returning JSON strings
- `telugu_panchangam/mcp/server.py` — FastMCP server, registers tools, `main()` entry point
- `pyproject.toml` — package metadata and `mcp-server-panchangam` entry point
- `.github/workflows/publish.yml` — publish to PyPI on `v*.*.*` tags
- `tests/test_mcp_location.py`
- `tests/test_mcp_tools.py`

**Modify:**
- `.github/workflows/generate.yml` line 29: `python -m src.generate` → `python -m telugu_panchangam.generate`
- `requirements.txt` — add `geopy`, `timezonefinder`, `mcp`

---

## Task 1: Rename src/ → telugu_panchangam/

**Files:**
- Rename: `src/` → `telugu_panchangam/`
- Modify: all `*.py` files in `telugu_panchangam/` and `tests/`
- Modify: `.github/workflows/generate.yml`

- [ ] **Step 1: Rename the directory**

```bash
git mv src telugu_panchangam
```

- [ ] **Step 2: Update all internal imports**

```bash
find telugu_panchangam tests -name "*.py" -exec sed -i '' 's/from src\./from telugu_panchangam./g' {} \;
find telugu_panchangam tests -name "*.py" -exec sed -i '' 's/import src\./import telugu_panchangam./g' {} \;
```

- [ ] **Step 3: Update the CI workflow**

In `.github/workflows/generate.yml` line 29, change:
```yaml
      - name: Generate feeds
        run: python -m src.generate
```
to:
```yaml
      - name: Generate feeds
        run: python -m telugu_panchangam.generate
```

- [ ] **Step 4: Run the full test suite to confirm nothing broke**

```bash
python -m pytest tests/ -q
```

Expected: `120 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: rename src/ to telugu_panchangam/ for PyPI packaging"
```

---

## Task 2: pyproject.toml and updated dependencies

**Files:**
- Create: `pyproject.toml`
- Modify: `requirements.txt`

- [ ] **Step 1: Add new dependencies to requirements.txt**

Append these three lines to `requirements.txt`:
```
geopy
timezonefinder
mcp>=1.0
```

- [ ] **Step 2: Install new deps**

```bash
pip install -r requirements.txt
```

Expected: geopy, timezonefinder, and mcp install successfully.

- [ ] **Step 3: Create pyproject.toml**

Create `pyproject.toml` at the project root with this exact content:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-server-panchangam"
version = "1.0.0"
description = "MCP server for Panchangam calculations — Tithi, Nakshatra, Yoga, Muhurtas for any city"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
keywords = ["panchangam", "vedic", "astrology", "mcp", "calendar"]
dependencies = [
    "mcp>=1.0",
    "pyswisseph>=2.10",
    "pytz",
    "geopy",
    "timezonefinder",
    "icalendar",
]

[project.scripts]
mcp-server-panchangam = "telugu_panchangam.mcp.server:main"

[tool.setuptools.packages.find]
include = ["telugu_panchangam*"]
```

- [ ] **Step 4: Verify the package builds**

```bash
pip install build
python -m build --wheel
```

Expected: `dist/mcp_server_panchangam-1.0.0-py3-none-any.whl` created successfully.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "build: add pyproject.toml for mcp-server-panchangam PyPI package"
```

---

## Task 3: Location resolution

**Files:**
- Create: `telugu_panchangam/mcp/__init__.py`
- Create: `telugu_panchangam/mcp/location.py`
- Create: `tests/test_mcp_location.py`

- [ ] **Step 1: Create the mcp package init**

Create `telugu_panchangam/mcp/__init__.py` as an empty file:
```bash
touch telugu_panchangam/mcp/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_mcp_location.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def test_predefined_city_resolves_without_network():
    from telugu_panchangam.mcp.location import resolve_location
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc:
        lat, lon, tz = resolve_location('Hyderabad')
        mock_gc.geocode.assert_not_called()
    assert abs(lat - 17.385) < 0.01
    assert abs(lon - 78.487) < 0.01
    assert tz == 'Asia/Kolkata'


def test_predefined_city_case_insensitive():
    from telugu_panchangam.mcp.location import resolve_location
    lat, lon, tz = resolve_location('hyderabad')
    assert tz == 'Asia/Kolkata'


def test_predefined_city_london():
    from telugu_panchangam.mcp.location import resolve_location
    lat, lon, tz = resolve_location('London')
    assert abs(lat - 51.507) < 0.01
    assert tz == 'Europe/London'


def test_unknown_city_uses_nominatim():
    from telugu_panchangam.mcp.location import resolve_location
    mock_loc = MagicMock()
    mock_loc.latitude = 51.5074
    mock_loc.longitude = -0.1278
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc, \
         patch('telugu_panchangam.mcp.location._TF') as mock_tf:
        mock_gc.geocode.return_value = mock_loc
        mock_tf.timezone_at.return_value = 'Europe/London'
        lat, lon, tz = resolve_location('Some Unknown City')
    assert lat == 51.5074
    assert lon == -0.1278
    assert tz == 'Europe/London'


def test_unresolvable_city_raises_value_error():
    from telugu_panchangam.mcp.location import resolve_location
    with patch('telugu_panchangam.mcp.location._GEOCODER') as mock_gc:
        mock_gc.geocode.return_value = None
        with pytest.raises(ValueError, match="Unknown city"):
            resolve_location('xyznotacity123abc')
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
python -m pytest tests/test_mcp_location.py -v
```

Expected: `ModuleNotFoundError: No module named 'telugu_panchangam.mcp.location'`

- [ ] **Step 4: Implement location.py**

Create `telugu_panchangam/mcp/location.py`:

```python
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from telugu_panchangam.cities import CITIES

_TF = TimezoneFinder()
_GEOCODER = Nominatim(user_agent='mcp-server-panchangam', timeout=10)


def resolve_location(city: str) -> tuple[float, float, str]:
    """Return (latitude, longitude, timezone) for a city name.

    Checks the 22 pre-configured cities first (case-insensitive, no network).
    Falls back to Nominatim geocoding + timezonefinder for any other city.
    Raises ValueError if the city cannot be resolved.
    """
    for c in CITIES:
        if c.name.lower() == city.lower():
            return c.lat, c.lon, c.timezone

    location = _GEOCODER.geocode(city)
    if location is None:
        raise ValueError(
            f"Unknown city: '{city}'. Call list_supported_cities() for pre-configured cities, "
            "or pass latitude/longitude/timezone directly."
        )

    tz = _TF.timezone_at(lat=location.latitude, lng=location.longitude)
    if tz is None:
        raise ValueError(f"Could not determine timezone for '{city}'.")

    return location.latitude, location.longitude, tz
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
python -m pytest tests/test_mcp_location.py -v
```

Expected: `5 passed`

- [ ] **Step 6: Commit**

```bash
git add telugu_panchangam/mcp/__init__.py telugu_panchangam/mcp/location.py tests/test_mcp_location.py
git commit -m "feat: add MCP location resolver with predefined cities and Nominatim fallback"
```

---

## Task 4: MCP tool functions

**Files:**
- Create: `telugu_panchangam/mcp/tools.py`
- Create: `tests/test_mcp_tools.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_mcp_tools.py`:

```python
import json
import pytest


def test_list_supported_cities_count():
    from telugu_panchangam.mcp.tools import tool_list_supported_cities
    result = json.loads(tool_list_supported_cities())
    assert len(result) == 22


def test_list_supported_cities_fields():
    from telugu_panchangam.mcp.tools import tool_list_supported_cities
    cities = json.loads(tool_list_supported_cities())
    for c in cities:
        assert 'name' in c
        assert 'latitude' in c
        assert 'longitude' in c
        assert 'timezone' in c
        assert 'country' in c


def test_get_panchangam_top_level_keys():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    for key in ('date', 'city', 'system', 'metadata', 'pancha_anga',
                'sky', 'auspicious', 'inauspicious', 'choghadiya',
                'special_days', 'is_special'):
        assert key in result, f"Missing key: {key}"


def test_get_panchangam_times_are_hhmm():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    sunrise = result['sky']['sunrise']
    assert len(sunrise) == 5
    assert sunrise[2] == ':'


def test_get_panchangam_metadata_fields():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    meta = result['metadata']
    for field in ('samvatsara', 'ayanam', 'rituvu', 'maasam', 'paksham', 'vaaram', 'solar_sign', 'lunar_sign'):
        assert field in meta, f"Missing metadata field: {field}"


def test_get_panchangam_all_three_systems():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    for system in ('drik', 'surya_siddhanta', 'vakya'):
        result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', system))
        assert 'error' not in result
        assert result['system'] == system


def test_get_muhurta_has_only_windows():
    from telugu_panchangam.mcp.tools import tool_get_muhurta
    result = json.loads(tool_get_muhurta('2026-06-10', 'Hyderabad', 'drik'))
    assert 'auspicious' in result
    assert 'inauspicious' in result
    assert 'pancha_anga' not in result
    assert 'metadata' not in result
    assert 'choghadiya' not in result


def test_get_muhurta_auspicious_keys():
    from telugu_panchangam.mcp.tools import tool_get_muhurta
    result = json.loads(tool_get_muhurta('2026-06-10', 'Hyderabad', 'drik'))
    assert 'brahma_muhurta' in result['auspicious']
    assert 'amrita_kalam' in result['auspicious']
    assert 'rahu_kalam' in result['inauspicious']
    assert 'gulika_kalam' in result['inauspicious']


def test_get_special_days_structure():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 6, 'Hyderabad', 'drik'))
    assert 'special_days' in result
    assert isinstance(result['special_days'], list)
    assert len(result['special_days']) > 0


def test_get_special_days_entry_fields():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 6, 'Hyderabad', 'drik'))
    for day in result['special_days']:
        assert 'date' in day
        assert 'tithi' in day
        assert 'events' in day
        assert isinstance(day['events'], list)


def test_get_panchangam_invalid_date():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('not-a-date', 'Hyderabad', 'drik'))
    assert 'error' in result
    assert 'YYYY-MM-DD' in result['error']


def test_get_panchangam_invalid_system():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'bad_system'))
    assert 'error' in result
    assert 'drik' in result['error']


def test_get_special_days_invalid_month():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 13, 'Hyderabad', 'drik'))
    assert 'error' in result
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_mcp_tools.py -v
```

Expected: `ModuleNotFoundError: No module named 'telugu_panchangam.mcp.tools'`

- [ ] **Step 3: Implement tools.py**

Create `telugu_panchangam/mcp/tools.py`:

```python
import json
import calendar
from datetime import date, datetime
from typing import Optional

import pytz

from telugu_panchangam.cities import CITIES
from telugu_panchangam.engines.drik import DrikGanitaEngine
from telugu_panchangam.engines.surya_siddhanta import SuryaSiddhantaEngine
from telugu_panchangam.engines.vakya import VakyaEngine
from telugu_panchangam.models.panchangam_day import Location, PanchangamDay
from telugu_panchangam.mcp.location import resolve_location

_ENGINES = {
    'drik': DrikGanitaEngine(),
    'surya_siddhanta': SuryaSiddhantaEngine(),
    'vakya': VakyaEngine(),
}

_TIMEZONE_COUNTRY = {
    'Asia/Kolkata': 'India',
    'America/Chicago': 'USA',
    'America/Los_Angeles': 'USA',
    'America/New_York': 'USA',
    'Europe/London': 'UK',
    'Australia/Sydney': 'Australia',
    'Asia/Dubai': 'UAE',
}


def _parse_date(date_str: str) -> date:
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date '{date_str}'. Expected YYYY-MM-DD.")


def _validate_system(system: str) -> None:
    if system not in _ENGINES:
        raise ValueError(
            f"Invalid system '{system}'. Must be one of: drik, surya_siddhanta, vakya."
        )


def _resolve_city(
    city: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
) -> Location:
    if latitude is not None and longitude is not None and timezone is not None:
        return Location(name=city or 'Custom', lat=float(latitude), lon=float(longitude), timezone=timezone)
    lat, lon, tz = resolve_location(city)
    return Location(name=city, lat=lat, lon=lon, timezone=tz)


def _fmt_time(dt: datetime, tz_str: str) -> str:
    return dt.astimezone(pytz.timezone(tz_str)).strftime('%H:%M')


def _span_to_dict(span, tz: str) -> dict:
    return {
        'name': span.name,
        'start': _fmt_time(span.start, tz),
        'end': _fmt_time(span.end, tz),
    }


def _window_to_dict(window, tz: str) -> dict:
    return {
        'start': _fmt_time(window.start, tz),
        'end': _fmt_time(window.end, tz),
    }


def _special_events(day: PanchangamDay) -> list[str]:
    events = []
    if day.is_ekadashi:         events.append('Ekadashi — fasting day')
    if day.is_amavasya:         events.append('Amavasya')
    if day.is_pournami:         events.append('Pournami')
    if day.is_shani_pradosham:  events.append('Shani Pradosham')
    elif day.is_soma_pradosham: events.append('Soma Pradosham')
    elif day.is_pradosham:      events.append('Pradosham')
    if day.is_sankranti:        events.append('Sankranti')
    return events


def tool_list_supported_cities() -> str:
    return json.dumps([
        {
            'name': c.name,
            'latitude': c.lat,
            'longitude': c.lon,
            'timezone': c.timezone,
            'country': _TIMEZONE_COUNTRY.get(c.timezone, 'Unknown'),
        }
        for c in CITIES
    ])


def tool_get_panchangam(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        d = _parse_date(date_str)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        day = _ENGINES[system].calculate(d, loc)
        tz = loc.timezone
        specials = _special_events(day)
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'metadata': {
                'samvatsara': day.samvatsara,
                'ayanam': day.ayanam,
                'rituvu': day.rituvu,
                'maasam': day.maasam,
                'paksham': day.paksham,
                'vaaram': day.vaaram,
                'solar_sign': day.solar_sign,
                'lunar_sign': day.lunar_sign,
            },
            'pancha_anga': {
                'tithi':     _span_to_dict(day.tithi, tz),
                'nakshatra': _span_to_dict(day.nakshatra, tz),
                'yoga':      _span_to_dict(day.yoga, tz),
                'karana':    [_span_to_dict(k, tz) for k in day.karana],
            },
            'sky': {
                'sunrise':  _fmt_time(day.sunrise, tz),
                'sunset':   _fmt_time(day.sunset, tz),
                'moonrise': _fmt_time(day.moonrise, tz),
                'moonset':  _fmt_time(day.moonset, tz),
            },
            'auspicious': {
                'brahma_muhurta':  _window_to_dict(day.brahma_muhurta, tz),
                'abhijit_muhurta': _window_to_dict(day.abhijit_muhurta, tz) if day.abhijit_muhurta else None,
                'amrita_kalam':    [_window_to_dict(w, tz) for w in day.amrita_kalam],
            },
            'inauspicious': {
                'rahu_kalam':   _window_to_dict(day.rahu_kalam, tz),
                'gulika_kalam': _window_to_dict(day.gulika_kalam, tz),
                'yamagandam':   _window_to_dict(day.yamagandam, tz),
                'varjyam':      [_window_to_dict(w, tz) for w in day.varjyam],
                'durmuhurtham': [_window_to_dict(w, tz) for w in day.durmuhurtham],
            },
            'choghadiya': [
                {'name': w.name, 'start': _fmt_time(w.start, tz)}
                for w in day.choghadiya
            ],
            'special_days': specials,
            'is_special': bool(specials),
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})


def tool_get_muhurta(
    date_str: str,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        d = _parse_date(date_str)
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        day = _ENGINES[system].calculate(d, loc)
        tz = loc.timezone
        return json.dumps({
            'date': date_str,
            'city': city,
            'system': system,
            'auspicious': {
                'brahma_muhurta':  _window_to_dict(day.brahma_muhurta, tz),
                'abhijit_muhurta': _window_to_dict(day.abhijit_muhurta, tz) if day.abhijit_muhurta else None,
                'amrita_kalam':    [_window_to_dict(w, tz) for w in day.amrita_kalam],
            },
            'inauspicious': {
                'rahu_kalam':   _window_to_dict(day.rahu_kalam, tz),
                'gulika_kalam': _window_to_dict(day.gulika_kalam, tz),
                'yamagandam':   _window_to_dict(day.yamagandam, tz),
                'varjyam':      [_window_to_dict(w, tz) for w in day.varjyam],
                'durmuhurtham': [_window_to_dict(w, tz) for w in day.durmuhurtham],
            },
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})


def tool_get_special_days(
    year: int,
    month: int,
    city: str,
    system: str = 'drik',
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None,
) -> str:
    try:
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid month {month}. Must be 1–12.")
        _validate_system(system)
        loc = _resolve_city(city, latitude, longitude, timezone)
        engine = _ENGINES[system]
        _, days_in_month = calendar.monthrange(year, month)
        special_days = []
        for day_num in range(1, days_in_month + 1):
            d = date(year, month, day_num)
            day = engine.calculate(d, loc)
            events = _special_events(day)
            if events:
                special_days.append({
                    'date': d.isoformat(),
                    'tithi': day.tithi.name,
                    'events': events,
                })
        return json.dumps({
            'year': year,
            'month': month,
            'city': city,
            'system': system,
            'special_days': special_days,
        })
    except ValueError as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': f'Calculation failed: {e}'})
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_mcp_tools.py -v
```

Expected: `13 passed`

- [ ] **Step 5: Run full suite to confirm no regressions**

```bash
python -m pytest tests/ -q
```

Expected: `138 passed` (120 existing + 5 location + 13 tools)

- [ ] **Step 6: Commit**

```bash
git add telugu_panchangam/mcp/tools.py tests/test_mcp_tools.py
git commit -m "feat: add MCP tool functions for panchangam, muhurta, and special days"
```

---

## Task 5: MCP server entry point

**Files:**
- Create: `telugu_panchangam/mcp/server.py`

No test file for the server itself — the tool functions are already tested. This task just wires FastMCP to the tools and verifies the entry point works.

- [ ] **Step 1: Create server.py**

Create `telugu_panchangam/mcp/server.py`:

```python
from mcp.server.fastmcp import FastMCP

from telugu_panchangam.mcp.tools import (
    tool_list_supported_cities,
    tool_get_panchangam,
    tool_get_muhurta,
    tool_get_special_days,
)

mcp = FastMCP('mcp-server-panchangam')


@mcp.tool()
def list_supported_cities() -> str:
    """Returns a JSON list of 22 pre-configured cities with name, latitude, longitude, timezone, and country. Call this first to discover valid city names."""
    return tool_list_supported_cities()


@mcp.tool()
def get_panchangam(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns full Panchangam JSON for a date and city: Pancha Anga (Tithi, Nakshatra, Yoga, Karana), sky events (Sunrise, Sunset, Moonrise, Moonset), auspicious windows (Brahma Muhurta, Abhijit, Amrita Kalam), inauspicious windows (Rahu Kalam, Gulika, Yamagandam, Varjyam, Durmuhurtham), Choghadiya, and special day flags. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude+timezone for a custom location), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_panchangam(date, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_muhurta(
    date: str,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns auspicious and inauspicious time windows for a date and city as JSON. Lighter than get_panchangam — use for quick 'is this a good time?' queries. Args: date=YYYY-MM-DD, city=city name (or pass latitude+longitude+timezone), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_muhurta(date, city, system, latitude, longitude, timezone)


@mcp.tool()
def get_special_days(
    year: int,
    month: int,
    city: str,
    system: str = 'drik',
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> str:
    """Returns a JSON list of special days in a given month: Ekadashi (fasting days), Amavasya (new moon), Pournami (full moon), Pradosham, and Sankranti. Args: year=e.g. 2026, month=1-12, city=city name (or pass latitude+longitude+timezone), system=drik|surya_siddhanta|vakya (default: drik)."""
    return tool_get_special_days(year, month, city, system, latitude, longitude, timezone)


def main() -> None:
    mcp.run()
```

- [ ] **Step 2: Verify the entry point is importable and main() exists**

```bash
python -c "from telugu_panchangam.mcp.server import main; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Verify the package entry point works via pip install**

```bash
pip install -e .
mcp-server-panchangam --help 2>&1 | head -5 || echo "entry point reachable"
```

Expected: Either help text or "entry point reachable" (FastMCP does not expose --help but the command should be found).

- [ ] **Step 4: Commit**

```bash
git add telugu_panchangam/mcp/server.py
git commit -m "feat: add FastMCP server entry point for mcp-server-panchangam"
```

---

## Task 6: CI publish workflow

**Files:**
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Create publish.yml**

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install build tools
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 2: Set up PyPI Trusted Publisher (one-time manual step)**

This must be done once on PyPI before the first publish. Steps:
1. Go to https://pypi.org and create an account (or log in)
2. Go to Account Settings → Publishing → Add a new publisher
3. Fill in:
   - **PyPI Project Name:** `mcp-server-panchangam`
   - **Owner:** `socraticsurge`
   - **Repository:** `telugu-calendar-utilities`
   - **Workflow filename:** `publish.yml`
   - **Environment:** `pypi`
4. Click Add

No API token or secret is needed after this. The OIDC token from GitHub Actions is used automatically.

- [ ] **Step 3: Commit the workflow**

```bash
git add .github/workflows/publish.yml
git commit -m "ci: add PyPI publish workflow triggered on version tags"
```

---

## Task 7: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add MCP Server section to README**

Open `README.md` and insert a new `## MCP Server` section after the `## Calculation Systems` table and before `## How it works`. The new section:

```markdown
## MCP Server

`mcp-server-panchangam` is available on PyPI. Add it to any MCP-compatible AI assistant in one step.

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "panchangam": {
      "command": "uvx",
      "args": ["mcp-server-panchangam"]
    }
  }
}
```

**Claude Code** — run once:

```bash
claude mcp add panchangam -- uvx mcp-server-panchangam
```

### Available tools

| Tool | Description |
|------|-------------|
| `list_supported_cities` | 22 pre-configured cities with lat/lon/timezone |
| `get_panchangam` | Full Panchangam for any date and city |
| `get_muhurta` | Auspicious/inauspicious windows only |
| `get_special_days` | Ekadashi, Amavasya, Pournami, Pradosham, Sankranti for a month |

All tools accept any free-text city name. Pre-configured cities resolve instantly; any other city is geocoded via OpenStreetMap. You can also pass `latitude`, `longitude`, and `timezone` directly.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add MCP server installation and usage section to README"
```

---

## Task 8: First publish to PyPI

- [ ] **Step 1: Set up PyPI Trusted Publisher if not done in Task 6 Step 2**

Confirm the publisher is configured on PyPI (see Task 6 Step 2).

- [ ] **Step 2: Tag and push**

```bash
git tag v1.0.0
git push origin master --tags
```

- [ ] **Step 3: Watch the publish workflow**

```bash
gh run watch --repo socraticsurge/telugu-calendar-utilities
```

Expected: `publish` job completes successfully. The package appears at https://pypi.org/project/mcp-server-panchangam/

- [ ] **Step 4: Verify installation**

```bash
uvx mcp-server-panchangam --help 2>&1 | head -3 || echo "entry point reachable"
```

Expected: Command found without errors.
