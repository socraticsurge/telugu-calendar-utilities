# Muhurta behavior-contract test map

Epic: [#593](https://github.com/socraticsurge/telugu-calendar-utilities/issues/593).
Tasks: #594 Python contracts, #595 browser journeys, #596 release verification.
Base: `614cc2f2893ab066c72118c7bcc811738e5bc657`.

This is a test-only reorganization, not a change to calculation behavior or an
expansion of test coverage. Existing production files, assertions, expected
values, parameter tables, storage schemas and release gates are unchanged.

## Where a failing contract belongs

| Python suite in `tests/` | Responsibility | Collected cases |
| --- | --- | ---: |
| `test_muhurta_finder.py` | Slot timing, transitions and input validation | 15 |
| `test_muhurta_finder_activity_rules.py` | Activity admission and scoring policies | 33 |
| `test_muhurta_finder_personal_scoring.py` | Personal strength, dosha and tier rules | 22 |
| `test_muhurta_finder_explanations.py` | Reasons, doctrinal notes and dropped-day explanations | 11 |
| `test_muhurta_finder_mcp.py` | Public MCP signatures and response contracts | 9 |
| `test_muhurta_finder_night.py` | Night-slot windows, ranking and timing | 12 |

`tests/muhurta_finder_support.py` holds the original Hyderabad/Drik engine setup
and the three original helpers. The tier helper uses equivalent early returns;
expected results have not been replaced by calls into different production logic.

| Browser suite in `src/__tests__/` | Responsibility | Collected cases |
| --- | --- | ---: |
| `muhurta-profile-scoring.test.ts` | Scoring, orchestration seams and activity guidance | 11 |
| `muhurta-profile-presentation.test.ts` | Result labels, disclosure, markup and share privacy | 13 |
| `muhurta-profile-chart-boundaries.test.ts` | Lagna evidence, cycle boundaries and chart screening | 16 |
| `muhurta-profile-panel.test.ts` | Saved/manual participants, roles, limits and focus | 11 |
| `muhurta-profile-storage.test.ts` | Storage failure, hostile text and legacy compatibility | 7 |

`src/__tests__/muhurta-profile/types.ts` contains the original test-facing types.
`fixtures.ts` contains the original storage doubles, DOM fixture and interaction
helpers. Each suite explicitly registers `usePanelFixture`; mutable bindings
remain in the suite, not in a shared singleton. Each test receives fresh storage
and mocks. Suites owning controllers destroy them before restoring mocks and
globals. The existing Vitest file isolation remains enabled.

## Preservation evidence

The adjacent JSON inventory records each original declaration's destination and
source hash, including Python assertion counts and both browser parameter tables.
It is a one-time relocation audit, not a permanent lock on future test evolution.

- All 254 Python assertion ASTs and 281 browser expectation statements are preserved.
- 95 Python tests and 41 browser declarations retain their original bodies.
- Three cases per language are structurally simplified as recorded in the JSON.
- The tier helper passes a differential check; the reason-sum oracle stays independent.
- Original parameter tables are unchanged; splitting yields 102 Python and 58 browser cases.
- Every split suite passes alone; both families also pass with shuffle seed 593.
- The full frontend suite has 1,733 passing tests; the increase is case separation, not new coverage.
- V8 coverage metrics are identical for all 89 reported production files and totals.
- Python Ruff and complexity debt baselines remain zero.

Focused commands:

```sh
python -m pytest tests/test_muhurta_finder*.py -q
npx vitest run src/__tests__/muhurta-profile-*.test.ts
```

Run one suite by naming its exact path when diagnosing a failure.
Full release gates remain `python -m pytest tests/`, frontend coverage, typecheck,
lint and the build; no gate, exclusion or threshold is loosened.

## Code health and stopping point

The initial relocation inherited complex tests and failed CodeScene's new-file
gate. Focused scenario splitting addresses that debt without threshold changes.
Final local and hosted results are recorded on the release task; types-only
declarations are unscored.
The original files scored 6.32 and 7.31 in hosted analysis 7588260.
File splitting changes the aggregation, so these are not like-for-like measures
of reduced calculation complexity. The practical gain is behavior-local tests,
explicit fixture ownership and focused failure diagnosis.
Keep #593 and #596 open until required PR checks, review, merge and hosted analysis
are verified; record final release evidence there.
