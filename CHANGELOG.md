# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[SemVer](https://semver.org/spec/v2.0.0.html). The `mcp-server-panchangam`
PyPI version tracks this file's most recent release entry.

## [Unreleased]

### Fixed

- Constrain the MCP SDK to the tested 1.x API so fresh installations cannot
  resolve the incompatible 2.x package while the server uses
  `mcp.server.fastmcp`.

## [1.13.0] — 2026-07-22

Astrological authority and Muhurtam coverage release. The daily Panchangam,
Daily Horoscope and Muhurtam surfaces now disclose criterion-level provenance
instead of treating computed output as uniform textual authority.

### Release highlights

- **Muhurtam coverage:** 34 of 35 distinct purpose-specific profiles now have
  verified rule-level source claims; `Anything auspicious` remains the sole
  explicit heuristic. House warming is the narrowly scoped, source-verified
  Gruhapravesha election, with completed-house purchase and renovation kept
  separate.
- **Corrected elections:** wedding, Gruhapravesha, court filing, engagement,
  Homahuti, deferred Pretakriya, Seemantha, borrowing, lending, inventory
  purchase, service entry, capital deployment, Shantika/Paushtika and
  Dharma-kriya rules now follow their inspected passages and disclose manual
  chart conditions.
- **Panchangam and horoscope corrections:** Bhadra Mukha/Puchha follows the
  Tithi-specific Muhurta Chintamani Yamas; Rahu and Ketu transit houses follow
  Phaladeepika rather than inheriting Shani's set.
- **MCP trust contract:** `find_muhurta` returns the selected activity's
  provenance, automated constraints and manual prerequisites. Panchangam
  responses disclose authority state by output category.
- **Clearer recommendations:** browser results remove irrelevant weekday
  guidance, separate computed strengths from chart validation and practical
  information, and keep specialist Dharma-kriya/Pretakriya activities out of
  the general public selector while retaining them in Python and MCP.
- **Engineering:** generated Python-to-browser activity contracts, provenance
  validation, documentation-drift checks and `tools/verify_project.py` provide
  one fail-fast verification path across Python, frontend tests, type checking
  and production build.

### Added
- **Precisely scoped vehicle-acquisition profile.** Raman Chapter IV, printed
  page 10 (PDF page 14), now supplies a +1 preference for five movable
  Nakshatras without treating every other star as rejected.
  Other vehicle ranking preferences remain explicitly uncited project rules;
  the citation is not presented as a complete vehicle election. Coverage is
  now 10/30.
- **Source-backed Upanayana profile.** Raman Chapter VIII, printed pages
  23–24 (PDF pages 27–28), now supplies lunar months, Uttarayana solar Rasis,
  exact Paksha-qualified Tithis, weekdays, Nakshatras, Lagnas and a before-noon
  gate. Age, conditional Budha combustion and chart checks remain explicit.
  Verified activity coverage reaches 9/30.
- **Source-backed Vidyarambha profile.** Raman Chapter VIII, printed page 23
  (PDF page 27), now supplies exact weekday, Nakshatra and movable-or-common
  Lagna gates; age, forenoon/noon preference and chart checks remain explicit.
  Verified activity coverage reaches 8/30.
- **Source-backed Mundana / Chaula profile.** Raman Chapter VIII, printed
  pages 22–23 (PDF pages 26–27), now supplies Shukla-Paksha, combustion,
  Tithi, Nakshatra, weekday, conservative Lagna and forenoon constraints.
  Python and browser share the solar-noon boundary. Coverage reaches 7/30.
- **Source-backed Karnavedha profile.** Raman Chapter VIII, printed page 22
  (PDF page 26), now supplies the never-at-night rule, weekdays and rejected
  rising Rasis; its Tithi reference resolves to Chapter V. Age, transition and
  election-house checks remain explicit. Coverage rises from 5/30 to 6/30.
- **Source-backed Annaprasana profile.** Raman Chapter VIII, printed pages
  21–22 (PDF pages 25–26), now supplies the admitted Nakshatras, weekdays and
  rising Rasis; its general-Tithi reference is resolved to Chapter V's exact
  Panchanga-Suddhi list. Child-age and election-chart checks remain explicit.
  Verified activity coverage rises from 4/30 to 5/30.
