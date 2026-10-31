import{_ as n,o as e,c as t,a4 as s}from"./chunks/framework.CzJ_HCFe.js";const m=JSON.parse('{"title":"01 · System Mindmap & Architecture","description":"","frontmatter":{},"headers":[],"relativePath":"reference/01-system-mindmap.md","filePath":"reference/01-system-mindmap.md","lastUpdated":1788532705000}'),r={name:"reference/01-system-mindmap.md"};function i(o,a,h,l,c,u){return e(),t("div",null,[...a[0]||(a[0]=[s(`<h1 id="_01-·-system-mindmap-architecture" tabindex="-1">01 · System Mindmap &amp; Architecture <a class="header-anchor" href="#_01-·-system-mindmap-architecture" aria-label="Permalink to &quot;01 · System Mindmap &amp; Architecture&quot;">​</a></h1><p>The whole project on a few screens. Start with the mindmap for breadth, then the layer-cake for <em>where code lives</em>, then the class hierarchy for <em>how the engines relate</em>.</p><hr><h2 id="the-deep-mindmap" tabindex="-1">The deep mindmap <a class="header-anchor" href="#the-deep-mindmap" aria-label="Permalink to &quot;The deep mindmap&quot;">​</a></h2><p>Everything the project is, from the engine core out to the three distribution surfaces. (If your viewer doesn&#39;t render Mermaid mindmaps, the same tree is in the indented list below it.)</p><pre class="mermaid">mindmap
  root((Telugu&lt;br/&gt;Panchangam))
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
        Solar &amp; lunar signs
      Sky
        Sun/Moon rise &amp; set
      Windows
        Auspicious: Brahma / Abhijit / Amrita
        Inauspicious: Rahu / Gulika / Yamagandam / Varjyam / Durmuhurtham
        Choghadiya x8
      Flags &amp; events
        Ekadashi / Amavasya / Pournami / Pradosham
        Sankranti / Sankramanam
        Festivals / Special yogas / Eclipse
      1.9.0 additive timing
        Ghati clock + Vishaghati
        Bhadra Mukha/Puchha
        Panchaka nakshatra / Panchaka Rahita
        Khar-Maasa / Pitru Paksha
        Anandadi yoga / Disha Shoola / Nakshatra Mukha
        Simha-stha &amp; Maudhya (Drik only)
    Computational features
      Ghati-precision
        ghati.py
        karana_windows.py (Vishaghati, Bhadra)
        sankramana.py
      Nakshatra &amp; yoga
        special_yogas.py (Anandadi 28, Visha/Dagdha, Pushkara)
        nakshatra_filters.py
        panchaka.py / panchanga_shuddhi.py
      Maasa &amp; periods
        maasa_filters.py (Khar-Maasa)
        pitru_paksha.py
        disha_shoola.py
      Graha-based
        graha_yuddha.py
        maudhya_calendar.py
        gochara: positions / rules / combustion / simha_stha
      Calendars &amp; events
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
</pre><h3 id="same-tree-as-text" tabindex="-1">Same tree, as text <a class="header-anchor" href="#same-tree-as-text" aria-label="Permalink to &quot;Same tree, as text&quot;">​</a></h3><ul><li><strong>Engines (the core)</strong> — <code>telugu_panchangam/engines/</code><ul><li><strong>Drik Ganita</strong> — Swiss Ephemeris true positions; 4 ayanamsas; computes outer planets (Guru/Shukra); most accurate for modern dates.</li><li><strong>Surya Siddhanta</strong> — classical mean-motion + manda correction; Kali epoch; ayanamsa is a no-op.</li><li><strong>Vakya</strong> — SS Sun + a tabulated Moon correction; subclasses SS; print tradition.</li><li><strong>Shared base</strong> — <code>calculate()</code>, <code>calculate_bulk()</code>, <code>facts_at()</code>, festival rule tables, window helpers, name tables.</li></ul></li><li><strong><code>PanchangamDay</code></strong> — the one canonical output object (see <a href="./02-engines-and-model">doc 02</a>).</li><li><strong>Computational features</strong> — standalone jyotisha modules consuming engine output (see <a href="./03-computational-features">doc 03</a>).</li><li><strong>Personal layer</strong> — per-person scoring &amp; readings (see <a href="./05-data-flow-and-muhurta">doc 05</a>).</li><li><strong>Outputs/surfaces</strong> — ICS feeds, MCP server (17 tools), landing page (see <a href="./04-user-facing-features">doc 04</a>).</li><li><strong>Distribution</strong> — GitHub Pages, PyPI, MCP registry.</li></ul><hr><h2 id="the-layer-cake-where-code-lives" tabindex="-1">The layer cake (where code lives) <a class="header-anchor" href="#the-layer-cake-where-code-lives" aria-label="Permalink to &quot;The layer cake (where code lives)&quot;">​</a></h2><p>Consumers read engine output; they never reach into engine internals. Only four public entry points cross the line.</p><pre class="mermaid">flowchart TB
    subgraph CONS[&quot;Consumers — read PanchangamDay / SlotFacts / name-tables only&quot;]
        direction LR
        PERSONAL[&quot;personal/&lt;br/&gt;muhurta · tarabalam · chandrabalam&lt;br/&gt;lagna_hora · nitya_yoga · tithi_class · phalalu&quot;]
        FEAT[&quot;feature modules/&lt;br/&gt;ghati · panchaka · special_yogas · karana_windows&lt;br/&gt;maudhya_calendar · graha_yuddha · ingress · eclipses&lt;br/&gt;nakshatra_filters · maasa_filters · pitru_paksha · sankramana&quot;]
        GOCHARA[&quot;gochara/&lt;br/&gt;positions · rules · combustion · simha_stha&quot;]
        GEN[&quot;generators/&lt;br/&gt;ics · anga_variants&quot;]
        MCP[&quot;mcp/&lt;br/&gt;server (17 tools) · tools · location&quot;]
        SCRIPTS[&quot;scripts/&lt;br/&gt;build_landing / build_gochara / build_lagna&quot;]
    end

    subgraph API[&quot;Engine public API (the contract)&quot;]
        A1[&quot;engine.calculate(date, city) → PanchangamDay&quot;]
        A2[&quot;engine.calculate_bulk(...) → list[PanchangamDay]&quot;]
        A3[&quot;engine.facts_at(jd) → SlotFacts&quot;]
        A4[&quot;RASHI_NAMES, NAKSHATRA_NAMES, TITHI_NAMES, …&quot;]
    end

    subgraph ENG[&quot;Engines — engines/&quot;]
        BASE[&quot;base.py — PanchangamEngine (ABC)&quot;]
        DRIK[&quot;drik.py — DrikGanitaEngine&quot;]
        SS[&quot;surya_siddhanta.py — SuryaSiddhantaEngine&quot;]
        VAK[&quot;vakya.py — VakyaEngine&quot;]
    end

    UTIL[&quot;engines/utils.py — JD, rise/set, cached longitudes, ayanamsa&quot;]
    MODELS[&quot;models/ — PanchangamDay, Window, Span, GhatiClock, …&quot;]

    CONS --&gt; API --&gt; ENG --&gt; UTIL --&gt; MODELS
    DRIK -.-&gt; BASE
    SS -.-&gt; BASE
    VAK -.-&gt; SS
</pre><hr><h2 id="engine-class-hierarchy-the-asymmetry" tabindex="-1">Engine class hierarchy (the asymmetry) <a class="header-anchor" href="#engine-class-hierarchy-the-asymmetry" aria-label="Permalink to &quot;Engine class hierarchy (the asymmetry)&quot;">​</a></h2><p>The three engines are <strong>not symmetric</strong> — Vakya subclasses Surya Siddhanta and only overrides the Moon-touching methods. This is the documented motivation for the (currently parked) Phase 6 <code>EngineCore</code> unification.</p><pre class="mermaid">classDiagram
    class PanchangamEngine {
        &lt;&lt;abstract&gt;&gt;
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
    PanchangamEngine &lt;|-- DrikGanitaEngine
    PanchangamEngine &lt;|-- SuryaSiddhantaEngine
    SuryaSiddhantaEngine &lt;|-- VakyaEngine
</pre><blockquote><p><strong>Why it matters:</strong> a fix to a shared helper in <code>SuryaSiddhantaEngine</code> silently changes Vakya, but the same fix in <code>DrikGanitaEngine</code> does not — and there&#39;s no warning when they drift. <code>_special_flags</code> is triplicated (Drik checks 3 sankranti points, SS checks 2). Tracked in <a href="./06-roadmap-and-backlog">doc 06 — roadmap</a>.</p></blockquote>`,17)])])}const g=n(r,[["render",i]]);export{m as __pageData,g as default};
