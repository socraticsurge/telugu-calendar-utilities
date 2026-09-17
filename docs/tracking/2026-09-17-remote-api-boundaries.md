# Browser remote API boundary epic

Epic: [#588](https://github.com/socraticsurge/telugu-calendar-utilities/issues/588).
Tasks: #589 characterization, #590 implementation, #591 release verification.
Base: `4feb25a2cdd1689851a4f2a50568267b38858b39`.
Branch: `codex/remote-api-boundaries`.

## Scope and dependency direction

- Keep the birth and election API facades and all existing public exports.
- Keep endpoint activation, URLs, payloads, privacy settings, deadlines and errors.
- Put shared chart invariants in `src/lib/chart-contracts.ts`.
- Make persistence consume those invariants without importing an API client.
- Put civil-time conversion in `src/lib/local-chart-time.ts`.
- Separate response parsing from trusted URL policy and JSON request primitives.
- Keep the endpoints' intentionally different abort classification policies.
- Do not move computation between browser and server or change persisted schemas.
- Leave frozen engines, subscriber ICS output and deployment workflows unchanged.

## Evidence

The new compatibility tests passed against the original code before refactoring.
All 1,725 frontend tests passed after the split, with lint and typecheck passing.
The first complete Python/browser run passed 2,047 tests; only the exact inventory
source-count assertion failed because nine modules increased 167 sources to 176.
The full site/documentation build passed.

A temporary differential harness compared original and refactored responses under
field mutations and civil-time conversion across six time zones, eight dates and
ten minute values; all three comparison tests passed.
The temporary baseline copies were removed, not included as duplicate source.

Local CodeScene reviews: birth API 5.99 to 9.60; election API 4.71 to 10.00.
New executable helpers score 10.00; the types/error contract has no numeric score.
These are local review results, not a new hosted analysis.

Final staged CodeScene safeguard: passed, 20 eligible files checked, no degraded
files; both API entry points improved.
The final full Python/browser rerun again passed 2,047 tests with only the
unapproved source-count assertion failing; frontend tests remain 1,725 passing.

## Release gate

The owner approved changing only the existing inventory assertion from 167 to
176 on 2026-09-17; the exact-output assertion and all behavior assertions remain.
After that update, all 2,048 Python/browser tests and 1,725 frontend tests passed;
lint and type checking passed as well.
Review the exact final patch, then merge only with passing hosted checks and
sole-author identity.
Hosted mapping additions retain the existing components: `src/lib/remote-api/**`
belongs to Browser - remote API boundary; `chart-contracts.ts` and
`local-chart-time.ts` belong to Browser - shared data contracts.
Keep #588 and #591 open until release and hosted verification are complete.
