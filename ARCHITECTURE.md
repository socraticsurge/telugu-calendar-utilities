# Architecture

How the project is layered and where each module sits. This is the
mental model for "where should I add X?" and for understanding the
engine-core refactor that's planned for [improvement-plan Phase 6](docs/tracking/improvement-plan.md).

> **Status note (2026-06-16):** the engines were originally treated as
> "frozen core" — additive features were required to live in new
> modules consuming engine output. That constraint has been **lifted**;
> the engines themselves are now editable, with the planned
> `EngineCore` unification refactor scheduled for Phase 6.

## The layer cake

```
┌──────────────────────────────────────────────────────────────────┐
│ Consumers (no internal coupling — they read PanchangamDay /       │
│            SlotFacts / name-tables only)                          │
│                                                                   │
│   ├── telugu_panchangam/personal/                                 │
│   │   • tarabalam.py    chandrabalam.py   lagna_position.py       │
│   │   • lagna_hora.py   muhurta.py        nitya_yoga.py           │
│   │   • tithi_class.py                                            │
│   ├── telugu_panchangam/gochara/                                  │
│   │   • positions.py    rules.py                                  │
│   ├── telugu_panchangam/generators/ics.py    ← subscriber feeds   │
│   ├── telugu_panchangam/mcp/                  ← MCP server tools  │
│   │   • server.py       tools.py                                  │
│   └── scripts/                                ← build & feed gen  │
│       • build_landing_page.py                                     │
│       • build_gochara_json.py                                     │
│       • build_lagna_json.py                                       │
└──────────────────────────────────────────────────────────────────┘
                                ▲
                                │ public API:
                                │   • engine.calculate(date, city) → PanchangamDay
                                │   • engine.calculate_bulk(dates, city) → list[PanchangamDay]
                                │   • engine.facts_at(jd) → SlotFacts
                                │   • RASHI_NAMES, NAKSHATRA_NAMES, VAARAM_NAMES, ...
                                │
┌──────────────────────────────────────────────────────────────────┐
│ Engines — three calculation systems with a shared base            │
│                                                                   │
│   telugu_panchangam/engines/                                      │
│   ├── base.py                                                     │
│   │   PanchangamEngine (ABC) — calculate(), facts_at(),           │
│   │   name tables, festival rules, helpers                        │
│   ├── drik.py        DrikGanitaEngine                             │
│   │   Swiss Ephemeris + Lahiri ayanamsa.                          │
│   │   Independent implementation; subclasses PanchangamEngine.    │
│   ├── surya_siddhanta.py   SuryaSiddhantaEngine                   │
│   │   Mean-motion algorithms from the classical SS text.          │
│   │   Subclasses PanchangamEngine.                                │
│   └── vakya.py       VakyaEngine                                  │
│       Surya Siddhanta + Vakya correction tables.                  │
│       Subclasses SuryaSiddhantaEngine (thin override of           │
│       Moon-touching methods only).                                │
└──────────────────────────────────────────────────────────────────┘
                                ▲
                                │
┌──────────────────────────────────────────────────────────────────┐
│ Utilities — pure functions, shared by every engine                │
│                                                                   │
│   telugu_panchangam/engines/utils.py                              │
│     datetime_to_jd, jd_to_utc, get_sunrise, get_sunset,           │
│     local_midnight_jd, sidereal longitude helpers (cached)        │
└──────────────────────────────────────────────────────────────────┘
                                ▲
                                │
┌──────────────────────────────────────────────────────────────────┐
│ Domain models                                                     │
│                                                                   │
│   telugu_panchangam/models/                                       │
│     PanchangamDay, SlotFacts, AngaSpan, FestivalEntry, ...        │
└──────────────────────────────────────────────────────────────────┘
```

## Engine asymmetry (the case for Phase 6 unification)

The three engines today are **not symmetric**:

- **Drik** subclasses `PanchangamEngine` directly. Independent
  implementation of every anga.
- **Surya Siddhanta** subclasses `PanchangamEngine` directly.
  Independent implementation of every anga.
- **Vakya** subclasses `SuryaSiddhantaEngine` and **only overrides the
  Moon-touching methods**: `_tithi_index_at`, `_tithi_span`,
  `_nakshatra_span`, `_yoga_span`, `_karana_spans`, `_special_flags`,
  `_maasam`, `_moon_longitude_func`.

The asymmetry creates two real correctness risks:

1. A fix to a shared helper in `SuryaSiddhantaEngine` will silently
   change Vakya. A fix to the same helper in `DrikGanitaEngine` will
   not. There's no warning when these drift.
2. `_special_flags` is triplicated. Drik checks **3** sankranti points
   (sunrise, sunset, prev/next-day boundary); SS checks **2**. We don't
   currently know which is "right" against Drik Panchang — that's
   answered during Phase 6.

