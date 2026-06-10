# Telugu Panchangam Calendar Utilities — Design Spec

**Date:** 2026-06-10
**Status:** approved

---

## Overview

A Telugu Panchangam generator that produces iCalendar (`.ics`) subscription feeds for 22 cities,
covering the full traditional Panchangam — five elements, auspicious/inauspicious windows, solar
and lunar markers, and special-day alerts. Feeds are generated monthly via GitHub Actions and
hosted on GitHub Pages at zero cost.

---

## Goals

- Produce accurate Panchangam data using three traditional calculation systems
- Deliver it as subscribable calendar feeds (webcal://) compatible with Google, Apple, and Outlook
- Give users advance alerts for fasting days (Ekadashi, Amavasya, Pournami, Pradosham) and
  inauspicious windows (Rahu Kalam, Varjyam, Durmuhurtam) so they can plan accordingly
- Keep the entire system free to run and maintain

## Non-Goals (Phase 1)

- Tarabalam (personalized by birth Nakshatra) — deferred to Phase 2
- Chrome extension — deferred to Phase 2
- MCP server — deferred to Phase 2 (see below)
- Real-time / on-demand feed generation (static monthly generation is sufficient)
- Automatic alerts or timed calendar blocks — users set their own reminders
- User accounts or personalization beyond city + system selection

## Phase 2 Roadmap

**MCP Server:** Expose the Panchangam engine as an MCP (Model Context Protocol) tool so AI
assistants (Claude, etc.) can query it directly. A tool like `get_panchangam(date, location, system)`
returns structured PanchangamDay data. This enables conversational, personalized use — "remind me
of all Ekadashis this year", "is tomorrow auspicious for a new venture?", "what is Rahu Kalam
in Hyderabad today?" — far more flexible than any static feed.

**Tarabalam:** Personalized feed variant where users provide their Janma Nakshatra and the feed
highlights auspicious/inauspicious days specific to them.

**Chrome Extension:** Quick-access Panchangam for the current day/location without opening a
calendar app.

---

## Architecture

Four layers, each with a single responsibility:

```
Layer 1: Calculation Engines
  DrikGanitaEngine | SuryaSiddhantaEngine | VakyaEngine
          ↓
Layer 2: Data Model
  PanchangamDay (system-agnostic)
          ↓
Layer 3: ICS Generator
  PanchangamDay → VEVENT + VALARM → .ics file
          ↓
Layer 4: Distribution
  GitHub Actions (monthly) → GitHub Pages (66 feeds + landing page)
```

### Project Structure

```
src/
  engines/
    base.py                  # abstract PanchangamEngine interface
    drik.py                  # DrikGanitaEngine (pyswisseph + Lahiri ayanamsa)
    surya_siddhanta.py       # SuryaSiddhantaEngine (mean-motion algorithms)
    vakya.py                 # VakyaEngine (Vakya correction tables)
  models/
    panchangam_day.py        # PanchangamDay, Span, Window, Location dataclasses
  generators/
    ics.py                   # ICSGenerator
  cities.py                  # 22 city configs (name, lat, lon, timezone)
  generate.py                # entry point: loops cities × systems, writes feeds/
.github/workflows/
  generate.yml               # monthly cron + workflow_dispatch
docs/                        # GitHub Pages: landing page HTML/CSS/JS
feeds/                       # generated .ics output (published via Actions)
tests/
  test_drik_engine.py
  test_surya_siddhanta_engine.py
  test_vakya_engine.py
  test_ics_generator.py
  test_generate.py
```

---

## Calculation Systems

Three backends, all implementing `PanchangamEngine.calculate(date, location) → PanchangamDay`:

| System | Basis | Ayanamsa | Best for |
|--------|-------|----------|----------|
| Drik Ganita | pyswisseph (Swiss Ephemeris) | Lahiri | Accurate sky events, modern apps |
| Surya Siddhanta | Mean-motion algorithms from published SS text | Built-in | Classical/temple ritual timing |
| Vakya | Surya Siddhanta base + published Vakya correction tables | Built-in | Traditional Telugu/Tamil calendars |

Reference implementation for cross-checking: IIT Madras jyotisha (open source).

---

## Data Model

```python
@dataclass
class Location:
    name: str
    lat: float
    lon: float
    timezone: str           # e.g. "Asia/Kolkata"

@dataclass
class Span:
    name: str
    start: datetime         # UTC internally
    end: datetime

@dataclass
class Window:
    name: str
    start: datetime
    end: datetime

@dataclass
class PanchangamDay:
    # Identity
    date: date
    location: Location
    system: str             # 'drik' | 'surya_siddhanta' | 'vakya'

    # Metadata
    samvatsara: str
    ayanam: str             # 'Uttarayanam' | 'Dakshinayanam'
    rituvu: str             # season
    maasam: str             # lunar month
    paksham: str            # 'Shukla' | 'Krishna'

    # Five elements (Pancha Anga)
    tithi: Span
    vaaram: str             # day name in Telugu
    nakshatra: Span
    yoga: Span
    karana: list[Span]      # up to 2 per day

    # Solar & lunar markers
    sunrise: datetime
    sunset: datetime
    moonrise: datetime
    moonset: datetime
    solar_sign: str         # rashi
    lunar_sign: str         # rashi

    # Auspicious windows
    brahma_muhurta: Window
    abhijit_muhurta: Window | None   # absent on Wednesdays
    amrita_kalam: list[Window]

    # Inauspicious windows
    rahu_kalam: Window
    gulika_kalam: Window
    yamagandam: Window
    varjyam: list[Window]
    durmuhurtham: list[Window]

    # Choghadiya (8 blocks per day)
    choghadiya: list[Window]

    # Special day flags
    is_ekadashi: bool
    is_amavasya: bool
    is_pournami: bool
    is_pradosham: bool
    is_shani_pradosham: bool
    is_soma_pradosham: bool
    is_sankranti: bool
    special_notes: list[str]
```

All datetimes stored in UTC; converted to local timezone only at ICS generation.

---

## ICS Generation

### One event per day — all-day summary

Each day produces a single all-day VEVENT. No timed blocks, no automatic reminders (VALARM).
Users read the details on demand and set their own reminders if they choose.

```
Title:       Shukla Ekadashi · Hasta Nakshatra · Shobhana Yoga
Description:
  Samvatsara: Sharvari | Chaitra Maasam | Shukla Paksham | Mangalavaaram
  Sunrise: 05:48 | Sunset: 18:42 | Moonrise: 16:12 | Moonset: 04:30
  Solar sign: Mesha | Lunar sign: Tula

  Tithi:     Shukla Ekadashi  05:20 – next day 03:45
  Nakshatra: Hasta             06:10 – next day 04:55
  Yoga:      Shobhana          all day
  Karana:    Vanija / Vishti

  Auspicious:
    Brahma Muhurta   05:12 – 05:58
    Abhijit Muhurta  11:46 – 12:32
    Amrita Kalam     07:15 – 08:00

  Inauspicious:
    Rahu Kalam       09:00 – 10:30
    Gulika Kalam     07:30 – 09:00
    Yamagandam       12:00 – 13:30
    Varjyam          14:00 – 14:48
    Durmuhurtham     08:30 – 09:18, 15:30 – 16:18

  Choghadiya: Udveg 06:00 | Char 07:30 | Labh 09:00 | Amrit 10:30 ...

  ⚡ Ekadashi — fasting day
```

Special days (Ekadashi, Amavasya, Pournami, Pradosham, Sankranti) are highlighted with a
prefix symbol in the title: `⚡ Shukla Ekadashi · Hasta · ...`

### Feed naming convention
`{city-slug}-{system}.ics`
Examples: `hyderabad-drik.ics`, `tirupati-surya-siddhanta.ics`, `london-vakya.ics`

---

## Cities (22)

### Telugu Heartland (AP + Telangana)
Hyderabad, Vijayawada, Visakhapatnam, Tirupati, Warangal, Guntur, Nizamabad, Rajahmundry, Kurnool, Nellore

### Major Indian Metros
Bengaluru, Chennai, Mumbai, Delhi

### International Diaspora
Dallas, San Jose, San Francisco, Edison (NJ), New York, London, Sydney, Dubai

**Total feeds:** 22 cities × 3 systems = **66 feeds**

---

## GitHub Actions Pipeline

**Trigger:** 1st of every month at 02:00 UTC + manual `workflow_dispatch`

**Steps:**
1. Checkout repo
2. Set up Python, install `pyswisseph` and `icalendar`
3. Run `generate.py` — 22 × 3 loops, writes `feeds/*.ics`
4. Rebuild landing page HTML into `docs/`
5. Commit and push `feeds/` + `docs/` to `gh-pages` branch

**Feed window:** 18 months ahead from generation date (no gaps for subscribers).

**Estimated runtime:** < 2 minutes. Well within GitHub Actions free tier.

---

## Landing Page

Static HTML/CSS/JS hosted on GitHub Pages alongside the feeds.

**Sections:**
1. What is Telugu Panchangam — brief educational intro
2. Which system to choose — plain-language explanation of Drik vs Surya Siddhanta vs Vakya
3. **City + system picker** — dropdowns → generates `webcal://` URL → Copy button
4. How to subscribe — step-by-step for Google Calendar, Apple Calendar, Outlook

No build tools, no framework. Plain HTML.

---

## Testing Strategy

TDD throughout. Each engine tested against known reference dates cross-checked against
published Panchangams. Key test cases:
- Correct Tithi at sunrise for a known date + location
- Correct Rahu Kalam times for Hyderabad
- Sankranti detection on known dates
- Ekadashi flag set correctly across Paksha boundary
- ICS output is valid (parseable by `icalendar` library)
- All 66 feeds generated without error

---

## Stories

| ID | Role | Story |
|----|------|-------|
| S01 | devotee | subscribe to a Panchangam calendar feed for my city so Tithi/Nakshatra appear in my calendar |
| S02 | devotee | receive an alert the evening before Ekadashi so I can prepare for my fast |
| S03 | devotee | receive alerts before Amavasya, Pournami, Pradosham, and Shani Pradosham |
| S04 | devotee | see Rahu Kalam and other inauspicious windows as calendar blocks with advance reminders |
| S05 | devotee | see Brahma Muhurta, Abhijit Muhurta, and Amrita Kalam as auspicious calendar blocks |
| S06 | devotee | see Varjyam, Durmuhurtham, and Choghadiya blocks in my calendar |
| S07 | devotee | get the full day metadata (Samvatsara, Maasam, Paksham, Vaaram) visible in the all-day event |
| S08 | devotee | pick my city and preferred calculation system from a landing page and get my subscription URL |
| S09 | scholar/priest | choose Surya Siddhanta or Vakya system for ritual-accurate timings |
| S10 | developer/maintainer | have feeds regenerated automatically each month without manual intervention |
