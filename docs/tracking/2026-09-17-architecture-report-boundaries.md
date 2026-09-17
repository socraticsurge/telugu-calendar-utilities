# Architecture-reporting maintenance

Epic: #598; tasks: #599 baseline, #600 boundaries, #601 release.
Base: `da4600b9803ba48c2aab137c032f58944e19469c`.

## What changed

The existing script remains the CLI and compatibility entrypoint for
`build_report`, `_summary`, `_layer` and `source_scope_class`.
Its internal responsibilities now have explicit homes under
`tools/architecture_report/`:

| Module | Owns |
| --- | --- |
| `repository.py` | Read-only Git commands, ref validation and pinned source reads |
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
Record immutable commit, review, merge and hosted CodeScene evidence on #601.
Check every extracted module; do not claim improvement from the original file alone.
Stop after this epic; profile-persistence changes are explicitly out of scope.
