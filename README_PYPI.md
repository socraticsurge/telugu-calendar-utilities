# mcp-server-panchangam

An MCP (Model Context Protocol) server that gives AI assistants accurate Telugu/Vedic Panchangam data — Tithi, Nakshatra, Yoga, Karana, sky events, and auspicious/inauspicious time windows — for any city and date.

## Installation

This is a standard MCP stdio server (`uvx mcp-server-panchangam`), so it works with any MCP-compatible client or agent — Claude Desktop, Claude Code, Cursor, Windsurf, and custom agents built on the MCP SDK. Below are examples for a couple of common clients; for others, point your client's MCP config at the same `uvx mcp-server-panchangam` command.

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
- **Festivals** — 30+ named Telugu festivals (Ugadi, Vinayaka Chavithi, Deepavali, Maha Shivaratri, Makara Sankranti cluster, Navaratri days, Varalakshmi Vratam, …) plus monthly Sankashti Chaturthi and Masa Shivaratri, with traditional deciding moments (madhyahna/aparahna/pradosha/nishita)
- **Special day flags** — Ekadashi, Amavasya, Pournami, Pradosham, Sankranti, Ganda Moola
- **Eclipse** — Solar/lunar eclipse with type (Total/Partial/Annular/Penumbral), visibility from your location, eclipse window, and Sutak period (or `null` if not visible)
- **Special Yogas** — Sarvartha Siddhi, Amrita Siddhi, Visha, and Dagdha yogas
- **Timing-computation fields (1.9.0)** — `ghati_clock` (sunrise-anchored ghati/vighati clock), `nakshatra_pada` (Moon's pada 1–4), `vishaghati` windows, `bhadra_mukha`/`bhadra_puchha` (Vishti split), `sankramana_avoidance`, `in_panchaka_nakshatra`, `nakshatra_mukha` (Adho/Urdhva/Tiryak), `anandadi_yoga`, `is_khar_maasa`/`khar_maasa_name`, `is_pitru_paksha`, `simha_stha_guru`/`simha_stha_shukra` (Drik only), `guru_maudhya`/`shukra_maudhya` (Drik only), `disha_shoola_direction`, `panchaka_rahita`

### `get_muhurta(date, city, system="drik", latitude=None, longitude=None, timezone=None)`

Auspicious and inauspicious time windows only — a lighter call for quick "is this a good time?" queries. To search and rank slots across several days, use `find_muhurta`.

### `find_tarabalam_days(janma_nakshatras, start_date, days=14, city="Hyderabad", system="drik", ...)`

Tarabalam & Chandrabalam: pass 1-4 birth stars (e.g. `["Uttara Bhadrapada", "Purva Ashadha"]`) and get each day's tara per person (Janma/Sampat/Vipat/Kshema/Pratyak/Sadhana/Naidhana/Mitra/Parama Mitra) plus `good_for_all_dates` — days auspicious for everyone at once. Optionally pass `janma_rasis` (aligned, null entries allowed) to also check Chandrabalam — each person then gets the Moon's position from their rashi with a verdict (good / needs remedial puja / avoid), and `chandra_mode` selects how it affects `good_for_all`: `stars` (annotate only — default, matches classic tarabalam tables), `puja_ok`, or `strict`. Up to 60 days per call.

### `get_graha_positions(date, city="Hyderabad", ...)`

Sidereal (Lahiri) positions of all nine grahas at sunrise: longitude, rasi, nakshatra, pada, retrograde flag, plus `rasi_until` and `next_rasi` — the date each graha changes sign, retrograde-aware.

### `get_gochara(date, janma_rasi, city="Hyderabad", ...)`

Gochara (transit) verdicts from a janma rashi (natal Moon sign): each graha's house position with a verdict — favourable, blocked (vedha, with the obstructing graha named), or adverse — per the classical Brihat Samhita tables, plus named conditions: Sade Sati (with phase), Ashtama Shani, Ardhastama Shani.

### `get_rasi_phalalu(date, janma_rasi, city="Hyderabad", janma_nakshatra=None, ...)`

Daily Rasi Phalalu: a deterministic daily reading. The Moon's chandrabalam house sets the day quality, each graha's gochara verdict (with vedha) becomes one traceable sentence, Sade Sati / Ashtama Shani are stated when running, and an optional birth star adds the tarabalam line. Every line maps to a calculation — nothing is invented.

### `find_muhurta(start_date, days=7, activity="any", city="Hyderabad", system="drik", janma_nakshatras=None, ...)`

Ranked auspicious time slots: good choghadiya blocks (Amrit/Shubh/Labh/Char) with every inauspicious window subtracted, scored with Abhijit/Amrita overlap and special-yoga bonuses. `activity` tunes the rules (travel avoids Vishti karana, ceremony skips Visha/Dagdha days, purchase favours Labh, beginning favours Amrit); optional birth stars keep only days whose tarabalam favours everyone. Each slot carries its reasons. New in 1.9.0: additional activities `litigation`, `cremation`, `construction_roof`, `wood_cutting`, `well_digging`, `coronation`; Bhadra Mukha hard-avoid and Bhadra Puchha bonus for litigation; Khar-Maasa, Adhika Maasa, Pitru Paksha, Simha-Stha, Maudhya, and Panchaka Rahita filters applied per activity; optional `travel_direction` parameter (N/S/E/W/NE/NW/SE/SW) activates Disha Shoola filtering for travel.

### `get_special_days(year, month, city, system="drik", latitude=None, longitude=None, timezone=None)`

Lists special days in a given month: named festivals, Ekadashi (fasting), Amavasya (new moon), Pournami (full moon), Pradosham, Sankranti, Ganda Moola, and Solar/Lunar Eclipses. Each entry includes a `special_yogas` list for that day.

### `get_panchangam_range(start_date, end_date, city, system="drik", latitude=None, longitude=None, timezone=None)`

Compact Panchangam summary for each day in a date range (max 31 days). Each day carries Tithi, Nakshatra, Yoga, sunrise/sunset, every auspicious and inauspicious window, eclipse (if any), special yogas, and special-day flags. Useful for planning muhurtas across a week or comparing multiple days side-by-side.

### `get_daily_horas(date, city, system="drik", latitude=None, longitude=None, timezone=None)`

24 planetary hours (horas) for a date and city: 12 daytime horas starting at sunrise and 12 nighttime horas starting at sunset, each ruled by one of Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn. The first hora of the day is ruled by that weekday's lord (Sunday → Sun, Monday → Moon, …). Useful for fine-grained timing within a day.

### `get_lagna_transitions(date, city, system="drik", latitude=None, longitude=None, timezone=None)`

Ascendant (Lagna) sign boundaries for the day — the rising sign on the eastern horizon, tracked from sunrise to next sunrise. Returns each lagna with its start and end time and the rashi name. Combined with `get_daily_horas`, gives the two classical day-level subdivisions used in Muhurta selection.

## Cities and locations

`city` accepts any of the 22 pre-configured cities (instant, no network) or any free-text city name (geocoded via OpenStreetMap). You can also bypass city lookup entirely by passing `latitude`, `longitude`, and `timezone` directly.

**Telugu Heartland** — Hyderabad, Vijayawada, Visakhapatnam, Tirupati, Warangal, Guntur, Nizamabad, Rajahmundry, Kurnool, Nellore

**Major Indian Metros** — Bengaluru, Chennai, Mumbai, Delhi

**International Diaspora** — Dallas, San Jose, San Francisco, Edison (NJ), New York, London, Sydney, Dubai

## Calculation systems

| System | Basis | Best for |
|--------|-------|----------|
| `drik` | Swiss Ephemeris (pyswisseph) + Lahiri ayanamsa | Modern apps, accurate sky events |
| `surya_siddhanta` | Mean-motion algorithms from classical SS text | Traditions rooted in classical siddhantic calculation |
| `vakya` | Surya Siddhanta + published correction tables | Traditional Telugu/Tamil printed Panchangams |

## Source

Source code, tests, and the related Panchangam calendar feed project: https://github.com/socraticsurge/telugu-calendar-utilities

---

mcp-name: io.github.socraticsurge/panchangam
