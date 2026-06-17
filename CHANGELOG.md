# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[SemVer](https://semver.org/spec/v2.0.0.html). The `mcp-server-panchangam`
PyPI version tracks this file's most recent release entry.

## [1.9.0] — 2026-06-17

### Added — Timing computations round (16 features)

**Foundational:**
- **Ghati/vighati infrastructure** — sunrise-anchored ghati clock (`GhatiClock`, `GhatiWindow`) on `PanchangamDay.ghati_clock`. Foundation for downstream classical timing windows.
- **Moon's pada on the daily nakshatra span** — `PanchangamDay.nakshatra_pada` (1..4).
- **Ayanamsa as engine parameter** — Drik accepts `ayanamsa: 'lahiri' | 'raman' | 'krishnamurti' | 'true_chitrapaksha'`; Lahiri default preserves prior byte-identical behaviour. SS and Vakya accept the parameter for API symmetry.

**Ghati-precision filters:**
- **Vishaghati windows** — `PanchangamDay.vishaghati` per Muhurta Chintamani nakshatra-poison offsets; treated as inauspicious cuts in slot scoring.
- **Bhadra Mukha / Puchha** — Vishti karana split into Mukha (first 5/16, hard-avoid) and Puchha (last 3/16, auspicious for contests/litigation).
- **Sankramana 16-ghati avoidance window** — `PanchangamDay.sankramana_avoidance`; samskara activities skip during this window.

**Nakshatra / yoga filters:**
- **5 Panchaka Nakshatras flag** — `in_panchaka_nakshatra` for cremation / roofing / wood-cutting muhurta.
- **Adho / Urdhva / Tiryan-Mukha nakshatra** — `nakshatra_mukha` activity-conditioned bonus (foundations / coronation / travel).
- **Anandadi 28 Yogas** — `anandadi_yoga` vaaram × nakshatra classification with auspicious/inauspicious scoring.

**Solar / lunar maasa filters:**
- **Khar-Maasa flag** — `is_khar_maasa` and `khar_maasa_name` (Dhanur / Meena); samskara skip.
- **Adhika Maasa muhurta consumption** — `find_muhurta` now skips Adhika months for samskaras (engine data already existed; consumption was missing).
- **Pitru Paksha 15-day window** — `is_pitru_paksha` (Bhadrapada Krishna paksha); samskara skip.

**Graha-based filters (Drik only):**
- **Simha-Stha Guru / Shukra** — `simha_stha_guru` (hard skip) and `simha_stha_shukra` (-2 penalty) for marriage muhurta.
- **Guru / Shukra Maudhya (combustion)** — `guru_maudhya` and `shukra_maudhya` (`MaudhyaInfo` with elongation, threshold, combust flag); samskara skip when combust.

**Activity-conditioned filters:**
- **Disha Shoola** — `disha_shoola_direction` (weekday direction-of-blocked-travel); travel activity drops days when `travel_direction` matches.

**Modular-9 dosha:**
- **Panchaka Rahita** — `panchaka_rahita` (mod-9 dosha: Mrityu / Agni / Raja / Chora / Roga / Rahita) at day-level (sunrise lagna) and slot-level (lagna at slot start). Mrityu universally caps; activity-specific avoidance applies penalty.

### Changed
- MCP `tool_get_panchangam`, `tool_get_muhurta`, `tool_get_panchangam_range` outputs gain all of the above fields consistently across all three response paths.
- MCP `tool_find_muhurta` gains an optional `travel_direction` parameter for Disha Shoola filtering.
- MCP `tool_get_panchangam`, `tool_get_panchangam_range`, `tool_get_graha_positions`, `tool_find_muhurta` gain an optional `ayanamsa` parameter.
- New activities in muhurta `ACTIVITY_RULES`: `litigation`, `cremation`, `construction_roof`, `wood_cutting`, `well_digging`, `coronation`.
- Test suite: 849 → 991 (+142 tests).

### Notes
- ICS feeds are byte-identical (golden snapshot guard passes).
- No personal-astrology computations were added in this round (deferred to a separate project).
- Frozen-core engines untouched beyond additive field assignments.

---

## [Unreleased]

The theme: **operational maturity**. Release safety net, dependency
hygiene, dual-axis CI matrix, security scanning, contributor docs,
forward-year DP-verified festival regression, and a uniform table-
driven festival dispatcher. No engine math changes; 21 new tests
(825 → 846 passed).

