# 04 · User-Facing Features

Three surfaces, all built from the same engine output:

1. **MCP server** — 17 tools (`mcp-server-panchangam` on PyPI)
2. **ICS calendar feeds** — 22 cities × 3 systems, on GitHub Pages
3. **Landing page** — `panchangam.astrochaganti.com`

---

## 1. MCP server — 17 tools

FastMCP server ([`mcp/server.py`](../../telugu_panchangam/mcp/server.py)), with
decorator-registered tools wrapping logic in `mcp/tools.py`. Every tool returns a
**JSON string**; failures return `{"error": "…"}`.

**Location resolution** (`mcp/location.py`): a free-text `city` resolves first
against the 22 pre-configured `CITIES` (instant, no network); unknown names fall
back to Nominatim/OpenStreetMap geocoding (10 s timeout) with timezone via
`timezonefinder`. You can also pass `latitude`/`longitude`/`timezone` directly to
skip lookup entirely.

**Ayanamsa**: `get_panchangam`, `get_panchangam_range`, `get_graha_positions`,
`get_gochara`, `get_rasi_phalalu`, `get_rashi_ingresses`, `find_muhurta` accept
`ayanamsa = lahiri | raman | krishnamurti | true_chitrapaksha` (default
`lahiri`). SS/Vakya accept it for symmetry but ignore it.

### Per-day (single date)

| Tool | Purpose | Key params |
|------|---------|-----------|
| **`get_panchangam`** | Full day: 5 angas, sky, all windows, Choghadiya, flags, 1.9.0 timing fields | `date, city, system, [lat/lon/tz], ayanamsa` |
| **`get_muhurta`** | Lighter: just the auspicious/inauspicious windows + timing fields (no anga names/sky/Choghadiya) | `date, city, system, [lat/lon/tz]` |
| **`get_panchanga_shuddhi`** | Five-limb purity verdict (Sarva Shuddha → Sarva Ashuddha) + per-limb reason | `date, city, system, [lat/lon/tz]` |
| **`get_daily_horas`** | 24 planetary hours (12 day from sunrise + 12 night), weekday-lord sequence | `date, city, system, [lat/lon/tz]` |
| **`get_lagna_transitions`** | Ascendant sign boundaries across the day | `date, city, system, [lat/lon/tz]` |

### Planning across days

| Tool | Purpose | Key params |
|------|---------|-----------|
| **`get_panchangam_range`** | Compact per-day summary over a range (≤31 days) | `start_date, end_date, city, system, ayanamsa` |
| **`get_special_days`** | Festivals, Ekadashi/Amavasya/Pournami/Pradosham, Sankranti, eclipses in a month | `year, month, city, system` |
| **`find_muhurta`** | **Ranked auspicious slots** over coming days, activity-aware, every slot with reasons + tier; hard-avoids doshas | `start_date, days(≤14), activity, city, system, janma_nakshatras, janma_rasis, janma_lagnas, chandra_mode, travel_direction, ayanamsa` |
| **`find_tarabalam_days`** | Days favourable for 1–4 people by birth star (+ optional rasi for Chandrabalam) | `janma_nakshatras[1-4], start_date, days(≤60), city, system, janma_rasis, chandra_mode` |

### Sky-event calendars (range)

| Tool | Purpose | Key params |
|------|---------|-----------|
| **`get_combustion_calendar`** | Asta/Udaya (combustion entry/exit) for Mercury/Venus/Mars/Jupiter/Saturn (≤366 days) | `start_date, end_date, city, [planets]` |
| **`get_graha_yuddha`** | Planetary-war periods — winner/loser, timing UTC, min separation (≤366 days) | `start_date, end_date, [planets]` |
| **`get_rashi_ingresses`** | All sign-change events for the classical planets (≤366 days) | `start_date, end_date, [planets], ayanamsa` |
| **`get_eclipse_calendar`** | Solar & lunar eclipses, per-city visibility, Sutak (≤730 days) | `start_date, end_date, city` |

### Gochara & personal transits

