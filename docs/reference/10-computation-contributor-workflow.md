# Add or change a computation safely

> **Audience:** contributors and maintainers implementing a computation change.
> **Status:** current contribution workflow; it does not authorize frozen-core
> changes. **Owners:** `AGENTS.md`, `ARCHITECTURE.md`, the computation inventory,
> and the verification tools. **Review when:** any of those contracts, public
> surfaces, or release rules change.

This is the concrete path from a proposed formula or rule to a reviewable pull
request. It applies to astronomical facts, Panchangam classifications, textual
rules, personal calculations, scores, and generated interpretations.

Use the [copyable worksheet and JSON record](computation-record-template.md)
while implementing. The canonical machine-readable catalogue is
[`computations.json`](computations.json); its vocabulary and required fields are
defined by [`computations.schema.json`](computations.schema.json).

## 1. Stop before choosing a file

First classify the requested change. A pull request is not permission to cross
the repository's frozen boundaries.

| Change | Correct owner | May proceed without new owner approval? |
|---|---|---|
| Change a Drik, Surya Siddhanta, or Vakya formula, engine finalization, muhurta-window owner, or festival evaluation mechanism | `telugu_panchangam/engines/` | **No. Stop and obtain explicit owner approval.** |
| Append one festival row using an existing deciding moment | Existing rule table in `engines/base.py` | Yes, but only with a precise external reference and a new reference-verified test; do not change an existing assertion |
| Add a deterministic fact derived from engine output | A new focused top-level module under `telugu_panchangam/` | Yes; consume the public engine result and keep the engines unchanged |
| Add a birth-dependent or electional computation | A new or existing focused module under `telugu_panchangam/personal/` | Yes; consume engine outputs and keep personal inputs out of public URLs |
| Add another domain such as Gochara | Its focused domain package | Yes when additive; do not move unrelated core logic merely for symmetry |
| Expose an existing computation through MCP | `mcp/tools.py` plus `mcp/server.py` signature/help | Yes, with parity tests and a PyPI version bump |
| Present an existing result in the browser | `src/` adapter/panel code or generated shared data | Yes, but do not invent a second owner; screenshots and owner sign-off are required before pushing UI changes |
| Change the subscriber-facing ICS representation | `generators/ics.py` | **No. Stop and obtain explicit owner approval.** |
| Change deployment, Pages composition, CNAME, or workflow triggers | `.github/workflows/` | **No. Stop and obtain explicit owner approval.** |
| Make a new feature pass by changing an existing expected calculation | Existing test assertion | **No. Stop.** Treat this as a frozen-core or correction proposal and show the independent evidence first |

Adapters serialize, validate inputs, and choose presentation. They must not own
domain formulas. If Python already owns the computation, prefer generated
shared tables or explicit parity fixtures over manually retyping constants into
TypeScript.

## 2. Define the contract before implementation

Open or update one GitHub story and record:

- a stable computation ID that describes the meaning, not its file path;
- formula or textual rule in plain language;
- inputs, defaults, accepted ranges, units, coordinate frame, system,
  ayanamsa, timezone, and day-boundary convention;
- outputs, units, rounding, null/error behavior, and public consumers;
- edge cases, known disagreements, safety limitations, and backward-
  compatibility expectations;
- evidence class and the exact evidence needed for the intended assurance
  statement; and
- which Python, MCP, browser, generated-data, or ICS surfaces must agree.

Start one feature branch for that story. If investigation uncovers a different
defect, source conflict, or frozen-core correction, open a separate story and
PR rather than silently widening the branch.

## 3. Plan evidence at the right level

Regression tests establish reproducibility. They do not independently verify a
formula or textual rule.

| Claim type | Required evidence before calling it verified |
|---|---|
| Drik astronomical value or boundary | Same date, place, timezone, ayanamsa and convention compared with the named Drik Panchang day page; use several dates and more than one city, and record values plus tolerance |
| Surya Siddhanta or Vakya result | An edition, almanac, or independently implemented model that uses that system; a modern Drik result is not the authority for an intentional system difference |
| Textual or electional rule | Identified edition plus chapter/verse/page locator, with a criterion-by-criterion crosswalk and conflicts disclosed |
| Regional convention | Named regional or lineage scope; do not present it as universal |
| Product ranking or heuristic | Mark it `project_heuristic` / `heuristic`, explain the choice, and test deterministic behavior |
| Generated interpretation | Verify cited structured facts separately; keep prose and advice under the generated-interpretation boundary |

