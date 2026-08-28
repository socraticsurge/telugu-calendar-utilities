# Documentation standard

This repository is the **canonical source** for Telugu Calendar Utilities
documentation. The VitePress website under `/docs/` is a generated projection
of selected committed files; it must never become a second place where source
content is edited.

This contract applies to maintainers, contributors, automation, and any static
site renderer introduced after [issue #171](https://github.com/socraticsurge/telugu-calendar-utilities/issues/171).

## Principles

1. **Keep source beside code.** A computation change and its documentation can
   be reviewed, versioned, and released together.
2. **Separate authoring from presentation.** Markdown, JSON registries, and
   source diagrams are durable inputs. HTML, search indexes, and copied assets
   are replaceable build output.
3. **Publish deliberately.** Being in a public repository does not make a file
   part of the supported documentation navigation. Historical plans remain
   inspectable without being presented as current guidance.
4. **Prefer portable source.** Canonical prose uses GitHub-flavoured Markdown,
   relative links, and Mermaid source. Framework-specific MDX, Vue, or Astro
   components do not belong in canonical reference pages.
5. **Document evidence honestly.** Deterministic astronomy, textual rules,
   regional convention, project heuristics, and generated interpretation are
   distinct claim classes. A regression-pinned result is not automatically an
   independently verified result.

## Where documentation belongs

| Location | Purpose | Default projection |
|---|---|---|
| Root `README.md` | Product entry point and development quick start | Public |
| Root `ARCHITECTURE.md` | Current module boundaries and frozen-core posture | Public |
| Root `CONTRIBUTING.md` | Active contribution and verification entry point | Public |
| Root `MAINTENANCE_RUNBOOK.md` | Current operating and release procedures | Maintainer navigation |
| `docs/reference/` | Long-lived computation, provenance, surface, and domain references | Public |
| `docs/operations/` | Focused operational evidence and recovery procedures | Maintainer navigation |
| `docs/decisions/` | Durable architecture decisions with status and consequences | Maintainer navigation |
| `docs/screenshots/` | Review evidence and assets referenced by current documentation | Only when linked |
| `docs/specs/` | Point-in-time design proposals and approved historical specifications | Archive; excluded by default |
| `docs/plans/` | Completed or parked implementation plans | Archive; excluded by default |
| `docs/tracking/` | Retired June 2026 planning and execution record | Archive; excluded by default |
| `docs/GUIDELINES.md`, `docs/NOW.md` | Retired spec-harness entry points | Archive; excluded by default |

Ignored runtime output such as `docs/feeds/` and `docs/gochara.json` is product
data, not documentation source. The `dist/` directory, renderer output, copied
Markdown, and generated search indexes must also remain untracked.

When a new class of documentation does not fit this table, update this file in
the same pull request that introduces it. Do not create another top-level docs
tree or use the GitHub Wiki as a parallel source of truth.

## Authoring contract

Every long-lived page starts with enough context to answer:

- who the page is for;
- whether it describes current behaviour, a proposal, or a historical record;
- which code, registry, test, or operational surface it owns;
- what event requires it to be reviewed again.

Computation documentation additionally records:

- a stable computation identifier and owning module;
- inputs, defaults, units, timezone, ayanamsa, and day-boundary assumptions;
- outputs, consumers, and public surfaces;
- the formula or rule in plain language, with edge cases and limitations;
- evidence class, source locator or verification state, and known conflicts;
- representative tests and independent comparison evidence where applicable;
- whether Python, MCP, browser, generated-data, or calendar representations
  mirror the same owner.

The canonical machine-readable fields and completeness rules will be defined by
[issue #165](https://github.com/socraticsurge/telugu-calendar-utilities/issues/165).
Human-readable pages should link to those records rather than duplicate live
catalogue counts by hand.

## Markdown, links, diagrams, and assets

- Use repository-relative Markdown links. A link must work on GitHub before it
  is expected to work in a generated site.
- Use fenced Mermaid for diagrams and include an equivalent prose or table
  explanation. A diagram must not be the only carrier of required information.
- Add meaningful alternative text to images. Store maintained images in
  `docs/screenshots/` or a future purpose-named asset directory under `docs/`.
- Prefer descriptive headings over file-number knowledge. Existing numbered
  reference pages may retain their names; new navigation must display titles.
- Do not paste generated HTML, a rendered site, a search index, or dependency
  output into `docs/`.
- Avoid hard-coded inventory counts. If a count is useful, derive it from a
  registry or protect it with an automated check.

## Generated documentation

A generated page or data file must have one declared source owner and one
reproducible command. Generated files use an explicit header or adjacent README
that states:

- that the file is generated and must not be edited;
- the source files and generator command;
- whether the output is committed or ignored;
- the validation command that detects drift.

The source registry remains canonical even when a website presents a more
readable table, filter, or cross-link graph derived from it.

## Public computation-reference contract

Documentation explains a method; by itself, it does not verify the particular
value a visitor sees. Every user-facing computation should therefore map to one
stable computation identifier and one public reference route under
`https://panchangam.astrochaganti.com/docs/`.

Product links should use explicit labels such as **How this is calculated** or
**Verify this result**, not a generic “Learn more”. The first link explains the
method. The second carries the non-sensitive calculation context needed to
interpret or reproduce the displayed value, such as:

- date, city or coordinates, and IANA timezone;
- calculation system, ayanamsa, and sunrise/day-boundary convention;
- the displayed result and its units;
- application and computation-registry versions; and
- the stable computation identifier.

Do not put birth details, names, free-form activity text, or other personal
inputs into a verification URL. Personalised features may link to the method
page and show their input summary locally instead.

Each public computation page must distinguish:

1. **Meaning** — what the value tells the user.
2. **Method** — formula or textual rule, inputs, intermediates, units, and time
   basis.
3. **Evidence** — evidence class, exact source or comparison status, and known
   disagreements.
4. **Verification** — representative multi-date/multi-city tests, reproducible
   command or machine-readable record, and the current result context when
   supplied.
5. **Limitations** — regional, lineage, approximation, manual-check, safety, or
   generated-interpretation boundaries.
6. **Implementation** — owning module, public consumers, tests, and release or
   commit version.

The page must not describe an `ENGINE_PINNED` regression value as independently
verified. It should show exactly which cells or claims have independent source
comparisons and which are protected only against software regression.

Public labels use three explicit assurance levels:

- **Documented and traceable** — the owner, method, inputs, outputs, and evidence
  state are disclosed.
- **Regression or reproduction checked** — tests or a repeatable command protect
  the behaviour, but the check may still use the same implementation or pinned
  output.
- **Independently source-compared** — the specifically named claim or result cell
  has been compared with an independent source and carries its locator.

A page may contain claims at different levels. Re-fetching the same published
result is reproduction, not independent verification, and must be labelled that
way.

## Review and freshness

- Behaviour changes update their computation record and affected prose in the
  same focused pull request.
- Documentation-only corrections still run `python tools/verify_project.py`.
- Changes to `telugu_panchangam/engines/`, the ICS contract, or deployment
  workflows retain the approval boundaries in `AGENTS.md`.
- Public UI or documentation-site changes require a local preview, screenshots,
  and owner sign-off before publishing.
- Historical files are not silently rewritten to look current. Add a status
  note or promote the still-valid guidance into a maintained page.
- Documentation freshness and inventory coverage gates belong in the canonical
  verifier; [issue #169](https://github.com/socraticsurge/telugu-calendar-utilities/issues/169)
  owns that enforcement work.

## Projection and hosting

GitHub's Markdown rendering remains the zero-build fallback. The implemented
projection decision is recorded in
[ADR 0001](decisions/0001-documentation-projection.md): use a local VitePress
projection while keeping the source renderer-neutral.

When publication is approved, the generated documentation belongs on the
existing site at `https://panchangam.astrochaganti.com/docs/`. It is built into
`dist/docs/` as an atomic part of the landing-site build and published by the
existing landing deployment. Do not add another independent `gh-pages` writer:
that branch is already a layered product-data surface shared by several frozen
workflows.

The landing workflow will eventually need to notice canonical documentation
source changes. That is a frozen-workflow change and therefore remains an
explicit owner-approval gate. The approved design must preserve the current
CNAME, generated feeds, Gochara, Lagna, and Rasi Phalalu artifacts.

Publication is a later, explicit decision. The sequence is:

1. build the selected content locally from committed source;
2. verify links, search, Mermaid, accessibility, and representative mobile and
   desktop pages;
3. verify stable computation routes and representative contextual links from
   the existing feature screens;
4. review screenshots and the dependency/build footprint;
5. obtain owner approval for the public UI and frozen-workflow changes; and
6. publish the combined landing-and-documentation artifact without changing the
   production hostname or losing layered product data.
