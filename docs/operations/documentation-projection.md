---
title: Documentation projection operations
description: Build, validate, and review the same-site documentation projection without creating a second source of truth.
---

# Documentation projection operations

The repository Markdown and structured registries under `docs/` are canonical.
VitePress renders a searchable projection at `/docs/`; generated HTML and copied
JSON in `dist/docs/` are disposable build output and must not be edited or
committed.

## Build contract

Run the complete local site build from the repository root:

```bash
npm run build
```

The command builds the existing landing site first, adds the documentation under
`dist/docs/`, and then checks that every existing `public/` artifact is still
present byte-for-byte. It also verifies every stable computation route and every
structured reference copy.

For documentation-only iteration:

```bash
npm run dev:docs
npm run build:docs
npm run docs:check-output
```

`npm run build:docs` parses every included Mermaid fence before rendering. A
diagram syntax error fails the build instead of reaching publication as a broken
figure.

## Public-source boundary

The projection includes maintained computation references, provenance records,
selected decisions, contributor guidance, and operational contracts. It excludes:

- historical `plans/`, `specs/`, and `tracking/` trees;
- generated feed documentation and runtime calendar payloads;
- repository working notes such as `NOW.md`, `GUIDELINES.md`, and the
  maintainer-only reference status index;
- local UI-review screenshots;
- ignored local output.

Links from included documents to excluded repository material remain explicit
GitHub source links. The projection does not copy that material into the search
index.

## Computation routes and data

`docs/reference/computations.json` creates one stable route per computation at
`/docs/computations/<id>/`. Each page labels documentation, regression coverage,
and independent source support separately. The build also exposes exact copies
of the maintained JSON registries under `/docs/reference/` for traceability.

## Publication boundary

The documentation build deliberately adds no deploy workflow, `CNAME`, DNS
record, or second Pages writer. Publishing it requires a separately reviewed,
minimal change to the existing Pages workflow after the local screenshots and
navigation checks have owner approval. Until then, this is a local build only.