### Added
- **MCP — `find_muhurta` now exposes per-person Chandrabalam, strict
  Lagna Shuddhi, and `chandra_mode`** ([`janma_rasis`, `janma_lagnas`,
  `chandra_mode`] kwargs) — previously unreachable from MCP clients
  even though the underlying tool already supported them. Pattern
  matches `find_tarabalam_days`.
  ([PR #91](https://github.com/socraticsurge/telugu-calendar-utilities/pull/91)).
- **Per-anga ICS variant feed generators** in new
  `telugu_panchangam/generators/anga_variants.py`: Ekadashi-only,
  Festivals-only, Moon-Cycles (Pournami + Amavasya). Caller-side
  only for now; deploy + subscribe-UI is a deliberate follow-up.
  ([PR #94](https://github.com/socraticsurge/telugu-calendar-utilities/pull/94)).
- **Forward-year DP-verified festival regression**: 30 cells
  (5 anchor festivals × 2027–2028 × Hyderabad / Bengaluru / Chennai)
  with DP day-page URL provenance per cell. Locks engine behaviour
  against drikpanchang.com for two years out.
  ([PR #89](https://github.com/socraticsurge/telugu-calendar-utilities/pull/89)).
- **ICS golden-snapshot regression test** pinning byte-stable
  subscriber feed format for a 3-day stretch (Hyderabad / drik,
  5131 bytes).
  ([PR #93](https://github.com/socraticsurge/telugu-calendar-utilities/pull/93)).
- **MCP tool tests** for `tool_get_daily_horas` (4 tests including
  full-week planetary-hour-rule sweep) and `tool_get_lagna_transitions`
  (5 tests including cyclic-order invariant) — previously zero direct
  coverage.
  ([PR #92](https://github.com/socraticsurge/telugu-calendar-utilities/pull/92)).
- **`ARCHITECTURE.md` and `MAINTENANCE_RUNBOOK.md`** at repo root —
  layer-cake diagram, engine API contract, release flow, monthly
  cron map, add-a-city / add-a-festival recipes, emergency runbooks.
  ([PR #85](https://github.com/socraticsurge/telugu-calendar-utilities/pull/85)).
- **SEO surface on the landing page**: JSON-LD (`WebSite` +
  `SoftwareApplication`), `<link rel="canonical">`, sitemap.xml,
  robots.txt, OG/Twitter share preview metadata.
  ([PR #86](https://github.com/socraticsurge/telugu-calendar-utilities/pull/86)).
- **PyPI release safety**: `publish.yml` now gates on three pre-build
  checks — pyproject ↔ server.json ↔ tag version sync, CHANGELOG
  section presence (this entry's gate), and auto-creates a GitHub
  Release with extracted notes.
  ([PR #81](https://github.com/socraticsurge/telugu-calendar-utilities/pull/81)).
- **Security scanning workflow** (`security.yml`): CodeQL (Python,
  `security-and-quality` query suite) + pip-audit (`--strict`) on
  every PR, master push, and weekly Monday cron. Zero CVEs at
  baseline.
  ([PR #82](https://github.com/socraticsurge/telugu-calendar-utilities/pull/82)).
- **`tests/test_version_sync.py`** — three asserts pinning
  `pyproject.toml` ↔ `server.json.version` ↔ `server.json.packages[0].version`.
  ([PR #74](https://github.com/socraticsurge/telugu-calendar-utilities/pull/74)).
- **CNAME pin guard** in `tests/test_deploy_drift.py` — every deploy
  workflow must contain `cname: panchangam.astrochaganti.com`.
  ([PR #76](https://github.com/socraticsurge/telugu-calendar-utilities/pull/76)).

### Changed
- **`_festivals` dispatcher refactored** — Karthika Somavaram,
  Varalakshmi Vratam, Sankashti Chaturthi, and Masa Shivaratri lifted
  from inline conditionals into named rule tables
  (`_WEEKDAY_IN_MAASAM_FESTIVALS`, `_LAST_WEEKDAY_IN_PAKSHAM_FESTIVALS`,
  `_MOONRISE_MONTHLY_FESTIVALS`, `_NISHITA_MONTHLY_FESTIVALS`).
  **Byte-identical festival output** across 63 DP-verification cells.
  Adding new festivals of these shapes is now a routine row-append.
  ([PR #90](https://github.com/socraticsurge/telugu-calendar-utilities/pull/90)).
- **`ICSGenerator.generate()`** accepts an optional `variant_label`
  kwarg used by the new per-anga variant feeds. Default empty string
  preserves existing dense-feed output byte-for-byte (golden snapshot
  pinned).
  ([PR #94](https://github.com/socraticsurge/telugu-calendar-utilities/pull/94)).
- **`README_PYPI.md`** updated with 3 previously-missing 1.8.0 tools
  (`get_panchangam_range`, `get_daily_horas`, `get_lagna_transitions`).
  Picked up on the next PyPI release automatically.
  ([PR #75](https://github.com/socraticsurge/telugu-calendar-utilities/pull/75)).
- **CI matrix expanded to Python 3.10 / 3.11 / 3.12 / 3.13** (was
  3.11 only); Node runtime bumped 20 → 24 (current Active LTS, post-
  EoL); concurrency groups added to all 7 workflows.
  ([PR #77](https://github.com/socraticsurge/telugu-calendar-utilities/pull/77),
  [PR #87](https://github.com/socraticsurge/telugu-calendar-utilities/pull/87)).
- **Dependency declaration consolidated**: `pyproject.toml` is the
  source of truth; `requirements.txt` is a thin `-e .[test]` shim.
  `requirements.lock` committed for reproducible builds.
  ([PR #83](https://github.com/socraticsurge/telugu-calendar-utilities/pull/83),
  [PR #88](https://github.com/socraticsurge/telugu-calendar-utilities/pull/88)).

### Fixed
- **`server.json` version drift** — both top-level and `packages[0]`
  were pinned at 1.7.1 while PyPI shipped 1.8.0; the MCP registry was
  advertising the wrong package version. Now in lockstep with
  `pyproject.toml` and enforced by `tests/test_version_sync.py` + the
  publish-time gate.
  ([PR #74](https://github.com/socraticsurge/telugu-calendar-utilities/pull/74)).
- **`CODE_OF_CONDUCT.md` enforcement section had a blank email**
  ("reports go to … at ."). Filled in `cvk.atreya@gmail.com`.
  ([PR #75](https://github.com/socraticsurge/telugu-calendar-utilities/pull/75)).

### Removed
- Three unused imports in `engines/vakya.py` (`_CIVIL_DAYS`,
  `_MOON_REVS`, `_MOON_APOGEE_REVS`) and a dead `d += timedelta(days=1)`
  rebind in `tool_get_panchangam_range`. Byte-identical behaviour.
  ([PR #95](https://github.com/socraticsurge/telugu-calendar-utilities/pull/95)).

### Security
- **All third-party GitHub Actions pinned to commit SHAs** with
  version comments (Dependabot understands the convention). Closes
  the tag-move supply-chain risk on `peaceiris/actions-gh-pages`
  (writes to gh-pages) and `pypa/gh-action-pypi-publish` (OIDC to
  PyPI).
  ([PR #84](https://github.com/socraticsurge/telugu-calendar-utilities/pull/84)).
- **Branch protection on master** with 6 required CI contexts (4-Python
  matrix + CodeQL + pip-audit); `delete-branch-on-merge` enabled.
- **Dependabot configured** for `pip` + `github-actions` weekly bumps
  (Mondays 06:00 IST).
  ([PR #77](https://github.com/socraticsurge/telugu-calendar-utilities/pull/77)).
- `.editorconfig` + opt-in `.pre-commit-config.yaml` (ruff E/F/I +
  check-yaml + end-of-file-fixer + merge-conflict + line-ending fix).
  ([PR #83](https://github.com/socraticsurge/telugu-calendar-utilities/pull/83)).

### Verification (per `verify-against-drikpanchang.md`)
Every engine-touching change in this release is verified byte-identical
against the project's DP-verification surface:
- **33 existing DP-pinned festival dates** (`tests/test_festivals.py`) —
  unchanged
- **30 forward-year DP-verified cells** ([PR #89]) — unchanged
- **5131-byte ICS golden snapshot** ([PR #93]) — unchanged

Aggregate: 846 passed, 1 skipped (was 825 before Phase 1; +21 from
the new tests added here). Zero behaviour regressions.

### Engine surface change (sign-off recorded)
Two engine files touched:
- `engines/base.py` — `_festivals` dispatcher refactor ([PR #90]):
  inline cases for Karthika Somavaram, Varalakshmi Vratam, Sankashti
  Chaturthi, Masa Shivaratri are now data-table entries. No math
  change. Byte-identical output verified across 33+30 cells.
- `engines/vakya.py` — three unused imports removed ([PR #95]). No
  math change.

## [1.8.0] — 2026-06-15

The big theme: **janma lagna across the panchangam**. The engine now
computes lagna transitions and planetary horas; the muhurta finder scores
slots from both janma rashi and janma lagna independently; per-activity
lagna-class preferences (Sthira / Chara / Dvisvabhava) round out the
classical Muhurta Chintamani guidance.

### Added
- Lagna transitions + planetary horas as first-class engine output
  ([PR #58](https://github.com/socraticsurge/telugu-calendar-utilities/pull/58)).
- MCP tools `get_daily_horas` and `get_lagna_transitions`
  ([PR #58](https://github.com/socraticsurge/telugu-calendar-utilities/pull/58)).
- Per-city pre-computed `lagna.json` data layer + monthly cron workflow
  ([PR #61](https://github.com/socraticsurge/telugu-calendar-utilities/pull/61)).
- Hora strip + Lagna ribbon on the day card
  ([PR #61](https://github.com/socraticsurge/telugu-calendar-utilities/pull/61)).
- Lagna kendra/trikona/Ashtama scoring inside `find_muhurta`; Ashtama-Lagna
  joins Ashtama-Chandra as a tier-capping personal dosha
  ([PR #62](https://github.com/socraticsurge/telugu-calendar-utilities/pull/62)).
- Optional `janma_lagna` per profile — strict Lagna Shuddhi mode runs
  alongside the Chandra-Rashi mode (additive, both score)
  ([PR #64](https://github.com/socraticsurge/telugu-calendar-utilities/pull/64)).
- Per-activity lagna preferences: wedding → Sthira, travel → Chara,
  learning rites → Dvisvabhava, etc.
  ([PR #67](https://github.com/socraticsurge/telugu-calendar-utilities/pull/67)).
- Gochara verdicts from **both** rashi and lagna lenses side by side; chart
  highlights both natal cells; Rasi Phalalu prose carries the dual lens
  ([PR #66](https://github.com/socraticsurge/telugu-calendar-utilities/pull/66)).
- Symmetric audit-trail "neutral" chips when both references are set, so
  no asymmetric silences in the muhurta finder reasons
  ([PR #67](https://github.com/socraticsurge/telugu-calendar-utilities/pull/67)).
- Pure muhurta scorer extracted into a Node-importable module with 27
  unit tests + CI parity job, to prevent future Py/JS drift
  ([PR #65](https://github.com/socraticsurge/telugu-calendar-utilities/pull/65)).

### Changed
- Render `<Year> Nama Samvatsara` everywhere — the conversational form
  devotees actually use. JS parser handles both old and new ICS shapes
  for backward compat
  ([PR #68](https://github.com/socraticsurge/telugu-calendar-utilities/pull/68)).

### Fixed
- Amavasya and unrectified-Tara doshas now correctly cap tier
  ([PR #55](https://github.com/socraticsurge/telugu-calendar-utilities/pull/55)).
- `tara_dosha` tier cap restored in the JS UI (silent regression that
  lived for months)
  ([PR #63](https://github.com/socraticsurge/telugu-calendar-utilities/pull/63)).

### Performance
- ~30% on Tarabalam multi-day searches via `@lru_cache` on engine utils
  and a new `calculate_bulk` engine method
  ([PR #60](https://github.com/socraticsurge/telugu-calendar-utilities/pull/60)).

### Security
- DOM-XSS hardening at 7 user-name innerHTML sinks in `docs/index.html`
  ([PR #59](https://github.com/socraticsurge/telugu-calendar-utilities/pull/59)).

### Engine surface change (sign-off recorded)
Minimal additive touch (PR #60):
- `engines/utils.py`: `@lru_cache(maxsize=1024)` on four pure swisseph
  longitude wrappers.
- `engines/base.py`: default `calculate_bulk` that loops `calculate`
  sequentially; concrete engines may override later.
No engine math changed; 75-test engine regression suite + DP-verified
lagna transition test (Hyderabad 2024-01-01 Dhanu→Makara at 07:47 IST
±2 min) all pass against this code.

[Unreleased]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.8.0...HEAD
[1.8.0]: https://github.com/socraticsurge/telugu-calendar-utilities/releases/tag/v1.8.0