| Tool | Purpose | Key params |
|------|---------|-----------|
| **`get_graha_positions`** | All 9 grahas at sunrise — rasi, nakshatra, pada, retrograde, next-rasi date | `date, city, ayanamsa` |
| **`get_gochara`** | Transit verdicts from a janma rasi — houses, vedha, Sade Sati / Ashtama Shani | `date, janma_rasi, city, ayanamsa` |
| **`get_rasi_phalalu`** | Deterministic daily reading rendered from gochara + chandrabalam + tarabalam | `date, janma_rasi, [janma_nakshatra], city, ayanamsa` |

### Utility

| Tool | Purpose |
|------|---------|
| **`list_supported_cities`** | The 22 pre-configured cities with lat/lon/timezone |

> **17 tools total.** Grouping mirrors the
> [README_PYPI tool table](../../README_PYPI.md); this doc adds the parameter and
> return-shape detail. Full per-field return shapes were mapped during this
> doc's generation — see `mcp/tools.py` for the authoritative serializers.

---

## 2. ICS calendar feeds

**What:** one all-day event per day, full panchangam in the description. Festival
days get 🪔 in the title; other special days (Ekadashi/Amavasya/Pournami/
Pradosham/Sankranti/eclipse) get ⚡.

**Each event's description** (`generators/ics.py`): metadata
(Samvatsara/Maasam/Paksham/Vaaram, ayanam/rituvu, signs), the five angas with
HH:MM(±1) bounds, sky markers, auspicious & inauspicious windows, daytime **and**
night Choghadiya, eclipse + Sutak, special yogas, and a specials summary.

**Dense vs variant feeds:**
- Dense (default, `variant_label=''`): every day, full description.
- **Variant feeds** (`generators/anga_variants.py`): Ekadashi-only,
  Festivals-only, Moon-Cycles (Pournami+Amavasya) — pure filters that reuse
  `ICSGenerator`, so format/metadata never drift. *Built but not yet deployed —
  a deliberate follow-up (see [roadmap](06-roadmap-and-backlog.md)).*

**Generation** (`generate.py`): `generate_feeds(out, start, end, systems, cities)`
precomputes eclipses once, then loops systems × cities × days →
`{city_slug}-{system}.ics`. **22 cities × 3 systems = 66 feeds**, regenerated
monthly by GitHub Actions covering ~18 months ahead, served as static files from
GitHub Pages (`webcal://` subscriptions, zero hosting cost).

```mermaid
flowchart LR
    CRON["GitHub Actions<br/>(monthly cron)"] --> GEN["python -m telugu_panchangam.generate"]
    GEN -->|"22 cities × 3 systems"| ICS["66 × .ics"]
    ICS --> PAGES["GitHub Pages<br/>panchangam.astrochaganti.com"]
    PAGES -->|"webcal://"| SUB["Google / Apple / Outlook"]
```

**Cities:** Telugu heartland (Hyderabad, Vijayawada, Visakhapatnam, Tirupati,
Warangal, Guntur, Nizamabad, Rajahmundry, Kurnool, Nellore) · metros (Bengaluru,
Chennai, Mumbai, Delhi) · diaspora (Dallas, San Jose, San Francisco, Edison,
New York, London, Sydney, Dubai).

**Systems:** Drik Ganita (modern apps) · Surya Siddhanta (classical tradition) ·
Vakya (Telugu/Tamil printed panchangams).

---

## 3. Landing page

The Vite/TypeScript application under `src/`, built by `deploy-landing.yml`
and served at `panchangam.astrochaganti.com`
(the `CNAME` is load-bearing — never drop it). Beyond letting devotees pick a
city/system and copy a `webcal://` URL, it's a daily toolkit:

- **Today's Panchangam** — any date, any city.
- **Tarabalam · Muhurtam** — good days & ranked time slots for up to four people
  by birth star, with Chandrabalam. Typed scorer modules consume the generated
  Python activity contract; runtime `lagna.json` / `gochara.json` sidecars
  supply slot-time data. The per-city Lagna sidecar also carries Guru/Shukra
  combustion flags, allowing browser Muhurtam searches to enforce the same
  Maudhya exclusions declared by the Python activity profile. If those flags
  are absent, affected browser searches fail closed instead of returning
  unscreened dates.
