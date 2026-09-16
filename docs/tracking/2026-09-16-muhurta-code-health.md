# Muhurta calculation-boundary repair

Bounded task: [#584](https://github.com/socraticsurge/telugu-calendar-utilities/issues/584).
Baseline: `f8fa03da823fa915156e50ab658b8269acbab77e`.
Priority signal: hosted architecture analysis `7580455` identifies personal scoring
as a frequently changed component and Muhurta as its lowest-health file.

## Responsibilities

```text
MCP search / other Python callers
  -> muhurta.py: unchanged public API, day/night orchestration and ranking
       -> muhurta_eligibility.py: day and slot admission rules
       -> muhurta_slot_scoring.py: compose existing atomic contributions
            -> muhurta_explanations.py: ordered cautions and explanation buckets
            -> slot_scorers.py: existing atomic scoring rules
```

Repeated day/night candidate evaluation and traditional admission checks now have
one owner. Daytime-only filtering and night-only Nishita bonuses remain distinct.
No engine, ICS, UI, MCP interface, deployment workflow or source claim changed.
Runtime locations are unchanged: this is Python responsibility separation, not
moving existing browser calculations to a server.

## Health evidence

Local CodeScene MCP reviews on 2026-09-16, with unchanged metric configuration:

| Module | Before | After |
|---|---:|---:|
| `personal/muhurta.py` | 4.95 | 9.38 |
| `personal/muhurta_eligibility.py` | New | 9.09 |
| `personal/muhurta_slot_scoring.py` | New | 9.09 |
| `personal/muhurta_explanations.py` | New | 9.68 |

The origin and every extraction are measured; none hides relocated low-health code.
Remaining argument-count warnings include deliberately preserved public signatures.
These are local reviews, not a claim about an as-yet-unrun hosted analysis.

The local change safeguard does **not** pass: it treats residual warnings in new
files as introduced debt. Eligibility and scoring retain moderate mean complexity;
the three new files retain some argument-count warnings. This is a reviewed
tradeoff, not a suppressed check: all extracted owners exceed 9, long/complex
functions are removed, and public interfaces remain compatible. No metric rules,
exclusions or thresholds were changed. The original file's improvement alone
must not be presented as a clean whole-change safeguard.

## Compatibility and approval

- Capture fixture hashes before modifying production code at the baseline above.
- Preserve 1,296 request combinations, each covering day slots, night slots and diagnosis.
- Include every activity, all Chandra modes, supplied/absent slot engine, three
  calculation systems, two cities and both London DST transitions.
- Pin public signatures and retain the existing byte-level MCP response fixtures.
- Compare 5,184 additional direct baseline/refactor day/night calls byte-for-byte,
  covering absent, empty, single and paired participants, birth Lagnas and Sydney.
- Guard transport-independent imports, rejection precedence and day/night differences.
- Existing behavioral assertions and frozen calculation files remain untouched.
- Owner approval covers inventory counts, module mappings and the 1.18.17 metadata
  assertion; an append-only reversible source audit preserves all older fixtures.
- Package metadata is 1.18.17; no tag or PyPI publication is part of this task.
- Register three computation owners and architecture nodes: 216 implementations,
  152 audited files, still 69 computations and 92 established source files.

Snapshots prove sampled compatibility, not independent astronomical correctness.
They do not cover every date, latitude or participant configuration.

## Verification and completion

Full-suite, frontend, review and protected-merge results are recorded in the PR.
The task is not complete until those checks pass and the hosted rerun is checked.
Review must check output order, rule precedence, temporal facts and engine fallback.
Assistant self-review does not constitute independent human approval.

Local verification on 2026-09-16: 2,030 Python and built-browser tests passed.
Frontend: 1,686 tests passed; lint, typecheck and standalone site/docs build passed.
Locked dependencies and 1.18.17 wheel/sdist source, dependency and license checks passed.
The initial full run found the moved daylight test hook; it was restored without
changing its assertion. The protected-source failure was resolved with the approved
append-only audit. An initial concurrent documentation build conflicted over `dist/`;
the standalone rerun passed. No failed check was removed or loosened.

Browser-journey investigation and API-client cleanup remain separate follow-up tasks.
Completing this task does not complete the wider maintenance backlog.
