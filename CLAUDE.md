# Working agreement

This project's core was concluded on 2026-06-11 and is in maintenance. New features
are built one at a time, as additions layered on the core — never by reworking it.

## Frozen core — do not modify without explicit owner approval

- `telugu_panchangam/engines/` — the three calculation systems (Drik, Surya
  Siddhanta, Vakya), muhurta windows, festival rules. All values are verified
  against drikpanchang.com and pinned in tests. The only routine change allowed
  here is **appending** a festival row to the rules tables in `base.py`, with a
  reference-verified test.
- `telugu_panchangam/generators/ics.py` — the feed format subscribers depend on.
- `.github/workflows/` — deploys carry `cname: panchangam.astrochaganti.com`;
  never remove it.
- Existing tests are the contract. A new feature that requires changing an
  existing test assertion is touching the core — stop and ask.

> **Status (2026-06-17):** the frozen core stands. The `EngineCore`
> engine-unification refactor (improvement-plan "Phase 6") that would relax
> this is **designed but parked** — not active work — and revisits the
> constraint only on a real driver (a new engine variant, or a bug that traces
> to the engine-inheritance duplication). `ARCHITECTURE.md` is kept consistent
> with this; if you ever decide to unfreeze, change it *here* first.

## How new features land

1. One feature at a time, on a feature branch — `master` always stays releasable.
2. New capability goes in **new modules** (e.g. `telugu_panchangam/personal/` for
   Tarabalam/horoscope work) that *consume* engine outputs, never modify engines.
3. Tests first; timing or jyotisha claims verified against drikpanchang.com day
   pages before merge (several dates, more than one city).
4. UI changes need screenshots and owner sign-off before pushing.
5. Merge to master only when the feature is concluded; then stop.

## Project rules

- Commits authored solely as `Socraticsurge <cvk.atreya@gmail.com>` — no
  Co-Authored-By trailers, no other identities.
- English only in user-facing text; transliterated terms (Tithi, Varjyam) as-is.
- Engine or MCP changes bump the PyPI version (`mcp-server-panchangam`).
- Run `python -m pytest tests/` before any commit; the full suite must pass.