- **Source-backed Namakarana profile.** Raman Chapter VIII, printed page 21
  (PDF page 25), now supplies the ceremony's admitted Nakshatras and weekdays,
  rejected Tithi numbers, fixed-Lagna preference, and disclosed birth-day,
  election-chart and name-selection checks. Verified activity coverage rises
  from 3/30 to 4/30.
- **One-command project verification.** `python tools/verify_project.py` now
  runs provenance-link validation, generated activity-data drift checks, the
  complete Python suite, frontend tests, typecheck, and production build in a
  fixed fail-fast order.
- **Machine-checked activity provenance.** Verified Muhurtam profiles now
  declare their stable ledger claim beside the Python rules; MCP and the
  browser consume that shared field. A CI-ready audit rejects missing,
  non-Muhurtam, non-verified, or duplicate links and reports the honest
  coverage baseline: 3 of 30 activity profiles have exact rule locators.
- **Source-backed land-purchase profile.** The former generic Property / Land
  option is now accurately scoped to buying land for building, following
  Raman Chapter XII, printed page 53 (PDF page 57): fourteen Nakshatras, four
  weekdays, hard Rikta-Tithi rejection, fixed-Lagna preference, and disclosed
  manual election-chart checks. Buying a completed house is explicitly outside
  this profile rather than silently conflated with land purchase.
- **Source-backed well-digging activity.** Raman, *Muhurtha*, Chapter XII,
  printed page 51 (PDF page 55), now supplies the eight admitted Nakshatras,
  three admitted rising Rasis, the Surya-in-Lagna hard-rock caution, and
  explicit manual Shukra/Chandra chart checks. The activity is now selectable
  on the website and exposed through the same generated contract as Python.
- **Source-backed Bhumi Puja / house-foundation profile.** B. V. Raman,
  *Muhurtha*, Chapter XII, printed page 50 (PDF page 54), now governs the
  activity's admitted lunar months, solar-Rasi classes, exact Tithi numbers,
  Nakshatras, weekdays and fixed Lagna. Full election-chart and site-placement
  conditions remain explicit manual checks.
- `find_muhurta` now returns an additive `activity_profile` with the automated
  constraints, manual review requirements, and stable provenance claim ID.
  The website consumes the same generated Python activity contract.

### Changed
- Bhumi Puja / foundation candidates use the cited activity profile instead
  of the former generic Bhadra-tithi/fixed-Lagna preference pair. Shared
  samskara and ranking rules remain independently disclosed.

### Documentation
- Corrected the Muhurtam architecture guide from the retired
  Choghadiya-derived slot model to the named, indivisible 30-Muhurta pipeline;
  narrowed Drik Panchang's role to external Drik-output comparison rather than
  universal textual authority.
- Added a criterion-level foundation-laying crosswalk and verified
  `muhurta.bhumi_puja.foundation` provenance claim.
- CHANGELOG reconciled against the full git history. The operational-
  maturity round that actually shipped **inside the v1.9.0 tag** is now
  folded into the [1.9.0] entry — it had been stranded under a misplaced
  `[Unreleased]` heading below newer releases. Every release back to the
  project's first tag (**v1.0.5**) is now documented here, with
  comparison links.

### Housekeeping
- The 15 automated-assistant cleanup commits from the 1.9.0 round were
  re-authored to the maintainer identity, so the assistant bot no longer
  appears in the contributor list. Author/committer metadata only — every
  tree SHA is unchanged, so released artifacts are byte-identical.

## [1.12.0] — 2026-07-21

Muhurta finder rebuilt on the named 30-muhurta grid. **1082 tests passing.**

### Changed
- **Muhurta slots are now the named muhurtas**, not choghadiya-derived
  windows. `day_slots`/`night_slots` iterate the 30 muhurtas of the
  ahoratra — 15 daytime (sunrise→sunset ÷15) + 15 night (sunset→next
  sunrise ÷15), each an indivisible ~48-min unit carrying its name,
  presiding deity, and intrinsic nature. New module
  `telugu_panchangam/muhurtas.py`; owner-verified reference table at
  `docs/reference/07-muhurta-table.md`.
