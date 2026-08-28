# Computation inventory

The canonical inventory of production computations is
[`computations.json`](computations.json). Its structural contract is
[`computations.schema.json`](computations.schema.json), and the repository
enforces the stronger cross-file rules with
[`tools/check_computation_inventory.py`](../../tools/check_computation_inventory.py).

Repository-wide catalogue counts are derived into
[`project-facts.json`](project-facts.json). Run
`python tools/check_documentation_freshness.py --write` after intentionally
changing calculation systems, cities, MCP tools, activity catalogues, or the
computation inventory. The normal `tools/verify_project.py` command fails if
that generated snapshot or the high-level documentation has drifted.

The inventory answers these questions for each conceptual computation:

- What stable ID names it?
- Which implementation owns it, and which implementations mirror or consume it?
- What are its inputs, outputs, and time basis?
- Which public or internal surfaces expose it?
- Which provenance claims and verification states apply?
- Which tests exercise it, and what limitations remain?

Stable IDs are durable documentation anchors. They should survive file moves and
refactors when the meaning of the computation has not changed. New production
computations must add a record; retired computations must remove or explicitly
replace their record.

## Scope boundary

The inventory records domain computations, not every function. A computation is
a meaningful astronomical result, Panchangam fact or window, derived
classification, personal calculation, scoring decision, or interpretive result.
One conceptual computation can have several implementation links when, for
example, Python owns the calculation and TypeScript mirrors it in the browser.

Source files that own no domain calculation are classified explicitly under
`coverage.exclusions`. Valid exclusions include package markers, lookup data,
data models, adapters, orchestration, serialization, and UI-only code. The
validator audits the configured Python and TypeScript source roots, so a new
production file cannot remain silently unclassified.

## Assurance language

Inventory coverage does not mean that every result has been independently
verified. Each record carries its actual evidence class and verification state:

- tests show that the repository's current behavior is reproducible;
- provenance links show what source or comparison supports the claim;
- `partially_verified`, `needs_locator`, `conflicted`, and similar states expose
  incomplete evidence instead of implying blanket correctness;
- limitations state important convention, accuracy, scope, or safety boundaries.

The claim-level source register remains
[`provenance.json`](provenance.json). The computation inventory links to it; it
does not replace it.

## Validation

Run the inventory contract directly from the repository root:

```bash
.venv/bin/python tools/check_computation_inventory.py
```

The command validates IDs, vocabularies, required metadata, source symbols,
test paths, provenance claim links, implementation ownership, explicit
exclusions, and complete classification of the configured production source
roots. Its successful summary prints the current record, implementation, and
audited-file counts.

The same contract is exercised by `tests/test_computation_inventory.py`, so it
also runs as part of the normal Python test suite.

## Updating the inventory

1. Choose a stable conceptual ID; do not encode a file path into it.
2. Link the owner implementation and every material mirror or consumer.
3. Record inputs, outputs, time basis, exposed surfaces, evidence, tests, and
   limitations at the precision actually supported.
4. Add any genuinely non-computational new source file to the explicit exclusion
   list with a narrow reason.
5. Run the validator and the relevant computation tests before opening a PR.

If the inventory reveals a computation defect or evidence conflict, open a
separate correction or research story. Do not silently change a frozen engine
while updating documentation.