The Phase 6 `EngineCore` refactor collapses all three engines into a
single core class that consumes `(sun_long_fn, moon_long_fn,
ayanamsa_fn)` and produces every span. Each engine becomes thin —
just supplies the three longitude functions and any system-specific
overrides.

## The engine API contract

Consumers (the modules in the top layer of the diagram) reach engines
through exactly four entry points:

```python
from telugu_panchangam.engines import DrikGanitaEngine
engine = DrikGanitaEngine()

day = engine.calculate(date, city)           # PanchangamDay
days = engine.calculate_bulk(dates, city)    # list[PanchangamDay]
slot = engine.facts_at(jd)                   # SlotFacts at a given Julian day
                                              #   (re-derives — Phase 6 makes this cheap)
```

Plus the constant tables that consumers import directly:
`RASHI_NAMES`, `NAKSHATRA_NAMES`, `VAARAM_NAMES`, `TITHI_NAMES`,
`MAASAM_NAMES`, `SAMVATSARA_NAMES`, `YOGA_NAMES`,
`GANDA_MOOLA_NAKSHATRAS`, and the JD helpers from `utils.py`
(`datetime_to_jd`, `jd_to_utc`, `get_sunrise`, `local_midnight_jd`).

Anything below this contract is engine-private. The MCP tools and
the generators only consume these. New consumer modules (per the
Phase 8 features) should also consume only these.

## Distribution surfaces

The project ships in three places. They're built from the same
engine output but render to different audiences.

| Surface | Form | Built by |
|---|---|---|
| `panchangam.astrochaganti.com` (landing page) | static HTML + JS, served by GitHub Pages | `docs/index.html` (hand-edited until Phase 3 Vite migration); deployed by `.github/workflows/deploy-landing.yml` |
| `webcal://` subscriber feeds (22 cities × 3 systems) | static `.ics` files in `public/feeds/` | `python -m telugu_panchangam.generate` (monthly, via `.github/workflows/generate.yml`) |
| `mcp-server-panchangam` on PyPI | Python package, stdio MCP server | `pyproject.toml` + `telugu_panchangam/mcp/`; published by `.github/workflows/publish.yml` on tag push |

The MCP registry (`io.github.socraticsurge/panchangam`) reads
`server.json` independently. The Phase 1 version-sync test
(`tests/test_version_sync.py`) keeps `pyproject.toml`, `server.json`,
and the tagged release in lockstep; the publish workflow
re-enforces this at release time.

## Test architecture

515+ tests pin behaviour. Three philosophies in use:

- **Golden-output**: most engine tests verify against pre-computed
  values cross-checked with [drikpanchang.com](https://drikpanchang.com).
  See `tests/test_drik_engine.py`, `tests/test_festivals.py`.
- **Property-style**: structural invariants — "every tithi has a
  start and end", "all nakshatras visited exactly once in 27 days".
- **Boundary**: parametrised drift guards. `tests/test_deploy_drift.py`
  catches asset references that don't reach gh-pages.
  `tests/test_version_sync.py` catches manifest drift.

The forward-year regression scheduled in Phase 6 will extend the
golden-output set to 2027–2030 across multiple anchor festivals × all
three engines.

## Where to add new things

| If you're adding... | Put it in... | Why |
|---|---|---|
| A new festival rule | `engines/base.py:_festivals()` + a test in `tests/test_festivals.py` with a DP-verified date | The dispatcher is the canonical place; expand the deciding-moment vocabulary (Phase 6) if the new rule needs a moment not yet supported |
| A new per-user calculation (e.g. compatibility) | `telugu_panchangam/personal/<feature>.py` | Personal layer is intended for this — consume `PanchangamDay` / name tables only |
| A new MCP tool | `telugu_panchangam/mcp/tools.py` (logic) + `mcp/server.py` (signature) | Both need to stay in sync; the audit caught a drift case in Phase 7 |
| A new ICS feed shape | `telugu_panchangam/generators/<name>.py` | The existing `ics.py` is the dense daily; new shapes (weekly digest, Ekadashi-only) belong as siblings |
| A new city | `telugu_panchangam/cities.py` (or wherever the 22-city table lives) + a test | Verify timezone, lat/long, and at least one DP cross-check |
| A landing-page change | `docs/index.html` until Phase 3, then `src/` under Vite | Anything visible needs sign-off per the project's UI review rule |

## See also

- [`CLAUDE.md`](CLAUDE.md) — working agreement (test discipline, commit identity, etc.)
- [`MAINTENANCE_RUNBOOK.md`](MAINTENANCE_RUNBOOK.md) — release flow, monthly crons, adding a city, dealing with CVEs
- [`docs/tracking/improvement-plan.md`](docs/tracking/improvement-plan.md) — phased roadmap
- [`CHANGELOG.md`](CHANGELOG.md) — what shipped when
