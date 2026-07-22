# Activity Provenance States

Every Muhurtam activity has exactly one machine-readable provenance
disposition. The disposition describes the authority of the activity-specific
profile; it does not certify the astronomical engine or shared scoring layers.

| Rule field | Required ledger state | Meaning |
|---|---|---|
| `source_claim` | `verified` | Implemented activity criteria match the precisely located source within the recorded scope |
| `audit_claim` | `contradicted` | An inspected source exposes a rule or taxonomy conflict that remains visible pending an approval-gated correction |
| `heuristic_claim` | `heuristic` | The behavior is intentionally project-defined or source-neutral and makes no claim of classical authority |

The fields are mutually exclusive. `tools/check_activity_provenance.py` fails
for unknown claims, wrong surfaces, wrong states, duplicate claims or an
activity with no disposition. `tools/export_activity_rules.py` carries the same
field into the browser contract, while `tool_find_muhurta` returns it in
`activity_profile` for MCP consumers.

## The neutral `any` selector

`Anything auspicious` is the sole heuristic activity profile. It contributes
no activity-specific admission rule or scoring preference. It is useful for
exploring shared day and slot calculations, but it is not a classical election
for an unspecified act. Once the user's purpose is known, the corresponding
purpose-specific activity profile takes precedence.

## Adding an activity

1. Give the activity exactly one of the three claim fields.
2. Add the corresponding ledger entry with scope, implementation and review
   metadata.
3. For `source_claim`, record an inspected edition and exact locator.
4. Export the browser rules and test both browser and MCP disclosure.
5. Run `python tools/check_activity_provenance.py` and the full project
   verifier before review.
