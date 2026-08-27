# Documentation standard

This repository is the **canonical source** for Telugu Calendar Utilities
documentation. A future documentation website is a generated projection of
selected committed files; it must never become a second place where source
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

GitHub's Markdown rendering remains the zero-build fallback. The proposed
projection decision is recorded in
[ADR 0001](decisions/0001-documentation-projection.md): evaluate a local
Starlight projection first, while keeping the source renderer-neutral.

If a public site is approved, it should use a separate deployment target and a
dedicated documentation hostname such as `docs.panchangam.astrochaganti.com`.
It must not write into the existing `gh-pages` branch. That branch is a layered
product-data publication surface shared by multiple frozen workflows and owns
the `panchangam.astrochaganti.com` CNAME.

Publication is a later, explicit decision. The sequence is:

1. build the selected content locally from committed source;
2. verify links, search, Mermaid, accessibility, and representative mobile and
   desktop pages;
3. review screenshots and the dependency/build footprint;
4. obtain owner approval for hosting and DNS changes;
5. add an isolated preview and publication path without modifying the frozen
   product deployment workflows.
