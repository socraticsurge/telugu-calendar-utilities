# MCP handler code-health repair

Bounded task: [#582](https://github.com/socraticsurge/telugu-calendar-utilities/issues/582).
Baseline: `fe459236c718cacb2c787188b6261cb7f3ab58f8`.
Package metadata: `1.18.16`; this does not itself publish a PyPI release.

## Responsibilities

```text
MCP public tool signatures (unchanged)
  -> tools.py: validate inputs, resolve location, invoke existing domain owners
  -> calendar_response.py: format computed days, windows, flags and event labels
  -> JSON response (unchanged)
```

Daily Panchangam, Muhurta, Hora and Lagna handlers now share request orchestration.
Date-range, coordinate, planet and name checks have one implementation each.
Participant validation and Chandra annotation no longer contain deep nesting.
Repeated windows/flags serializers now have one owner across day/range tools.
Monthly eclipse preparation and notable-day selection have explicit helpers.

No calculation moved between the browser and backend; no engine was changed.
No ICS, UI, deployment workflow, source claim, ranking or profile-store change.

## Health evidence

Local CodeScene MCP reviews on 2026-09-16, using unchanged metric configuration:

| Module | Before | After |
|---|---:|---:|
| `telugu_panchangam/mcp/tools.py` | 4.67 | 9.09 |
| `telugu_panchangam/mcp/calendar_response.py` | New | 10.00 |

Both origin and extraction were measured; complexity was not moved unmeasured.
The remaining handler warnings are module size and argument counts.
Public signatures are deliberately retained rather than changed to improve a score.
The hosted historical analysis is separate; these are not dashboard-rerun results.

## Compatibility evidence

- Capture 42 byte-level response hashes from the unmodified baseline before refactoring.
- Pin all 17 public tool signatures; retain the pre-existing Muhurta byte fixtures.
- Cover all three engines, alternate ayanamsa, eclipse/festival dates and London DST.
- Cover coordinate bounds, partial coordinates, input-error precedence and range limits.
- Assert altitude preservation for combustion but not ordinary city resolution.
- Assert Tarabalam skips empty rashi while Muhurta validation still rejects it.
- Assert null projection, decimal rounding, special-event ordering and Makara deduplication.
- Assert unexpected exceptions are logged without exposing private details in responses.
- Run 160 additional direct baseline/refactor byte comparisons across three cities,
  three systems, four dates and malformed inputs; every comparison matched.

Snapshots establish compatibility, not independent astronomical correctness.
Frozen calculation assertions remain unchanged.
Owner approval covers the package-version and audited-source-count assertions,
plus adding the new serializer to the explicit architecture boundary-adapter allow-list.
The new serializer remains visible in the computation inventory and architecture graph.

## Verification and review

Final full-suite, frontend, branch-review and protected-merge results are recorded
in the linked pull request; implementation is not complete until those checks pass.
Review focuses on preserved field order, validation precedence, per-tool date limits,
known-city altitude, exception handling and the immutable-HEAD architecture tests.
The review is an assistant self-review, not an independent human approval.

Local pre-commit CodeScene safeguard: quality gates passed (seven eligible files).
Full Python and built-browser suite: 1,988 tests passed on Python 3.11.
Frontend: 1,686 tests passed; lint, typecheck, site and documentation builds passed.
Python 3.11 wheel/sdist built and passed dependency, license and source verification.
An initial sandbox run could not bind browser-test ports; reruns use local-server permission.
The patch release appends a no-change Raman successor audit; prior audit fixtures stay intact.

This completes only the bounded MCP task when merged, not the wider code-health plan.
API client validation, Muhurta rules and profile/storage workflow debt remain separate tasks.
