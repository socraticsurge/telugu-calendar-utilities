# ADR 0002: Harden computation boundaries selectively; do not reactivate EngineCore

- **Status:** Accepted
- **Date:** 2026-08-27
- **Audience:** maintainers and reviewers of computation, MCP and browser work
- **Scope:** repository state at `c46e9f0850aa07d1db7b6d65f6ab50b2cb2f9972`
- **Owns:** computation-layer organization, duplication and refactor triggers
- **Review when:** a new engine variant is requested; a correctness defect is
  traced to engine inheritance; or a new scoring/MCP feature crosses the
  boundaries named below

## Decision

Keep the current frozen engines and additive module layout. Do **not**
reactivate the parked `EngineCore` design from size or symmetry arguments
alone. Improve the architecture through small contract-focused changes:

1. correct the browser computations that already violate their selected-system
   or canonical-vocabulary contracts;
2. generate stable shared vocabularies where Python and TypeScript have the
   same semantics;
3. keep the generated activity-profile contract as the preferred ownership
   pattern;
4. document the actual bidirectional engine/derived assembly boundary;
5. defer broad MCP, Muhurta and engine restructuring until a named trigger is
   met; and
6. keep every correction or extraction in its own issue, branch and PR.

This is a targeted correctness and change-efficiency decision, not a claim
that the present file layout is ideal forever.

## Reproducible evidence

The static report reads the exact Git tree and the last 200 non-merge commits
at the selected ref. It maps imports, computation owners/mirrors/consumers,
cross-layer edges, direct test blast radius, private API use, engine method
asymmetry, duplicate contract groups and file change concentration.

The JSON report retains schema version 1. Its source-count fields have these
stable meanings:

| `scope` field | Meaning |
|---|---|
| `source_files` | Total production Python and TypeScript modules. This is the original schema-v1 contract. |
| `established_source_files` | Modules in the established computation layer, excluding allowlisted additive feature modules. |
| `additive_feature_source_files` | Allowlisted feature modules layered around the established computation layer. |
| `total_source_files` | Explicit total, equal to `source_files` and to the sum of the established and additive counts. |

```bash
python tools/analyze_computation_architecture.py \
  --ref c46e9f0850aa07d1db7b6d65f6ab50b2cb2f9972 \
  --commits 200 --summary
```

At that ref the report contains 78 production Python/TypeScript modules, 116
test files and all 62 computation records. The history window is exactly 200
non-merge commits, from `48d134dccebccc77e6251881280cd7a68c106ffc` through
`81f292553a2ba22188fb6d6928630c8be9736cc0` among the measured source paths.
The numbers below are evidence inputs, not architecture scores.

| File | Nonblank lines | Changed commits | Added + deleted lines | Direct linked tests | Computation IDs | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| `src/panels/tarabalam.ts` | 1,392 | 33 | 1,988 | 11 | 7 | UI, browser astronomy and manual scorer mirrors share one boundary; correctness risk is higher than size alone suggests |
| `telugu_panchangam/mcp/tools.py` | 1,239 | 62 | 1,466 | 59 | 0 owner IDs | High-change adapter/orchestration surface; heavily tested, but no computation should originate here |
| `telugu_panchangam/personal/activity_rules.py` | 1,087 | 53 | 1,985 | 43 | 1 | Mostly declarative, one Python owner, generated browser contract and per-profile provenance; size does not justify splitting it now |
| `telugu_panchangam/personal/muhurta.py` | 895 | 52 | 4,061 | 38 | 1 | Highest measured churn and a 283-line definition; rules and atomic scorers are already extracted, but orchestration remains a future split candidate |
| `telugu_panchangam/engines/base.py` | 508 | 16 | 785 | 13 | 16 | Large correctness blast radius but relatively low recent change; frozen-core posture is working as intended |

### Import and output-consumer map

The complete module and 62-record output-consumer maps are emitted in JSON by
the same command without `--summary`. Important current boundaries are:

- `PanchangamDay` is the central public result, but engine finalization is not
  one-directional. `engines/base.py` imports ten additive derived modules to
  populate fields such as Ghati, Vishaghati, Bhadra, Panchaka, special Yogas,
  month flags and Sankramana avoidance.