If the needed source cannot be inspected, use the honest state such as
`needs_locator`, `partially_verified`, `engine_pinned`, or `heuristic`. Never
upgrade the state because a test passes or because the implementation and its
own output agree.

## 4. Write tests, then add the owner

Add a focused test that fails because the new behavior is absent. Do not edit
an existing calculation assertion to make the feature fit.

The test set should cover, as applicable:

- normal and boundary inputs, invalid input, rollover, timezone and DST;
- multiple dates and cities, including a non-IST location for local-time code;
- every calculation system and ayanamsa the public signature accepts;
- exact table membership, units, rounding, interval inclusion/exclusion, and
  zero-duration or missing-event behavior;
- independent comparison cells with source URL/locator and tolerance;
- Python/MCP serialization and browser parity when the result crosses those
  surfaces; and
- backward compatibility for existing public fields, signatures, feed bytes,
  or accepted aliases.

Put the computation in the narrowest additive owner from the table above. Keep
the formula there. Adapters may call it but must not reinterpret its constants
or silently apply a different time basis.

## 5. Update the documentation contract in the same PR

1. Add or update the record in [`computations.json`](computations.json).
2. Add or update claim-level evidence in
   [`provenance.json`](provenance.json); keep source locators and assurance
   states precise.
3. Update the appropriate engine or derived-computation reference page and any
   affected MCP/browser/public-surface documentation.
4. Add every material mirror to `implementations` with role `mirror`; a
   serializer-only adapter normally remains a coverage exclusion.
5. Record limitations even when the algorithm is fully deterministic.
6. Regenerate [`project-facts.json`](project-facts.json) if a system, city, MCP
   tool, computation record, or activity catalogue changed.

Run:

```bash
python tools/check_computation_inventory.py
python tools/check_documentation_freshness.py --write  # only when facts changed
python tools/verify_project.py
```

Review the generated fact diff; do not accept it merely because it is
generated. The complete verifier is offline and must pass before commit.

## 6. Review public surfaces and release impact

Before opening the PR, reconcile every selected surface:

- **Python:** one canonical owner and a stable return contract;
- **MCP:** signature, help text, validation, JSON output, package README, tests,
  `CHANGELOG.md`, and synchronized `pyproject.toml` / `server.json` patch or
  minor version;
- **Browser:** same vocabulary, formula, timezone, system and ayanamsa;
  representative desktop/mobile screenshots and owner sign-off before push;
- **Generated data:** source, generator, committed/ignored status, and a drift
  check;
- **ICS:** no format change without explicit owner approval and byte-level
  regression evidence; and
- **GitHub Pages/workflows:** no workflow, CNAME, or layered-artifact change
  without explicit owner approval.

The PR description must name the computation IDs, evidence inspected, exact
dates/cities/systems compared, tolerances, public surfaces, compatibility
impact, commands run, and any approval still required. Keep the branch
unmerged for owner review.

## Worked example: five-limb Panchanga Shuddhi

The existing `derived.panchanga-shuddhi` record demonstrates the additive
path without rewriting an engine:

1. **Classification:** it consumes the five limbs of `PanchangamDay`, so the
   owner is the additive module `telugu_panchangam/panchanga_shuddhi.py`, not an
   engine or MCP adapter.
2. **Contract:** `assess_shuddhi` grades Tithi, Vaaram, Nakshatra, Yoga and
   Karana at sunrise, returning five assessments, a count from 0–5, and a
   summary verdict.
3. **Evidence:** it is a textual rule. The record honestly remains
   `needs_locator`; deterministic tests do not turn the table into an
   independently verified textual claim.
4. **Tests:** `tests/test_panchanga_shuddhi.py` covers the limb tables, verdict
   count, day extraction and MCP output. A source-verification PR would add an
   edition/locator and exact table crosswalk without rewriting passing behavior.
5. **Surfaces:** Python owns the result and MCP exposes it. It has no browser or
   ICS mirror, so the record does not claim those surfaces.
6. **Release:** the MCP tool required synchronized help/package documentation,
   tests, changelog entry and version bump. No engine, ICS, or workflow change
   was necessary.

That is a complete, reviewable record even though its textual evidence remains
open: method, ownership, tests, surfaces, limitation, and actual assurance state
are all explicit.
