# Telugu Panchangam Calendar Feeds

Subscribable Telugu Panchangam feeds for 22 cities — delivered as `.ics` files you can add to Google Calendar, Apple Calendar, or Outlook.

Every day appears as an all-day event (no calendar blocking) with full Panchangam details in the description. Special days — Ekadashi, Amavasya, Pournami, Pradosham, Sankranti — are marked with ⚡ in the title so they stand out at a glance.

## Subscribe

Visit the landing page to pick your city and calculation system and copy your `webcal://` URL:

**[socraticsurge.github.io/telugu-calendar-utilities](https://socraticsurge.github.io/telugu-calendar-utilities)**

## What's in each day's event

- **Metadata** — Samvatsara, Maasam, Paksham, Vaaram, solar and lunar signs
- **Pancha Anga** — Tithi, Nakshatra, Yoga, Karana with start/end times
- **Sky markers** — Sunrise, Sunset, Moonrise, Moonset
- **Auspicious windows** — Brahma Muhurta, Abhijit Muhurta, Amrita Kalam
- **Inauspicious windows** — Rahu Kalam, Gulika Kalam, Yamagandam, Varjyam, Durmuhurtham
- **Choghadiya** — 8 day blocks with names

## Cities

**Telugu Heartland** — Hyderabad, Vijayawada, Visakhapatnam, Tirupati, Warangal, Guntur, Nizamabad, Rajahmundry, Kurnool, Nellore

**Major Indian Metros** — Bengaluru, Chennai, Mumbai, Delhi

**International Diaspora** — Dallas, San Jose, San Francisco, Edison (NJ), New York, London, Sydney, Dubai

## Calculation Systems

| System | Basis | Best for |
|--------|-------|----------|
| **Drik Ganita** | Swiss Ephemeris (pyswisseph) + Lahiri ayanamsa | Modern apps, accurate sky events |
| **Surya Siddhanta** | Mean-motion algorithms from classical SS text | Temple rituals, TTD-style timing |
| **Vakya** | Surya Siddhanta + published correction tables | Traditional Telugu/Tamil printed Panchangams |

## How it works

Feeds are generated on the 1st of every month via GitHub Actions, covering 18 months ahead. They are served as static `.ics` files from GitHub Pages — zero hosting cost.

```
GitHub Actions (monthly cron)
  → python -m src.generate   (22 cities × 3 systems = 66 feeds)
  → feeds/*.ics
  → GitHub Pages (webcal:// subscriptions)
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
python -m src.generate   # writes to feeds/
```

## Roadmap

- **Plan A** ✅ — Drik Ganita engine + ICS pipeline + landing page
- **Plan B** ✅ — Surya Siddhanta engine
- **Plan C** ✅ — Vakya engine
- **Phase 2** — MCP server (`get_panchangam(date, location, system)` for AI assistants), Tarabalam personalization, Chrome extension
