# 01 · System Mindmap & Architecture

The whole project on a few screens. Start with the mindmap for breadth, then the
layer-cake for *where code lives*, then the class hierarchy for *how the engines
relate*.

---

## The deep mindmap

Everything the project is, from the engine core out to the three distribution
surfaces. (If your viewer doesn't render Mermaid mindmaps, the same tree is in
the indented list below it.)

```mermaid
mindmap
  root((Telugu<br/>Panchangam))
    Engines (the core)
      Drik Ganita
        Swiss Ephemeris true positions
        Ayanamsa: Lahiri / Raman / KP / true Chitrapaksha
        Outer planets: Guru, Shukra
        Most accurate for modern dates
      Surya Siddhanta
        Mean motion + manda epicycle
        Kali epoch reference
        Ayanamsa accepted but no-op
      Vakya
        SS Sun + tabulated Moon correction
        Subclasses Surya Siddhanta
        Telugu/Tamil print tradition
      Shared base
        calculate / calculate_bulk / facts_at
        Festival rule tables
        Window helpers (Rahu/Gulika/Choghadiya...)
        Name tables (Rashi/Nakshatra/Tithi/Yoga)
    PanchangamDay (the object)
      5 Angas
        Tithi
        Nakshatra (+ pada)
        Yoga
        Karana
        Vaaram
      Metadata
        Samvatsara / Maasam / Paksham
        Ayanam / Rituvu
        Solar & lunar signs
      Sky
        Sun/Moon rise & set
      Windows
        Auspicious: Brahma / Abhijit / Amrita
        Inauspicious: Rahu / Gulika / Yamagandam / Varjyam / Durmuhurtham
        Choghadiya x8
      Flags & events
        Ekadashi / Amavasya / Pournami / Pradosham
        Sankranti / Sankramanam
        Festivals / Special yogas / Eclipse
      1.9.0 additive timing
        Ghati clock + Vishaghati
        Bhadra Mukha/Puchha
        Panchaka nakshatra / Panchaka Rahita
        Khar-Maasa / Pitru Paksha
        Anandadi yoga / Disha Shoola / Nakshatra Mukha
        Simha-stha & Maudhya (Drik only)
    Computational features
      Ghati-precision
        ghati.py
        karana_windows.py (Vishaghati, Bhadra)
        sankramana.py
      Nakshatra & yoga
        special_yogas.py (Anandadi 28, Visha/Dagdha, Pushkara)
        nakshatra_filters.py
        panchaka.py / panchanga_shuddhi.py
      Maasa & periods
        maasa_filters.py (Khar-Maasa)
        pitru_paksha.py
        disha_shoola.py
      Graha-based
        graha_yuddha.py
        maudhya_calendar.py
        gochara: positions / rules / combustion / simha_stha
      Calendars & events
        eclipses.py
        ingress.py
        cities.py
    Personal layer
      muhurta.py (the scorer)
      tarabalam.py
      chandrabalam.py
      lagna_hora.py + lagna_position.py
      nitya_yoga.py / tithi_class.py
      phalalu.py (Rasi Phalalu)
    Outputs / surfaces
      ICS feeds
        generators/ics.py (dense)
        anga_variants.py (Ekadashi/Festivals/Moon-cycles)
        generate.py (22 cities x 3 systems)
      MCP server (17 tools)
        Per-day / Range / Calendars
        Personal / Gochara / Intraday
      Landing page
        panchangam.astrochaganti.com
    Distribution
      GitHub Pages (landing + webcal)
      PyPI (mcp-server-panchangam)
      MCP registry (server.json)
```

### Same tree, as text

- **Engines (the core)** — `telugu_panchangam/engines/`
  - **Drik Ganita** — Swiss Ephemeris true positions; 4 ayanamsas; computes outer
    planets (Guru/Shukra); most accurate for modern dates.
  - **Surya Siddhanta** — classical mean-motion + manda correction; Kali epoch;
    ayanamsa is a no-op.
  - **Vakya** — SS Sun + a tabulated Moon correction; subclasses SS; print tradition.
  - **Shared base** — `calculate()`, `calculate_bulk()`, `facts_at()`, festival
    rule tables, window helpers, name tables.