- Derived calendar modules import `engines/utils.py` for Julian-Day, sunrise
  and sidereal helpers. This creates an engine/derived utility seam, not a
  cycle through the engine classes.
- MCP, build and Muhurta code import the three concrete engine modules because
  `engines/__init__.py` is empty. The root architecture's earlier example
  `from telugu_panchangam.engines import DrikGanitaEngine` is not a supported
  façade today.
- MCP imports private `_validate_ayanamsa`, `_nak_index` and `_rasi_index`;
  `personal/homa.py` calls `engine._sun_longitude_func`. These are test-covered
  boundary leaks, not reasons to edit the frozen core in this assessment.
- Every computation record lists its Python owner, TypeScript mirror where
  applicable, public surfaces and direct tests. MCP serialization is a
  consumer/adaptor even where its file has no owner ID.

### Duplicate contract map

The analyzer records eight cross-surface contract groups. Activity profiles
already use the selected pattern: Python owner → generated JSON → check-mode
generator → browser consumer. Seven other groups remain manual mirrors:

1. Rashi vocabulary (four locations);
2. Nakshatra vocabulary;
3. Nitya Yoga names and disposition;
4. special-Yoga tables;
5. Hora tables;
6. Homa election rules; and
7. named Shani conditions.

Manual duplication is not automatically wrong. Homa and named-Shani mirrors,
for example, have focused tests. It becomes a consolidation priority when the
same semantics can be generated without moving executable judgment into data,
or when a real mismatch appears.

Two real mismatches did appear:

