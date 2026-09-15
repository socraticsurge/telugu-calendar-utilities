# ADR 0003: Incremental calculation-boundary repair

Status: repair merged; production pilot enabled through `.env.production` after sidecar publication is verified.
Owner approval: architecture repair and structural inventory-test updates approved.
Baseline: `e05eb3ba32be613e53832092588e996bb56558fe`.

## Decision

Keep the verified behavior, existing subscriber format and protected engines.
Replace responsibilities at their boundaries, rather than pursue a whole-project rewrite.
This is a scoped repair, not a claim that every browser panel is now strictly typed.

```mermaid
flowchart TD
    UI[Browser input adapter] --> BR[Typed browser search input]
    MCP[MCP input adapter] --> PR[Typed Python search options]
    Core[Protected calculation engines] --> Facts[Calendar facts]
    Facts --> Export[Versioned day-data export]
    Export --> BR
    Facts --> PR
    Rules[Python-owned shared tables] --> Generated[Checked generated browser tables]
    Generated --> BR
    PR --> Service[Transport-independent search service]
    Service --> Raw[Ranked slots with aware instants]
    Raw --> Response[MCP formatting and result limit]
    BR --> Browser[Browser evaluation and typed ranking]
    Browser --> View[Existing result presentation]
```

The arrows describe responsibility and data flow, not a new shared runtime.
The browser and Python implementations remain distinct.

## Completed repair sequence

1. Pin shared ranking boundaries with one hand-authored corpus consumed by both runtimes.
   Preserve MCP signatures and byte-level results with a baseline corpus.
   Define explicit browser inputs and Python search/result contracts.
2. Move multi-day search, night handling, diagnostics and ranking out of MCP formatting.
   Return all raw candidates with timezone-aware instants; the MCP adapter formats and limits them.
   Replace mutation of caller-owned score explanation buckets with returned contributions.
   Move browser ranking into the strictly checked calculation area.
3. Export the seven audited manual table/contract groups from their existing Python owners.
   Validate the generated artifact in the full Python gate.
   Preserve the browser's historical Yoga aliases and supported-rule subset.
4. Generate `.days-v1.json` beside the unmodified `.ics` feeds.
   Validate version, city, system, timezone and nested field types before using data.
   Migrate Today and the Muhurta day pipeline to the day-data adapter.
   Keep the legacy reader as a compatibility fallback during the pilot.

## Contracts intentionally not unified

- MCP accepts at most 14 days and presents at most 12 slots.
- Browser search retains its 60-day cap, personal-preference tie-break and chart screening.
- Python has 35 canonical activity profiles; the browser exposes its existing 30-profile subset.
- The browser's approximate Yoga names retain Priti/Shula/Variyana.
- Night slot tie-breaks retain local-clock ordering, rather than silently switching to UTC order.
- Generated day views retain minute precision and the old relative-date markers.
- ICS summaries/descriptions remain opaque display/legacy strings in the sidecar.
  Structured facts are projected from engine objects, never reconstructed from those strings.
- Domain source claims and rule semantics are unchanged; engine-pinned fixtures are not independent astronomical verification.

## Verification and material change tests

- `tests/test_muhurta_ranking_contract.py` and the matching frontend test share independent expected boundaries.
- `tests/test_muhurta_mcp_compatibility.py` pins the original signature and nine complete serialized responses/errors.
- `tests/test_muhurta_search_boundary.py` proves the service returns unformatted, untruncated results without MCP imports.
- `tests/test_shared_calendar_tables.py` rejects generator drift and pins intentional aliases.
- The 48-day structured-data corpus covers three systems, two cities, an eclipse, DST and cross-midnight data.
- `src/__tests__/calendar-data.test.ts` replaces description wording while asserting unchanged structured facts.
- `tests/test_structured_calendar_browser.py` exercises the built Today and Muhurta journeys at mobile and desktop widths.
- Existing behavioral assertions and coverage thresholds remain; only structural/release metadata and loader mocking change.
- Architecture tests compare a committed revision against its own committed inventory ledger, avoiding pre/post-commit count mismatches.

## Rollout and rollback

The repair landed with the pilot disabled; the activation release sets the flag
in `.env.production` only after verifying published sidecars for every city/system.
This separates feed publication from activation without changing workflows or CNAME.

1. Generate feeds with the existing `python -m telugu_panchangam.generate` entry point.
   The existing feed-publication script copies both ICS and day JSON; workflows and CNAME remain untouched.
2. Verify sidecars for the supported city/system combinations before enabling the public build.
3. Set `VITE_STRUCTURED_CALENDAR_ENABLED=true` for the browser build to activate the pilot.
   An explicit `false` disables it, including local query overrides.
4. For local browser inspection only, use `?calendarData=structured#today` or `#tarabalam` on loopback.
5. Roll back by building with the flag disabled; subscriber feeds and stored profiles are unchanged.

The production flag is committed in `.env.production`; ordinary production builds
therefore preserve activation during future feed regeneration. A flag-only change
does not match the landing workflow's path filter: dispatch `deploy-landing.yml`
after merging it and verify the published asset. Do not change workflow protections.

The legacy browser suite builds with an explicit `false` flag, preserving its
offline ICS fixtures. The separate structured browser suite builds with `true`
and uses ordinary URLs without query overrides. It verifies Today and Muhurta
at two viewport widths, plus missing, invalid and network-failure fallback.
The current hosted frontend job runs the legacy suite; run the structured suite
locally as a release gate until a separately approved workflow update includes it.

The full September 2026 generation covers 22 cities, three systems and 36,102 days.
Every structured day was compared with the existing description parser.
This proves compatibility, not independent astronomical accuracy or faster downloads.

No public activation, workflow dispatch or feed publication is implied by local verification.
Broad replacement of remaining panels, engine unification and API feature parity are outside this repair.
