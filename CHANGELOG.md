# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[SemVer](https://semver.org/spec/v2.0.0.html). The `mcp-server-panchangam`
PyPI version tracks this file's most recent release entry.

## [1.10.3] — 2026-06-17

The theme: **astronomical timing computations — four new MCP tools**.
All-planet combustion/visibility calendar, planetary war detection,
rashi ingress + eclipse calendar, and five-limb Panchanga Shuddhi
assessment. Every tool is a new module consuming engine outputs;
the frozen core and ICS feeds are untouched. **+84 tests
(991 → 1054 passed, 63 previously counted across PRs 101–103).**

### Added
- **`get_combustion_calendar` MCP tool** — heliacal Asta (setting) and
  Udaya (rising) periods for the five classical planets (Mercury, Venus,
  Mars, Jupiter, Saturn) via `swe.heliacal_ut()`, matching the
  Drik Panchang Asta/Udaya calendar. Per-city altitude used for
  sky-visibility accuracy. New module `telugu_panchangam/maudhya_calendar.py`.
  ([PR #101](https://github.com/socraticsurge/telugu-calendar-utilities/pull/101)).
- **`get_graha_yuddha` MCP tool** — Graha Yuddha (planetary war) periods:
  two tara grahas within 1° ecliptic longitude, winner by higher ecliptic
  latitude, entry/exit via binary search + ternary-search minimum.
  New module `telugu_panchangam/graha_yuddha.py`.
  ([PR #102](https://github.com/socraticsurge/telugu-calendar-utilities/pull/102)).
- **`get_rashi_ingresses` MCP tool** — all rashi (sign) ingress events
  for Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu; Lahiri
  sidereal; retrograde ingresses included; adaptive-step scan + 44-iter
  bisection. New module `telugu_panchangam/ingress.py`.
  ([PR #103](https://github.com/socraticsurge/telugu-calendar-utilities/pull/103)).
- **`get_eclipse_calendar` MCP tool** — solar and lunar eclipses in a
  date range with per-city visibility and Sutak timing (12 h Solar,
  9 h Lunar). Wraps the existing eclipse engine.
  ([PR #103](https://github.com/socraticsurge/telugu-calendar-utilities/pull/103)).
- **`get_panchanga_shuddhi` MCP tool** — five-limb purity assessment
  (Tithi, Vaara, Nakshatra, Yoga, Karana) with quality
  (shuddha / ashuddha / mixed) and one-line reason per limb; overall
  verdict from Sarva Ashuddha (0) to Sarva Shuddha (5). New module
  `telugu_panchangam/panchanga_shuddhi.py`.
  ([PR #104](https://github.com/socraticsurge/telugu-calendar-utilities/pull/104)).
- **`Location.alt`** — altitude (metres) added to the `Location` dataclass;
  all 22 bundled cities updated with real-world elevation values.
  Required for heliacal visibility accuracy.

---

## [1.9.0] — 2026-06-17

The theme: **classical muhurta sharpening — non-personal timing layer**.
Sixteen computations from Muhurta Chintamani, Brihat Samhita,
Dharmasindhu, and standard panchangam authority — all surface as
additive properties on `PanchangamDay` and across the three per-day
MCP response paths (`tool_get_panchangam`, `tool_get_muhurta`,
`tool_get_panchangam_range`). No personal-astrology computations
(Dasha, Navamsa, Kuta match) — those are reserved for a separate
project. Engine math is additive only; the frozen core is untouched
and ICS subscriber feeds are byte-identical. **+142 tests
(849 → 991 passed).**

### Added — Timing computations (16 features)

**Foundational (Tasks 1–3):**
- **Ghati/vighati clock infrastructure** — sunrise-anchored ghati
  scale (1 ghati = 1/60 ahoratri = sunrise→next-sunrise / 60).
  New `GhatiClock` and `GhatiWindow` dataclasses;
  `PanchangamDay.ghati_clock` exposes `sunrise`,
  `next_sunrise`, `seconds_per_ghati`. Foundation for all
  ghati-precision filters below. Module:
  `telugu_panchangam/ghati.py`.
- **Moon's pada on the daily nakshatra span** — `PanchangamDay.nakshatra_pada`
  (1..4), computed from each engine's own Moon longitude at sunrise.
  Drik value cross-pinned against `gochara/positions.py:81` (canonical
  `int(nak_pos * 4) % 4 + 1` formula).
- **Ayanamsa as engine parameter** — Drik now accepts
  `ayanamsa: 'lahiri' | 'raman' | 'krishnamurti' | 'true_chitrapaksha'`
  (default `'lahiri'`, byte-identical to prior behaviour).
  Surya Siddhanta and Vakya accept the parameter for API symmetry
  (their own mean-motion models drive sidereal positions; ayanamsa
  is a no-op there). New `engines/utils.sidereal_longitude_with_ayanamsa`
  helper restores Lahiri mode after each call to keep the hot-path
  `@lru_cache` consistent.

**Ghati-precision filters (Tasks 4–6, ride on the ghati clock):**
- **Vishaghati windows** — `PanchangamDay.vishaghati: list[GhatiWindow]`.
  Per-nakshatra "poison ghatika" offsets from Muhurta Chintamani
  (27-entry table in `karana_windows.VISHAGHATI_OFFSETS_GHATI`);
  width = 4 vighatis (`VISHAGHATI_WIDTH_VIGHATIS`). Treated as
  inauspicious cuts in muhurta slot scoring, alongside Rahu Kalam etc.
  Exposed under `inauspicious.vishaghati` in MCP.
- **Bhadra Mukha / Puchha** — Vishti karana split into Mukha
  (first 5/16 of the half-tithi, hard-avoid) and Puchha
  (last 3/16, auspicious for contests/litigation per Muhurta
  Chintamani). `PanchangamDay.bhadra_mukha` /
  `PanchangamDay.bhadra_puchha` (`GhatiWindow | None`). Mukha is
  cut from slots; Puchha grants +2 to `litigation` slots that overlap it.
- **Sankramana 16-ghati avoidance window** —
  `PanchangamDay.sankramana_avoidance: Window | None`. 16 ghatis
  before + 16 ghatis after the Sun's exact rasi-ingress moment
  (~12h 48m total). Conservative `16+16` rule (vs `30+30` for
  Karkata/Makara cited in some sources) applied uniformly.
  Samskaras with `skip_on_sankramana: True` drop slots overlapping
  this window. New helper `base._sankramanam_name_and_jd` bisects
  for the exact ingress JD via `find_crossing`.

**Nakshatra / yoga filters (Tasks 7, 13, 15):**
- **5 Panchaka Nakshatras flag** —
  `PanchangamDay.in_panchaka_nakshatra: bool`. True for Dhanishtha,
  Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada, Revati. New
  activities `cremation`, `construction_roof`, `wood_cutting` have
  `skip_on_panchaka_nakshatra: True`. Distinct from Panchaka Rahita
  (modular-9 dosha) below.
- **Anandadi 28 Yogas** — `PanchangamDay.anandadi_yoga: str | None`.
  Vaaram × Moon's nakshatra → one of 28 named muhurta yogas
  (Ananda, Kalidanda, Dhumra, Dhata, … Vardhamana) per Muhurta
  Chintamani. Auspicious yogas grant +1 / inauspicious -1 in slot
  scoring; classification tables `ANANDADI_AUSPICIOUS` and
  `ANANDADI_INAUSPICIOUS` in `special_yogas.py`.
- **Adho / Urdhva / Tiryan-Mukha nakshatra classification** —
  `PanchangamDay.nakshatra_mukha: str | None`. Activity-conditioned
  bonus: Adho (`construction_foundation`, `well_digging`), Urdhva
  (`coronation`), Tiryan (`travel`). Table in
  `nakshatra_filters.NAKSHATRA_MUKHA`.

**Solar / lunar maasa filters (Tasks 8, 11, 12):**
- **Khar-Maasa flag** — `PanchangamDay.is_khar_maasa: bool` and
  `PanchangamDay.khar_maasa_name: str | None` (`'Dhanur'` when Sun
  in Dhanu rasi; `'Meena'` when Sun in Meena). Samskara activities
  gain `skip_on_khar_maasa: True`. Note: codebase rasi spelling is
  `'Dhanu'` (not `'Dhanus'`).
- **Adhika Maasa muhurta consumption** — engine data was already
  in place since 1.0 (`engines/base.py:121-143` names months as
  `'Adhika <name>'` / `'Nija <name>'`), but `find_muhurta` ignored
  it. Samskaras now skip on `day.maasam.startswith('Adhika ')`.
  **Behaviour change:** prior versions returned slots on Adhika
  days for `wedding`/`upanayana`/`gruhapravesha`/etc.; 1.9.0 returns
  `[]` with diagnostic `'Adhika Maasa — <activity> traditionally avoided'`.
- **Pitru Paksha 15-day window** — `PanchangamDay.is_pitru_paksha: bool`.
  True for Bhadrapada Krishna paksha (15 days through Mahalaya
  Amavasya inclusive). Samskaras skip.

**Graha-based filters — Drik only (Tasks 9, 10):**
- **Simha-Stha Guru / Shukra** —
  `PanchangamDay.simha_stha_guru: bool` (hard skip on `wedding`
  via `skip_on_simha_stha_guru`) and
  `PanchangamDay.simha_stha_shukra: bool` (-2 score penalty via
  `penalty_on_simha_stha_shukra`). Strong south Indian custom
  (12-year Jupiter cycle). Surya Siddhanta and Vakya engines don't
  model outer planets — both fields stay `False` there.
- **Guru / Shukra Maudhya (combustion / heliacal setting)** —
  new `MaudhyaInfo` dataclass with `graha`, `elongation_deg`,
  `combust`, `threshold_deg` fields. Thresholds per Brihat Samhita:
  Jupiter 11°, Venus 10°. `PanchangamDay.guru_maudhya` and
  `PanchangamDay.shukra_maudhya`. `wedding` and `upanayana` gain
  `skip_on_combust: ['Guru', 'Shukra']` — universal samskara rule
  across all regional traditions.

**Activity-conditioned filter (Task 14):**
- **Disha Shoola** — `PanchangamDay.disha_shoola_direction: str | None`
  (one of `'East' | 'West' | 'North' | 'South'`). Classical weekday
  → blocked-travel-direction table. `tool_find_muhurta` gains a
  `travel_direction` parameter; when provided and matching the
  day's Disha Shoola, the `travel` activity drops slots.

**Modular-9 dosha — the headline addition (Task 16):**
- **Panchaka Rahita** — new `PanchakaInfo` dataclass with
  `remainder` (0..8), `name` (`'Rahita' | 'Mrityu' | 'Agni' |
  'Raja' | 'Chora' | 'Roga'`), `auspicious` (bool), `avoid_for`
  (list of activity tags). `PanchangamDay.panchaka_rahita` populated
  at sunrise lagna. **Slot-level recompute:** muhurta slot scoring
  recomputes Panchaka using the slot's start-moment lagna (computed
  via `personal/lagna_hora.get_lagna_transitions`, cached once per
  day). Mrityu Panchaka caps slot tier (-3 to score, day-quality
  reason); other doshas apply -2 when the activity matches
  `avoid_for`. Module: `telugu_panchangam/panchaka.py` (sources:
  Muhurta Chintamani, Dharmasindhu).

### Changed

**MCP surface:**
- All 19 new computation fields land on `tool_get_panchangam`,
  `tool_get_muhurta`, and `tool_get_panchangam_range` per-day dicts
  — consistent shape across all three tools (the
  multi-tool-serialization gap caught early in this round is now
  guarded by parity tests in each feature's test file).
- `tool_get_panchangam`, `tool_get_panchangam_range`,
  `tool_get_graha_positions`, `tool_find_muhurta` gain an optional
  `ayanamsa: str = 'lahiri'` parameter; the active ayanamsa is
  surfaced in each response.
- `tool_find_muhurta` gains an optional `travel_direction: str | None`
  parameter for Disha Shoola filtering on the `travel` activity.
- MCP server tool docstrings (`mcp/server.py`) updated to enumerate
  the new outputs.

**Muhurta activity rules (`personal/muhurta.ACTIVITY_RULES`):**
- 10 samskara activities (`ceremony`, `wedding`, `engagement`,
  `naming`, `annaprasana`, `karnavedha`, `mundana`, `upanayana`,
  `vidyarambha`, `gruhapravesha`) gained `skip_on_sankramana`,
  `skip_on_khar_maasa`, `skip_on_adhika`, `skip_on_pitru_paksha`
  rules — these days now correctly return no slots / explanatory
  diagnostic strings.
- 6 new activities added: `litigation`, `cremation`, `coronation`,
  `construction_roof`, `wood_cutting`, `well_digging`.
- `wedding` additionally gains `skip_on_simha_stha_guru`,
  `penalty_on_simha_stha_shukra: -2`, `skip_on_combust: ['Guru', 'Shukra']`.
- The activity-count test in `tests/test_muhurta_finder.py` is
  now `test_all_30_activities_callable` (was `_all_24_…`).

**Behaviour-changing fixes caught during review:**
- `prefer_bhadra_puchha` kwarg was extracted into `ACTIVITY_RULES`
  and declared on `_evaluate_slot` but never forwarded at the call
  site — the +2 Puchha bonus was a silent no-op. Now forwarded
  with a scoring-path regression test (a slot's `reasons` list
  must contain the bonus chip when overlap occurs).
- `sidereal_longitude_with_ayanamsa` set the global swisseph
  sid-mode but didn't restore it — restored on every call so the
  Lahiri `@lru_cache` hot-path never sees a stale mode.
- Daily pada formula initially used `(moon_lon % nak_arc) /
  (nak_arc / 4.0)` which mismatches the canonical `gochara/positions.py`
  form by 34 of 108 pada boundaries due to floating-point modulo
  instability — aligned to the canonical single-division form.
- One pre-existing `test_vara_bonus_thursday_wedding` was implicitly
  relying on a date where Jupiter happened to be 9.9° from the Sun
  (now correctly flagged combust); test rerouted to `2026-08-20`.
- MCP serialization initially landed in only `tool_get_panchangam`
  for the first three features (Tasks 1, 2, 4); swept fix added
  every field to all three per-day MCP tool responses with parity
  tests baked into each subsequent task.

### Notes

- **Frozen-core compliance** — no festival rules in `engines/base.py`
  touched, no `generators/ics.py` changes, no `docs/` UI changes.
  Engine `calculate()` methods gained only additive field
  assignments. ICS golden snapshot is byte-identical.
- **Personal-astrology layer deliberately out of scope.** Dasha
  (Vimshottari, Yogini), divisional charts (Navamsa et al.),
  Ashta Kuta compatibility, and Shadbala are reserved for a
  separate project that already has prior compute infrastructure.
- **Website surface unchanged** — `docs/index.html` and
  `docs/muhurta-scorer.js` were not edited. All 19 new fields are
  reachable via MCP today; the static site can adopt them when the
  paused Phase 3 (Vite + TypeScript) migration resumes.
- **Classical sources cited per feature** in the module docstrings:
  Muhurta Chintamani (Vishaghati, Bhadra Mukha/Puchha, Sankramana,
  Anandadi, Disha Shoola, Mukha-nakshatra, Panchaka Rahita),
  Brihat Samhita (Maudhya thresholds), Dharmasindhu (Pitru Paksha,
  Panchaka Rahita).

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
