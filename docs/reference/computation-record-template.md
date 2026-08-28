# Computation change worksheet and record template

> **Audience:** contributors preparing a computation story and pull request.
> **Status:** copyable current template. **Owner:**
> [`computations.schema.json`](computations.schema.json). **Review when:** the
> schema, provenance vocabulary, contributor workflow, or public surfaces
> change.

Read the [safe contributor workflow](10-computation-contributor-workflow.md)
before using this template. If the change touches an engine, the frozen ICS
serializer, a workflow, or an existing calculation assertion, stop at the
approval gate described there.

## Story worksheet

Copy this section into the GitHub story and replace every placeholder.

```markdown
## Computation contract

- Stable ID: `<layer>.<computation-name>`
- Meaning and user need: `<what the result tells a user>`
- Owning module and symbol: `<repository path>::<symbol>`
- Plain-language formula/rule: `<steps, constants, table or textual rule>`
- Inputs/defaults: `<names, ranges, units and defaults>`
- Time basis: `<timezone, day boundary, system and ayanamsa>`
- Outputs: `<fields, units, rounding and null/error behavior>`
- Edge cases: `<rollover, DST, missing event, boundary inclusion>`
- Public surfaces: `<python-library | mcp | ics | website | generated-data>`
- Mirrors/adapters: `<paths or none>`
- Backward compatibility: `<unchanged contract or migration>`

## Evidence plan

- Claim kind: `<deterministic-fact | textual-rule | regional-convention |
  project-heuristic | generated-interpretation>`
- Evidence class: `<astronomical | textual | published_panchangam |
  regional_convention | project_heuristic>`
- Intended verification state: `<verified | partially_verified |
  engine_pinned | needs_locator | heuristic | contradicted>`
- Source/edition/locator: `<exact source or explicit gap>`
- Independent comparisons: `<date, city, timezone, system, expected,
  actual, tolerance, URL/locator>`
- Known disagreements/limitations: `<do not leave blank>`

## Tests and review

- New failing test first: `<test path and case>`
- Cross-date/city/system cases: `<matrix>`
- Python/MCP/browser parity: `<tests or not applicable with reason>`
- Version/release impact: `<none | patch | minor | major and why>`
- Approval gates: `<none, or exact frozen/UI boundary requiring approval>`
- Verification command: `python tools/verify_project.py`
```

## Inventory record

Copy this object into the `computations` array in
[`computations.json`](computations.json). Replace every angle-bracket value and
use only vocabulary values already declared at the top of that registry. Add a
`test_gap` string instead of inventing a test path only when the gap is real and
visible.

```json
{
  "id": "<layer>.<computation-name>",
  "title": "<human-readable title>",
  "summary": "<one-sentence method and result>",
  "owning_layer": "derived",
  "claim_kind": "deterministic-fact",
  "implementations": [
    {
      "path": "telugu_panchangam/<module>.py",
      "symbol": "<owner_symbol>",
      "role": "owner"
    },
    {
      "path": "src/<browser-module>.ts",
      "symbol": "<mirror_symbol>",
      "role": "mirror"
    }
  ],
  "inputs": ["<input with units/defaults>"],
  "outputs": ["<output with units/rounding>"],
  "time_basis": "<timezone, day boundary, system and ayanamsa>",
  "surfaces": ["python-library", "mcp", "website"],
  "provenance": {
    "evidence_classes": ["astronomical"],
    "verification_states": ["partially_verified"],
    "claim_ids": ["<claim-id-from-provenance.json>"],
    "note": "<what the evidence verifies and what it does not>"
  },
  "tests": ["tests/test_<feature>.py"],
  "limitations": ["<scope, accuracy, convention, safety or manual boundary>"]
}
```

Delete a mirror object or surface that does not apply. Do not claim a surface
merely because an adapter could theoretically expose the result.

## Pull-request checklist

- [ ] The stable ID names a concept, not a file.
- [ ] The owner is additive, or explicit frozen-core approval is linked.
- [ ] Formula/rule, inputs, outputs, units, time basis and edge cases are clear.
- [ ] Evidence class, exact source/comparison, state and limitations are honest.
- [ ] New tests cover boundaries and the required date/city/system matrix.
- [ ] Python, MCP, browser, generated-data and ICS claims match actual surfaces.
- [ ] MCP changes include synchronized version, changelog and package docs.
- [ ] UI changes have screenshots and owner sign-off before push.
- [ ] No existing calculation assertion, frozen ICS format, CNAME or workflow
      changed without explicit owner approval.
- [ ] `python tools/verify_project.py` passes in full.
- [ ] The PR remains unmerged for owner review.
