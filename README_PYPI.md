# mcp-server-panchangam

An MCP (Model Context Protocol) server that gives AI assistants accurate Telugu/Vedic Panchangam data — Tithi, Nakshatra, Yoga, Karana, sky events, and auspicious/inauspicious time windows — for any city and date.

## Installation

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

## Tools

### `list_supported_cities`

Returns 22 pre-configured cities with name, latitude, longitude, timezone, and country. Call this first to discover valid city names.

### `get_panchangam(date, city, system="drik", latitude=None, longitude=None, timezone=None)`

Full Panchangam for a date and city:

- **Metadata** — Samvatsara, Ayanam, Rituvu, Maasam, Paksham, Vaaram, solar and lunar signs
- **Pancha Anga** — Tithi, Nakshatra, Yoga, Karana with start/end times
- **Sky events** — Sunrise, Sunset, Moonrise, Moonset
- **Auspicious windows** — Brahma Muhurta, Abhijit Muhurta, Amrita Kalam
- **Inauspicious windows** — Rahu Kalam, Gulika Kalam, Yamagandam, Varjyam, Durmuhurtham
- **Choghadiya** — 8 day blocks with names
- **Special day flags** — Ekadashi, Amavasya, Pournami, Pradosham, Sankranti

### `get_muhurta(date, city, system="drik", latitude=None, longitude=None, timezone=None)`

Auspicious and inauspicious time windows only — a lighter call for quick "is this a good time?" queries.

### `get_special_days(year, month, city, system="drik", latitude=None, longitude=None, timezone=None)`

Lists special days in a given month: Ekadashi (fasting), Amavasya (new moon), Pournami (full moon), Pradosham, and Sankranti.

## Cities and locations

`city` accepts any of the 22 pre-configured cities (instant, no network) or any free-text city name (geocoded via OpenStreetMap). You can also bypass city lookup entirely by passing `latitude`, `longitude`, and `timezone` directly.

**Telugu Heartland** — Hyderabad, Vijayawada, Visakhapatnam, Tirupati, Warangal, Guntur, Nizamabad, Rajahmundry, Kurnool, Nellore

**Major Indian Metros** — Bengaluru, Chennai, Mumbai, Delhi

**International Diaspora** — Dallas, San Jose, San Francisco, Edison (NJ), New York, London, Sydney, Dubai

## Calculation systems

| System | Basis | Best for |
|--------|-------|----------|
| `drik` | Swiss Ephemeris (pyswisseph) + Lahiri ayanamsa | Modern apps, accurate sky events |
| `surya_siddhanta` | Mean-motion algorithms from classical SS text | Temple rituals, TTD-style timing |
| `vakya` | Surya Siddhanta + published correction tables | Traditional Telugu/Tamil printed Panchangams |

## Source

Source code, tests, and the related Panchangam calendar feed project: https://github.com/socraticsurge/telugu-calendar-utilities
