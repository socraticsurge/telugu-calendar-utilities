# Architecture-reporting maintenance

Epic: #598; tasks: #599 baseline, #600 boundaries, #601 release, #603 Git hardening.
Base: `da4600b9803ba48c2aab137c032f58944e19469c`.

## What changed

The existing script remains the CLI and compatibility entrypoint for
`build_report`, `_summary`, `_layer` and `source_scope_class`.
Its internal responsibilities now have explicit homes under
`tools/architecture_report/`:

| Module | Owns |
| --- | --- |
| `repository.py` | Named read-only Git operations and pinned source reads |
| `git_validation.py` | Exact command grammar and typed ref, commit, path and history-limit validation |
| `scope.py` | Existing source membership and ordered layer classification |
| `parsing.py` | Pure Python/TypeScript source parsing and import resolution |
| `graph.py` | Dependency edges, private-import evidence and linked tests |
| `history.py` | Git history collection and independently testable numstat aggregation |
| `contracts.py` | Existing engine-shape and duplicate-contract evidence |
| `evidence.py` | Module, consumer, layer and change-impact facts |
| `report.py` | Stable report-schema composition |
| `presentation.py` | Stable human-readable summary |

`SourceSnapshot` binds reads to one resolved commit; `ModuleRelations` groups
the four related maps used for module evidence without introducing global state.
No calculation engine is executed by the reporter.

The substantive simplifications are separate import/attribute recognition,
numstat validation, registry test-link attachment and report-field assembly.
They remove nested or compound decision logic while retaining its outcomes.

## Compatibility and non-goals

JSON schema, field values, array ordering, summary wording, CLI options,
exit behavior and the supported imported entrypoints are preserved.
Existing test assertions, production modules, frozen engines, workflows,
storage schemas and CodeScene rules are untouched.

This deliberately does not expand the analyzer's evidence claims.
TypeScript parsing remains line-oriented: multiline imports and dynamic imports
are not newly inferred, and parent-directory path normalization is unchanged.
The report measures direct links, not proven transitive runtime reachability.
Any enhancement to those semantics needs separate tests and approval.

## Reproducing the fixed-commit parity gate

The adjacent `2026-09-17-architecture-report-parity.json` contains pre-refactor
SHA-256 references for three immutable commits with history limits 1, 20 and 200.
For each case, run the existing CLI with its `--ref` and `--commits` values;
hash stdout as UTF-8, including the trailing newline.
Repeat with `--summary` and compare the corresponding hash.
These six outputs must remain byte-identical, not merely structurally similar.
Full history is necessary; a shallow clone is not equivalent input.

The direct script also runs from outside the checkout, while the module
entrypoint remains `python -m tools.analyze_computation_architecture`.
Focused new tests cover parsing limitations, history deduplication and ordering,
Git/ref validation, symbol matching, field ordering, and CLI errors.
The existing integration tests continue to exercise whole-report evidence.

Required release gates remain the full Python/browser suite, frontend coverage,
typecheck, lint, build, zero-debt baselines, exact-patch review and hosted CI.
Both CodeScene and SonarQube must pass on the exact release commit.
Inspect their actual findings as well as the gate badges; release requires no
unreviewed new security, reliability or maintainability findings.
Neither maintainability improvements nor a prior false-positive decision waive
security validation; new findings require source-to-sink analysis and adversarial tests.
Record immutable commit, review, merge and hosted CodeScene evidence on #601.
Check every extracted module; do not claim improvement from the original file alone.
Stop after this epic; profile-persistence changes are explicitly out of scope.

## Git boundary hardening

Adversarial validation showed no hostile ref could reach Git through the current
CLI, but the internal generic helper could accept `show --output=...` and write
a file. This capability also existed before the refactor; it was not a safe
boundary for future callers. Task #603 closes it instead of relying on callers.

Named operations resolve a ref, read a pinned blob, list paths, and read bounded
history. The shared process-launch boundary additionally requires an exact
command shape, including the fixed history pathspecs. Direct compatibility calls
cannot add options. Source snapshots and direct reads require pinned commit IDs.
No shell is used. Existing supported CLI inputs and report bytes remain unchanged.

New tests reproduce and block the actual file write, inject options at every
argument position, check direct named-operation bypasses, and use a detectable
Git sentinel to prove hostile CLI refs fail before execution. Real Git controls
check blob/history reads, option-looking filenames and revision pinning.
Git itself, its configuration and the local execution environment remain trusted;
this reporting tool is not a sandbox for hostile Git installations.