- **`PanchangamDay`** — the one canonical output object (see [doc 02](02-engines-and-model.md)).
- **Computational features** — standalone jyotisha modules consuming engine output
  (see [doc 03](03-computational-features.md)).
- **Personal layer** — per-person scoring & readings (see [doc 05](05-data-flow-and-muhurta.md)).
- **Outputs/surfaces** — ICS feeds, MCP server (17 tools), landing page (see [doc 04](04-user-facing-features.md)).
- **Distribution** — GitHub Pages, PyPI, MCP registry.

---

## The layer cake (where code lives)

Consumers read engine output; they never reach into engine internals. Only four
public entry points cross the line.

```mermaid
flowchart TB
    subgraph CONS["Consumers — read PanchangamDay / SlotFacts / name-tables only"]
        direction LR
        PERSONAL["personal/<br/>muhurta · tarabalam · chandrabalam<br/>lagna_hora · nitya_yoga · tithi_class · phalalu"]
        FEAT["feature modules/<br/>ghati · panchaka · special_yogas · karana_windows<br/>maudhya_calendar · graha_yuddha · ingress · eclipses<br/>nakshatra_filters · maasa_filters · pitru_paksha · sankramana"]
        GOCHARA["gochara/<br/>positions · rules · combustion · simha_stha"]
        GEN["generators/<br/>ics · anga_variants"]
        MCP["mcp/<br/>server (17 tools) · tools · location"]
        SCRIPTS["scripts/<br/>build_landing / build_gochara / build_lagna"]
    end

    subgraph API["Engine public API (the contract)"]
        A1["engine.calculate(date, city) → PanchangamDay"]
        A2["engine.calculate_bulk(...) → list[PanchangamDay]"]
        A3["engine.facts_at(jd) → SlotFacts"]
        A4["RASHI_NAMES, NAKSHATRA_NAMES, TITHI_NAMES, …"]
    end

    subgraph ENG["Engines — engines/"]
        BASE["base.py — PanchangamEngine (ABC)"]
        DRIK["drik.py — DrikGanitaEngine"]
        SS["surya_siddhanta.py — SuryaSiddhantaEngine"]
        VAK["vakya.py — VakyaEngine"]
    end

    UTIL["engines/utils.py — JD, rise/set, cached longitudes, ayanamsa"]
    MODELS["models/ — PanchangamDay, Window, Span, GhatiClock, …"]

    CONS --> API --> ENG --> UTIL --> MODELS
    DRIK -.-> BASE
    SS -.-> BASE
    VAK -.-> SS
```

---

## Engine class hierarchy (the asymmetry)

The three engines are **not symmetric** — Vakya subclasses Surya Siddhanta and
only overrides the Moon-touching methods. This is the documented motivation for
the (currently parked) Phase 6 `EngineCore` unification.

```mermaid
classDiagram
    class PanchangamEngine {
        <<abstract>>
        +calculate(date, location, include_eclipse) PanchangamDay
        +calculate_bulk(start, days, location) list
        +facts_at(dt, location, vaaram) SlotFacts
        #_sun_longitude_func()
        #_moon_longitude_func()
        #_sun_sign_idx_at(jd)
        #_festivals(...)  rule tables
        #window helpers (rahu/gulika/choghadiya/...)
    }
    class DrikGanitaEngine {
        Swiss Ephemeris true positions
        ayanamsa-aware (Lahiri default)
        +outer planets: Guru, Shukra
        overrides every anga
    }
    class SuryaSiddhantaEngine {
        mean motion + manda correction
        Kali epoch; ayanamsa no-op
        overrides every anga
    }
    class VakyaEngine {
        SS Sun + tabulated Moon correction
        overrides ONLY Moon-touching methods
    }
    PanchangamEngine <|-- DrikGanitaEngine
    PanchangamEngine <|-- SuryaSiddhantaEngine
    SuryaSiddhantaEngine <|-- VakyaEngine
```

> **Why it matters:** a fix to a shared helper in `SuryaSiddhantaEngine`
> silently changes Vakya, but the same fix in `DrikGanitaEngine` does not — and
> there's no warning when they drift. `_special_flags` is triplicated (Drik
> checks 3 sankranti points, SS checks 2). Tracked in
> [doc 06 — roadmap](06-roadmap-and-backlog.md).