- the browser slot evaluator always uses Meeus/Lahiri astronomy, even after a
  user selects Surya Siddhanta or Vakya ([#182](https://github.com/socraticsurge/telugu-calendar-utilities/issues/182));
- the browser emits `Priti`, `Shula`, `Variyana` while Python owns `Preeti`,
  `Shoola`, `Variyan`, bypassing some Nitya-Yoga lookups
  ([#183](https://github.com/socraticsurge/telugu-calendar-utilities/issues/183)).

The shared-vocabulary prevention work is isolated in
[#184](https://github.com/socraticsurge/telugu-calendar-utilities/issues/184).
Previously found output-contract defects remain separate in
[#179](https://github.com/socraticsurge/telugu-calendar-utilities/issues/179)
and [#180](https://github.com/socraticsurge/telugu-calendar-utilities/issues/180).

## Three efficiency questions

### 1. Runtime efficiency

The current Python paths do not provide a runtime driver for a core rewrite.
The repeatable comparison command is:

```bash
python tools/benchmark_computation_paths.py \
  --start 2026-01-01 --days 30 --runs 3 --facts-per-day 4
```

On the recorded Apple-silicon/macOS/Python 3.11.15 run, warm 30-day Hyderabad
calculation medians with eclipse search disabled were 0.169 seconds (Drik),
0.065 seconds (Surya Siddhanta) and 0.067 seconds (Vakya). Evaluating 120 slot
facts took 0.0020, 0.0004 and 0.0004 seconds respectively. These figures are
hardware-dependent and not CI thresholds; they show only that no measured
Python bottleneck currently pays for an `EngineCore` migration.

The browser's local approximation is fast and static-host friendly, but its
selected-system mismatch is a correctness problem. #182 must compare compact
generated transition data against keeping client-side calculations before any
runtime/data-size decision.

### 2. Developer change efficiency

Change concentration is highest in MCP tools, activity profiles, Muhurta
orchestration and the Tarabalam panel. Their treatments differ:

- keep declarative activity profiles together while their generator,
  provenance audit and profile tests isolate changes;
- generate identical vocabularies rather than retyping them;
- make MCP remain an adapter and split it by domain only when the next tool or
  shared validation change would otherwise enlarge `mcp/tools.py` again;
- use #182 as the trigger to establish a pure browser slot-fact boundary, but
  do not hide its correction inside an unrelated panel rewrite; and
- split Muhurta day admission, candidate construction and ranking only when a
  new scoring signal needs to cross more than one of those phases.

### 3. Correctness and verification risk

Engine and scorer files have large direct test blast radii. That makes a broad
rewrite more expensive, not more urgent. The safe verification unit is the
stable computation ID and its existing public outputs:

- frozen-engine work requires explicit owner approval and multi-city,
  multi-date external comparison plus byte/field parity where relevant;
- a browser mirror needs cross-language boundary fixtures, not merely separate
  Python and TypeScript unit tests that encode the same mistake;
- generated data needs a check-mode command and stale-artifact test;
- MCP extraction must retain all 17 tool signatures and serialized responses;
  and
- an internal split must prove unchanged public output before claiming lower
  correctness risk.

## Recommendation record

| Classification | Affected boundary | Expected benefit | Migration/correctness risk | Verification strategy | Owner approval? |
|---|---|---|---|---|---|
| **Keep** | `activity_rules.py` as one declarative owner | One auditable catalogue and stable generation order | Splitting now would add imports/order failure modes without reducing rule semantics | Existing provenance, export, selector and per-profile tests | No, while behavior is unchanged |
| **Clarify boundary** | engine finalization ↔ additive derived fields | Accurate mental model; contributors know that `PanchangamDay` assembly is an aggregator | Documentation-only | Analyzer edge map + computation inventory | No |
| **Correct, then split narrowly** | browser slot facts inside `tarabalam.ts` | Selected-system correctness and an independently testable pure boundary | High: changes candidate admission/scoring near transitions | #182 differential fixtures for 3 systems, multiple dates/cities; screenshots for visible changes | UI sign-off; no frozen-core approval if engines remain untouched |
| **Consolidate/generate** | stable Python/TypeScript vocabulary arrays | Removes typo/order drift while keeping one owner | Medium: transliteration aliases and display spellings can be lost | #183 correction first; #184 generated artifact check + full browser parity | No frozen-core approval; UI sign-off for visible labels |
| **Clarify, then defer** | MCP private validators/index helpers and empty engine package façade | Makes supported API explicit without inventing a premature public library | Medium if engine imports change; current private calls are test-covered | Preserve 17 signatures/responses; add import-contract tests when a façade is proposed | Yes if any frozen engine/utility file changes |
| **Split on trigger** | `mcp/tools.py` by tool domain | Smaller review surface and less merge contention | Medium: serialization/signature drift | Snapshot every tool schema/response and keep `mcp/server.py` thin | No unless computation behavior changes |
| **Split on trigger** | `personal/muhurta.py` admission, candidates, ranking | Localized scoring changes and smaller function-level blast radius | High because ordering, reasons and tier caps are public behavior | Cross-surface golden candidates/reasons plus full current tests | No for byte/field-identical extraction; yes if frozen inputs change |
| **Defer** | parked `EngineCore` composition design | Would reduce method-name duplication and make variants pluggable | Very high: 3 systems, 16 base-owned computation IDs, many consumers and frozen tests | Dual-run byte/field parity, forward external fixtures, bulk benchmark | **Yes; explicit owner approval required** |

## Why EngineCore remains parked

The analyzer confirms asymmetry: Drik and Surya Siddhanta directly subclass
`PanchangamEngine`; Vakya subclasses Surya Siddhanta; ten method names are
defined in all three concrete classes. It also confirms why this is not enough
to reactivate the old plan:

- no new engine variant is requested;
- recent engine change concentration is below the MCP/scoring/browser
  hotspots;
- the local runtime comparison exposes no current performance problem;
- #176 concerns the source and fidelity of the provisional Vakya lunar model,
  not a defect caused by inheritance duplication;
- #177 concerns the shared rise/set convention, not divergent duplicated
  method bodies; and
- the new concrete defects #179, #180, #182 and #183 all live outside the
  engine inheritance problem.

Reactivation requires either a requested fourth engine/system variant or a
verified bug whose cause is duplicated/inherited engine orchestration. At that
point the old design is an option to reassess, not a pre-approved migration.

## Consequences

- The repository gains repeatable architecture and runtime evidence tools,
  but no runtime module or frozen test assertion changes.
- Large files are not split merely to improve a line-count statistic.
- Browser calculation parity becomes the first correctness priority from this
  assessment.
- Generated contracts are preferred for stable shared data; executable rules
  remain code with differential tests unless safe generation is demonstrated.
- Deferred refactors retain explicit triggers, risks and approval gates instead
  of returning as unbounded cleanup work.
