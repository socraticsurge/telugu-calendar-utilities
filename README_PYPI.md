# mcp-server-panchangam

An MCP (Model Context Protocol) server that gives AI assistants accurate Telugu/Vedic Panchangam data — Tithi, Nakshatra, Yoga, Karana, sky events, auspicious windows, Gochara, and planetary sky phenomena — for any city and date.

## Installation

This is a standard MCP stdio server (`uvx mcp-server-panchangam`), compatible with any MCP client — Claude Desktop, Claude Code, Cursor, Windsurf, and custom agents built on the MCP SDK.

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

For other MCP clients, point them at the same `uvx mcp-server-panchangam` command.

## Tools

Tools are grouped by purpose. All tools that accept a `city` name also accept `latitude`, `longitude`, and `timezone` as an alternative.

---

### Daily Panchangam

#### `get_panchangam(date, city, system="drik", ...)`

Full Panchangam for a date and city:

- **Metadata** — Samvatsara, Ayanam, Rituvu, Maasam, Paksham, Vaaram, solar and lunar signs
- **Pancha Anga** — Tithi, Nakshatra, Yoga, Karana with start/end times
- **Sky events** — Sunrise, Sunset, Moonrise, Moonset
- **Auspicious windows** — Brahma Muhurta, Abhijit Muhurta, Amrita Kalam
- **Inauspicious windows** — Rahu Kalam, Gulika Kalam, Yamagandam, Varjyam, Durmuhurtham
- **Choghadiya** — 8 day blocks with names
- **Festivals** — 30+ named Telugu festivals with traditional deciding moments (madhyahna/aparahna/pradosha/nishita), plus monthly Sankashti Chaturthi and Masa Shivaratri
- **Special day flags** — Ekadashi, Amavasya, Pournami, Pradosham, Sankranti, Ganda Moola
- **Eclipse** — Solar/lunar eclipse with type, visibility from your location, eclipse window, and Sutak period
- **Special Yogas** — Sarvartha Siddhi, Amrita Siddhi, Visha, and Dagdha yogas
- **Timing fields** — `ghati_clock`, `nakshatra_pada`, `vishaghati`, `bhadra_mukha`/`bhadra_puchha`, `sankramana_avoidance`, `in_panchaka_nakshatra`, `nakshatra_mukha`, `anandadi_yoga`, `is_khar_maasa`, `is_pitru_paksha`, `simha_stha_guru`/`simha_stha_shukra`, `guru_maudhya`/`shukra_maudhya`, `disha_shoola_direction`, `panchaka_rahita`

#### `get_muhurta(date, city, system="drik", ...)`

Auspicious and inauspicious time windows only — a lighter call for quick "is this a good time?" queries. Same window data as `get_panchangam` without the full Pancha Anga detail. For ranked time slots across several days, use `find_muhurta`.

#### `get_panchanga_shuddhi(date, city, system="drik", ...)`

Five-limb purity verdict for a date: counts how many of the five Panchangam limbs are auspicious (0–5) and returns a verdict from Sarva Ashuddha to Sarva Shuddha, with quality (`shuddha` / `ashuddha` / `mixed`) and a one-line reason for each limb. Values taken at sunrise.

Rules applied per limb:
- **Tithi** — Rikta tithis (4th, 9th, 14th of either paksha) are ashuddha
- **Vaara** — Mon/Wed/Thu/Fri are shuddha; Sun/Tue/Sat are ashuddha
- **Nakshatra** — Laghu/Mridu/Dhruva/Chara are shuddha; Tikshna/Ugra are ashuddha; Krittika/Vishakha (Mishra) are mixed
- **Yoga** — 17 Nitya auspicious yogas are shuddha; Vyatipata/Vaidhriti are ashuddha; six partial-dosha yogas are mixed (with dosha window in minutes)
- **Karana** — Vishti (Bhadra) and the four fixed karanas are ashuddha; all movable karanas are shuddha

---

### Planning across days

#### `get_panchangam_range(start_date, end_date, city, system="drik", ...)`

Compact Panchangam summary for each day in a range (max 31 days): Tithi, Nakshatra, Yoga, sunrise/sunset, all auspicious and inauspicious windows, eclipse (if any), special yogas, and special-day flags. Useful for comparing multiple days or planning muhurtas across a week.

#### `get_special_days(year, month, city, system="drik", ...)`

Lists all special days in a given month: named festivals, Ekadashi, Amavasya, Pournami, Pradosham, Sankranti, Ganda Moola, and Solar/Lunar Eclipses, each with its special-yoga list.

#### `find_muhurta(start_date, days=7, activity="any", city, system="drik", janma_nakshatras=None, ...)`

Ranked auspicious time slots: good Choghadiya blocks (Amrit/Shubh/Labh/Char) with every inauspicious window subtracted, scored with Abhijit/Amrita overlap and special-yoga bonuses. Each slot carries its reasons.

`activity` tunes the rules for: `travel`, `ceremony`, `purchase`, `beginning`, `litigation`, `cremation`, `construction_roof`, `wood_cutting`, `well_digging`, `coronation`, or `any`. Optional `travel_direction` (N/S/E/W/NE/NW/SE/SW) activates Disha Shoola filtering. Optional birth stars (`janma_nakshatras`) keep only days whose Tarabalam favours everyone; optional `janma_rasis` add Chandrabalam. Activity-aware filters — Bhadra Mukha, Khar-Maasa, Adhika Maasa, Pitru Paksha, Simha-Stha, Maudhya, and Panchaka Rahita — are applied automatically per activity.

#### `find_tarabalam_days(janma_nakshatras, start_date, days=14, city, system="drik", janma_rasis=None, ...)`