- **Additive, disclosed scoring.** A slot's score layers: intrinsic
  muhurta nature (Abhijit/Brahma +2, other auspicious +1, inauspicious −2)
  + dominant choghadiya (a scoring attribute — straddle disclosed, not a
  gate) + weekday Durmuhurtam / hard-window exclusion + the existing
  tarabalam, chandrabalam, lagna, tithi-class and special-yoga factors.
  Abhijit and Brahma are now scored as the 8th-day / 14th-night muhurta
  natures (the old "overlaps Abhijit/Brahma" bonuses are retired; Abhijit
  is correctly absent on Wednesday). This **supersedes the interim
  block-iteration fix (PR #135)** and fully resolves the 2026-07-21
  choghadiya mislabel (a Kaal slot scored as Amrit).
- Each slot now leads with its muhurta identity, e.g.
  `Vidhi (Abhijit) muhurta · Brahma · auspicious (+2)`. The website finder
  (`src/panels/tarabalam.ts`) mirrors the Python source of truth.
- **Card wording cleaned up.** User-facing muhurta reasons, skip
  diagnostics and doctrinal notes now use middots and plain punctuation
  instead of em-dashes; time and date ranges read "to". The redundant
  "clear of all inauspicious windows" line is removed: it was a tautology
  (a slot is only kept when it clears the hard windows) that also
  contradicted any muhurta of inauspicious nature. An adversarial sweep
  over 160 date/city/activity/profile combinations confirms zero dashes,
  zero contradictions, and each score equal to the sum of its (+n)/(−n)
  bonuses.
- **Day context on every slot card (website).** Each card carries the
  day's sunrise anga (Tithi, Nakshatra, Nitya Yoga) plus a timings row.
  Sunrise, Abhijit and Rahu Kalam show by default; the complete Panchangam
  auspicious and avoid window lists sit behind an "all timings" expand, so
  a slot's day quality is legible without switching to the Panchangam tab.
  Display only.

Affects `tool_find_muhurta` (MCP) and the website muhurta finder.

## [1.11.0] — 2026-06-22

The theme: **muhurta scorer enhancements** — cognitive split of the
scorer into three files, Siddha Yoga detection, Rikta dosha neutralization,
and activity-aware tithi-avoid scoring. No frozen-core or ICS-feed changes.
**1055 tests passing.**

### Added
- **Siddha Yoga detection** (`special_yogas.py`) — all five classical
  Tithi×Vara combinations from Muhurta Chintamani now detected:
  Nanda+Friday, Bhadra+Wednesday, Jaya+Tuesday, **Rikta+Saturday**,
  Purna+Thursday. Scores +1 per slot. The earlier implementation was
  missing Rikta+Saturday; the incorrect comment ("Rikta has no auspicious
  Vara partner") is removed.
- **Rikta dosha neutralization** — classical conditions reduce the Rikta
  penalty inside `score_tithi_class()`: Pushya nakshatra fully cancels
  (−2 → 0); Sarvartha or Amrita Siddhi Yoga partially offsets (−2 → −1).
  Both conditions surface as explicit reason notes.
- **Activity-aware tithi-avoid scoring** — `score_tithi_class()` extended
  with `avoid_tithi_class`: activities declare tithi families whose energy
  is classically mismatched, scoring −1 instead of the previous flat zero.
  Jaya (combat/victory energy) avoided by: ceremony, wedding, engagement,
  naming, annaprasana, karnavedha, mundana, upanayana, vidyarambha,
  gruhapravesha, yajna. Purna (completion energy) avoided by: court,
  litigation.

### Changed
- **Muhurta scorer split** — `personal/muhurta.py` (~1,200 lines) split
  into three focused files:
  - `personal/activity_rules.py` — declarative per-activity config
    (`ACTIVITY_RULES` dict, 28 activities); pure data, no logic.
  - `personal/slot_scorers.py` — atomic scoring functions + `_DayContext`
    dataclass; `score_tithi_class`, `score_tara`, `score_chandra`,
    `score_lagna`, `score_special_yogas`, `score_nitya_yoga`, etc.
  - `personal/muhurta.py` — orchestrator (~530 lines); public API
    (`day_slots`, `diagnose_day`, `assign_tiers`) unchanged.
- **`_DayContext` dataclass** — bundles 21 day-constant parameters so
  `_evaluate_slot()` takes `(s, e, block, base, facts, ctx)` instead of
  20+ positional arguments.
- **`_day_skip_reason()` helper** — day-skip logic extracted and shared
  between `day_slots()` and `diagnose_day()`, eliminating duplication.
- **MCP disclaimer updated** — `_MUHURTA_DISCLAIMER` in `tools.py` now
  reflects Siddha Yoga +1, symmetric tithi scoring (+1/−1/−2), and
  Pushya/Siddhi neutralization.

## [1.10.4] — 2026-06-17

The theme: **ayanamsa full support across gochara, ingress, and phalalu tools**.
`get_graha_positions`, `get_gochara`, `get_rasi_phalalu`, and
`get_rashi_ingresses` previously accepted an `ayanamsa` parameter but
always computed in Lahiri. All four now apply it end-to-end.
**+9 tests (1054 → 1063 passed).**

### Changed
- **`get_graha_positions`** — `ayanamsa` parameter now applied to all nine
  graha longitude and ingress calculations (previously Lahiri-only with a
  warning note in the response). Stale `ayanamsa_note` field removed.
- **`get_gochara`** — `ayanamsa` parameter added and applied; graha
  positions are now computed under the requested ayanamsa.
- **`get_rasi_phalalu`** — `ayanamsa` parameter added and applied; reading
  is rendered from positions under the requested ayanamsa.
- **`get_rashi_ingresses`** — `ayanamsa` parameter added and applied;
  sign-boundary crossings are computed under the requested ayanamsa.
- `gochara/positions.py` refactored: `graha_positions()` owns the Swiss
  Ephemeris sid mode (set once, restored in `finally`); internal helpers
  are now mode-agnostic, avoiding redundant `set_sid_mode` calls on every
  loop iteration of the ingress search.
- `ingress.py` refactored: same own-the-mode pattern in `rashi_ingresses()`.

### Documentation
- README and PyPI page updated: tool signatures show `ayanamsa="lahiri"` for
  all seven ayanamsa-aware tools; new Ayanamsa section lists the four
  supported keys and clarifies SS/Vakya accept-but-ignore behaviour.

([PR #105](https://github.com/socraticsurge/telugu-calendar-utilities/pull/105))

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

1.9.0 bundled **two rounds of work under a single release tag**: an
operational-maturity round (release safety, dependency hygiene, CI and
security hardening, contributor docs) merged first, then the headline
classical-muhurta-sharpening round (sixteen non-personal timing
computations). No engine math beyond additive fields; the frozen core
is untouched and ICS subscriber feeds are byte-identical. **+166 tests
overall (825 → 991 passed).** Both rounds are documented below.

### Headline — Classical muhurta sharpening: 16 timing computations (849 → 991)

Sixteen computations from Muhurta Chintamani, Brihat Samhita,
Dharmasindhu, and standard panchangam authority — all surface as
additive properties on `PanchangamDay` and across the three per-day
MCP response paths (`tool_get_panchangam`, `tool_get_muhurta`,
`tool_get_panchangam_range`). No personal-astrology computations
(Dasha, Navamsa, Kuta match) — those are reserved for a separate
project.

#### Added — Timing computations (16 features)

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

#### Changed

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

#### Notes

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

### Also shipped — Operational-maturity round (825 → 846)

Merged ahead of the timing work: release safety net, dependency
hygiene, dual-axis CI matrix, security scanning, contributor docs,
forward-year DP-verified festival regression, and a uniform table-
driven festival dispatcher. No engine math changes; +21 tests
(825 → 846 passed).

#### Added
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

#### Changed
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

#### Fixed
- **`server.json` version drift** — both top-level and `packages[0]`
  were pinned at 1.7.1 while PyPI shipped 1.8.0; the MCP registry was
  advertising the wrong package version. Now in lockstep with
  `pyproject.toml` and enforced by `tests/test_version_sync.py` + the
  publish-time gate.
  ([PR #74](https://github.com/socraticsurge/telugu-calendar-utilities/pull/74)).
- **`CODE_OF_CONDUCT.md` enforcement section had a blank email**
  ("reports go to … at ."). Filled in `cvk.atreya@gmail.com`.
  ([PR #75](https://github.com/socraticsurge/telugu-calendar-utilities/pull/75)).

#### Removed
- Three unused imports in `engines/vakya.py` (`_CIVIL_DAYS`,
  `_MOON_REVS`, `_MOON_APOGEE_REVS`) and a dead `d += timedelta(days=1)`
  rebind in `tool_get_panchangam_range`. Byte-identical behaviour.
  ([PR #95](https://github.com/socraticsurge/telugu-calendar-utilities/pull/95)).

#### Security
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

Aggregate across both rounds: 991 passed, 1 skipped (825 before this
release; +21 from the operational-maturity round, +142 from the
timing-computations round, +3 intermediate — +166 net). Zero
behaviour regressions.

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

## [1.7.1] — 2026-06-14

Patch release refining Muhurta finder tiering.

### Changed
- Muhurta slots now tiered by the empirical min/max score of the current
  search, so tiers are relative to each query's range.
- Reframed tier footnotes to present Good/Fair slots as genuinely
  workable, not merely runner-ups.

### Added
- Day-level dosha cap that downgrades slots on Rikta tithi, Visha/Dagdha
  yogas, and Vyatipata/Vaidhriti Nitya yogas.

## [1.7.0] — 2026-06-14

Major Muhurta scoring overhaul plus a full mobile app-shell redesign and
AstroChaganti rebrand.

### Added
- Graded Muhurta scoring engine: tithi-class and vara-activity scoring,
  Nitya Yoga scoring (Vyatipata/Vaidhriti), eclipse hard-skip, expanded
  24-entry activity taxonomy, and per-slot `day_slots` scoring with
  `dropped_days` transparency.
- `facts_at()` for slot-time anga precision, with a JavaScript Meeus port
  for matching slot-time accuracy in the browser preview.
- Relative tiering (Excellent/Good/Fair) with tier-first sort and a
  personal Chandra-dosha tier cap applied in both engine and JS.
- Mobile app-shell: top bar, bottom navigation, settings/subscribe
  drawers, swipe, per-screen titles, contextual help sheet, and
  Gochara/Tarabalam mobile screens.

### Changed
- Rebranded to Astro Chaganti Panchangam; adopted the astrochaganti.com
  Vellum light theme and ringed-glyph brand mark.
- Design refresh across the landing page: neutral cards, eyebrow labels,
  flatter shadows, rebalanced hero masthead.

### Fixed
- Reverted rogue AI-agent edits, restoring the landing page to its 1.6.2
  baseline before the redesign.
- Mobile fixes: always show Avoid windows, show the full Gochara chart
  before the Sade Sati banner, wrap Karana timings.

## [1.6.2] — 2026-06-13

Patch release hardening MCP Marketplace presence.

### Added
- `glama.json` manifest for the Glama MCP directory.

### Fixed
- Trimmed the registry description to the 100-character limit; corrected
  PyPI URLs.

## [1.6.1] — 2026-06-12

MCP registry manifest, ownership marker, and analytics.

### Added
- GoatCounter analytics tracking pageviews, growth-loop events, and share
  attribution.
- Tab subtitles carrying the devotee's question.

### Changed
- Tabs reordered to follow devotee cadence (Today; Gochara · Rasi Phalalu;
  Tarabalam · Muhurtam) and restyled as true equal-thirds segmented
  navigation.
- MCP section compressed to a button-first card; footer reduced to three
  lines.

## [1.6.0] — 2026-06-12

Daily Rasi Phalalu, a Muhurta finder, and a consolidated three-tab
structure.

### Added
- Muhurta finder surfacing ranked auspicious slots with per-reason point
  scores.
- Daily Rasi Phalalu: a deterministic daily reading derived from computed
  facts.
- Three-tab structure adding Muhurtam alongside Tarabalam, with full
  Phalalu sharing.

### Changed
- Polished panel anatomy, contextual date control, global time toggle,
  mobile chart labels, and accessibility.

### Fixed
- Ran the Gochara builder in module mode so the package resolves on CI;
  bumped GitHub Actions to Node-24-ready versions.

## [1.5.0] — 2026-06-11

Gochara rendered as a South Indian chart with transit verdicts.

### Added
- Gochara tab showing today's sky and transit verdicts from the user's
  rashi, with Brihat Samhita-style verdicts from the janma rasi.
- South Indian chart rendering with date selection.

### Changed
- Documented the sunrise-snapshot convention for Gochara.

### Fixed
- Gochara UX: single Viewing control, honest blank state, profile reset,
  and an explicit notice when a typed date falls outside the data window
  (with footnote pointing to MCP for any date).

## [1.4.0] — 2026-06-11

Graha positions groundwork for Gochara.

### Added
- Graha positions for all nine grahas, each with rasi, retrograde flag,
  and ingress dates.

## [1.3.0] — 2026-06-11

Chandrabalam joins the Tarabalam tool.

### Added
- Chandrabalam: rashi strength combined with Tarabalam, with a
  devotee-selectable standard (`janma_rasis`, `chandra_mode`) in
  `find_tarabalam_days`.
- Tarabalam WhatsApp share, completing the daily WhatsApp share flow.

## [1.2.0] — 2026-06-11

Tarabalam tool and project governance for post-conclusion feature work.

### Added
- `find_tarabalam_days` MCP tool and web tab finding favourable days for
  up to four birth stars.
- WhatsApp sharing of the selected day's panchangam from the preview
  header.
- Custom domain `panchangam.astrochaganti.com`.

### Changed
- Established working agreement, CI guardrails, contributing guide,
  security policy, PR/issue templates, and a Contributor Covenant Code of
  Conduct.

## [1.1.1] — 2026-06-11

Patch release naming monthly sign transitions.

### Added
- Feeds declare a `REFRESH-INTERVAL` / `X-PUBLISHED-TTL` of 12h; calendar
  name carries AstroChaganti's Panchangam branding.

### Fixed
- Monthly sign transitions are now named `<Rashi> Sankramanam` in MCP
  `special_days` and are no longer flagged as special days.

## [1.1.0] — 2026-06-11

The festival layer, plus engine and muhurta corrections verified against
Drik Panchang.

### Added
- Festival layer: 30+ named Telugu festivals, monthly vrats, and Ganda
  Moola nakshatra flagging, surfaced in MCP `special_days`.
- Feed-level named Ekadashis, night Choghadiya, and (+1)/(−1) day
  boundary markers.
- Devotee-focused preview upgrades: 12h time toggle, named Ekadashis,
  upcoming special days, and OG/social meta.

### Fixed
- Corrected muhurta window calculations against the Drik Panchang
  reference.
- Fixed tropical (Drik) rituvu, the ayanam sign-set, and the Surya
  Siddhanta manda equation.

### Changed
- Landing page now states the measured Surya Siddhanta accuracy (2–6 hour
  tithi drift) honestly; AstroChaganti branding and a two-column preview
  redesign.

## [1.0.6] — 2026-06-10

Adhika/Nija maasam detection and corrected eclipse visibility.

### Added
- Adhika/Nija maasam detection: a lunar month bounded by new moons in the
  same solar sign (no sankranti) is labeled `Adhika <name>` and the
  following month `Nija <name>` (detected live for Adhika Jyeshtha, 2026).

### Fixed
- Eclipse visibility now evaluates the whole eclipse window rather than
  just the maximum, correctly marking the 2026-03-03 total lunar eclipse
  visible at moonrise across India (and restoring its Sutak).

## [1.0.5] — 2026-06-10

Initial public release — the founding panchangam library, MCP server, and
ICS feed pipeline.

### Added
- Three calculation engines: **Drik Ganita** (Tithi, Nakshatra, Yoga,
  Karana with start/end times; solar/lunar rise-set; signs; ayanam;
  rituvu; temporal windows for Rahu Kalam, muhurtas, Choghadiya, Varjyam;
  Samvatsara/Maasam metadata; special-day flags), **Surya Siddhanta**
  (mean-motion plus manda correction), and **Vakya** (Surya Siddhanta base
  with a Moon correction table).
- ICS calendar feed generation for 22 cities × 3 systems, with full
  Panchangam day descriptions, ayanam/rituvu, and webcal + https subscribe
  links.
- FastMCP server (`mcp-server-panchangam`) exposing panchangam, muhurta,
  special-days, choghadiya, and multi-day `get_panchangam_range` tools,
  plus a location resolver (predefined cities with Nominatim fallback).
- Eclipse computation and special-yoga detection (including Dvipushkara
  and Tripushkara) surfaced in engines, ICS output, and MCP tools.
- Landing page with a live panchangam preview, city + system picker, date
  picker, and system guidance.
- GitHub Actions workflows for monthly feed generation, Pages deploy, and
  PyPI publishing on version tags.

### Performance
- Precompute eclipses once per generation run instead of per-day per-feed.

[Unreleased]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.13.0...HEAD
[1.13.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.12.0...v1.13.0
[1.12.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.11.0...v1.12.0
[1.10.4]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.10.3...v1.10.4
[1.10.3]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.9.0...v1.10.3
[1.9.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.7.1...v1.8.0
[1.7.1]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.6.2...v1.7.0
[1.6.2]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.0.6...v1.1.0
[1.0.6]: https://github.com/socraticsurge/telugu-calendar-utilities/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/socraticsurge/telugu-calendar-utilities/releases/tag/v1.0.5
