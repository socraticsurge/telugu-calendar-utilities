# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project uses
[SemVer](https://semver.org/spec/v2.0.0.html). The `mcp-server-panchangam`
PyPI version tracks this file's most recent release entry.

## [Unreleased]

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