Tarabalam & Chandrabalam: pass 1–4 birth stars and get each day's tara per person (Janma/Sampat/Vipat/Kshema/Pratyak/Sadhana/Naidhana/Mitra/Parama Mitra) plus `good_for_all_dates` — days auspicious for everyone at once. Pass `janma_rasis` to also check Chandrabalam; `chandra_mode` controls how it affects `good_for_all`: `stars` (annotate only — default, matches classic tarabalam tables), `puja_ok`, or `strict`. Up to 60 days per call.

---

### Sky events

These tools cover multi-day astronomical phenomena that don't appear in the single-day Panchangam view.

#### `get_combustion_calendar(start_date, end_date, city, planets=None, ...)`

Asta (heliacal setting / combustion entry) and Udaya (heliacal rising / re-emergence) periods for the five classical planets — Mercury, Venus, Mars, Jupiter, Saturn — over a date range. Asta marks when a planet becomes invisible due to Sun proximity; Udaya marks when it re-emerges. Matches the sky-visibility criterion used by Drik Panchang's Asta/Udaya calendar. Max range: 366 days. `planets` accepts a subset (e.g. `["Saturn", "Jupiter"]`).

#### `get_graha_yuddha(start_date, end_date, planets=None)`

Graha Yuddha (planetary war) periods: when two of the five tara grahas come within 1° of each other in ecliptic longitude. The planet with the higher ecliptic latitude at closest approach is the victor. Returns winner, loser, start/exact/end times in UTC, and minimum separation in arc-minutes. Sun, Moon, Rahu, and Ketu are exempt by classical convention. Max range: 366 days.

#### `get_rashi_ingresses(start_date, end_date, planets=None)`

All rashi (sign) ingress events for the classical planets: when a planet crosses from one zodiac sign to the next, including retrograde re-entries. Sidereal (Lahiri) throughout. Each entry includes the rashi entered, entry time (UTC), and exit time (next ingress). Moon is excluded (changes signs every ~2.25 days). Supported planets: Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu. Max range: 366 days.

#### `get_eclipse_calendar(start_date, end_date, city, ...)`

All solar and lunar eclipses in a date range with per-city visibility and Sutak timing. Each entry includes type (Solar/Lunar), subtype (Total/Annular/Partial/Penumbral), visibility from the given city, eclipse window in local time, and Sutak period (12h before Solar, 9h before Lunar) for visible eclipses. Max range: 730 days.

---

### Gochara and personal transits

#### `get_graha_positions(date, city, ...)`

Sidereal (Lahiri) positions of all nine grahas at sunrise: longitude, rasi, nakshatra, pada, retrograde flag, plus `rasi_until` and `next_rasi` — when each graha next changes sign. Transit groundwork for gochara queries.

#### `get_gochara(date, janma_rasi, city, ...)`

Gochara (transit) verdicts from a janma rashi (natal Moon sign): each graha's house position counted from the janma rashi with a verdict — favourable, blocked (vedha, with the obstructing graha named), or adverse — per classical Brihat Samhita tables. Includes named conditions: Sade Sati (with phase), Ashtama Shani, Ardhastama Shani.

#### `get_rasi_phalalu(date, janma_rasi, city, janma_nakshatra=None, ...)`

Deterministic daily reading for a janma rashi, rendered entirely from computed facts: the Moon's Chandrabalam house sets the day quality, each graha's gochara verdict (with vedha) becomes one traceable sentence, Sade Sati/Ashtama Shani are stated when active, and passing `janma_nakshatra` adds the day's Tarabalam line. Every sentence maps to a calculation.

---

### Intraday timing

#### `get_daily_horas(date, city, system="drik", ...)`

24 planetary hours (horas) for a date and city: 12 daytime horas starting at sunrise and 12 nighttime horas starting at sunset, each ruled by one of Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn. The first hora of the day is ruled by that weekday's lord (Sunday → Sun, Monday → Moon, …).

#### `get_lagna_transitions(date, city, system="drik", ...)`

Ascendant (Lagna) sign boundaries for the day — the rising sign on the eastern horizon, tracked from sunrise to next sunrise. Each entry includes start time, end time, and rashi name. Combined with `get_daily_horas`, gives the two classical intraday subdivisions used in Muhurta selection.

---

### Utility

#### `list_supported_cities()`

Returns the 22 pre-configured cities with name, latitude, longitude, timezone, and country. Call this first to discover valid city names and spellings.

---

## Cities and locations

`city` accepts any of the 22 pre-configured cities (resolved instantly, no network) or any free-text city name (geocoded via OpenStreetMap). You can also bypass city lookup by passing `latitude`, `longitude`, and `timezone` directly.

**Telugu Heartland** — Hyderabad, Vijayawada, Visakhapatnam, Tirupati, Warangal, Guntur, Nizamabad, Rajahmundry, Kurnool, Nellore

**Major Indian Metros** — Bengaluru, Chennai, Mumbai, Delhi

**International Diaspora** — Dallas, San Jose, San Francisco, Edison (NJ), New York, London, Sydney, Dubai

## Calculation systems

| System | Basis | Best for |
|--------|-------|----------|
| `drik` | Swiss Ephemeris (pyswisseph) + Lahiri ayanamsa | Modern apps, accurate sky events |
| `surya_siddhanta` | Mean-motion algorithms from the classical SS text | Traditions rooted in classical siddhantic calculation |
| `vakya` | Surya Siddhanta + published correction tables | Traditional Telugu/Tamil printed Panchangams |

## Source

Source code, tests, and the related Panchangam calendar feed project: https://github.com/socraticsurge/telugu-calendar-utilities

---

mcp-name: io.github.socraticsurge/panchangam