- **Gochara + Rasi Phalalu** — South Indian chart, transit verdicts, computed
  daily reading.

Everything is shareable to WhatsApp.

### Guest profiles and local data

Guests can save up to **four profiles** for reuse in Daily Horoscope and
Muhurtam. Manual entry is always available. On localhost, or in a public build
that explicitly enables the remote calculation capability, the default flow
accepts name, exact date/time of birth, and a selected birthplace. After an
explicit calculation, it shows Nakshatra, Padam, Janma Rashi, Lagna, a South
Indian D1 chart, an accessible graha table, and the calculation method before
anything is saved.

The Profiles destination supports create, edit, delete, and clear-all actions.
Recalculation and editing of a calculated profile are available only while the
birth-calculation capability is active. When it is inactive, an already-saved
calculated profile remains viewable and usable and is never converted into a
manual profile. A saved profile can contain:

| Field | Purpose and readiness |
|-------|-----------------------|
| **Name** | Required display label for recognizing the person. |
| **Date, time, and selected birthplace** | Used by calculated profiles to reproduce the birth instant and location-dependent Lagna. |
| **Nakshatra** | Calculated from the sidereal Moon longitude, or supplied manually; required for Muhurtam and for deriving the Daily Horoscope's Janma Rashi. |
| **Padam** | Optional for Muhurtam; needed for Daily Horoscope only when the selected Nakshatra spans two Rashis. |
| **Janma Rashi** | Calculated from Chandra with the disclosed sidereal convention. |
| **Lagna** | Calculated from the exact birth instant and selected coordinates; it remains optional in a manual profile. |
| **D1 chart and provenance** | Nine graha positions, Whole Sign houses, contract version, engine version, Lahiri ayanamsha, and the actual reported ephemeris. |

A profile is **Muhurtam-ready** once it has a Nakshatra. It is **Daily
Horoscope-ready** once its Janma Rashi can be derived from the Nakshatra, with
Padam supplied for a Nakshatra that crosses a Rashi boundary. Contextual create
and edit actions return to the originating journey; a one-off Muhurtam person
can remain limited to that search instead of becoming a saved profile.

Profiles are stored only in this browser's origin-scoped `localStorage`. The
name never leaves the browser. Place search sends the submitted city/town text;
calculation sends the date, time, selected coordinates, and IANA timezone to a
stateless Astro Chaganti gateway and authenticated DashaFlow sidecar. See the
[full calculation and privacy contract](53-birth-profile-calculation.md).

Public builds fail closed by default. `VITE_BIRTH_PROFILE_API_ENABLED=true`
is the only public opt-in, and `true` must be the exact, case-sensitive string;
whitespace, alternate casing, empty and malformed values disable calculation.
An absent flag enables calculation only on `localhost`, `127.0.0.1`, or
`[::1]`. Public pages always route through the canonical
`https://astrochaganti.com/api/guest` HTTPS gateway and ignore loopback or
arbitrary base overrides. The client flag controls presentation and requests;
independent server-side activation remains mandatory and blocked pending the
licensing and place-provider decisions tracked in
[#231](https://github.com/socraticsurge/telugu-calendar-utilities/issues/231)
and [#233](https://github.com/socraticsurge/telugu-calendar-utilities/issues/233).

Anyone using the same browser profile and site origin can see the saved data.
It is isolated from other browsers, devices, domains, protocols, and ports
(including a local test server running on a different port). Clearing site data
or deleting a profile is permanent, and private-browsing storage may disappear
when the private session ends. There is no account, cloud sync, cross-device
transfer, or recovery.

GoatCounter may receive fixed, content-free interface events. Analytics must
never receive profile names, birth details, coordinates, Nakshatra, Padam,
Lagna, chart data, profile IDs, or stored journey selections.

> MCP remains the complete computational interface. The website intentionally
> presents a curated devotee-facing subset; its declared activity catalogue and
> generated rule contract are protected by parity tests.
