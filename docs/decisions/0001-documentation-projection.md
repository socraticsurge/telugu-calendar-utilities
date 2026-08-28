# ADR 0001: Repository-first documentation projected into the product site

- **Status:** Accepted; local implementation complete
- **Date:** 2026-08-27
- **Accepted:** 2026-08-28
- **Decision owner:** repository owner
- **Related work:** [epic #164](https://github.com/socraticsurge/telugu-calendar-utilities/issues/164),
  [story #171](https://github.com/socraticsurge/telugu-calendar-utilities/issues/171)

## Context

The repository already contains extensive architecture, computation,
provenance, activity-profile, operational, plan, and tracking material. The
reference documents are committed to Git, but their index incorrectly called
them local and gitignored. There is no declared authoring/publication contract
and no browsable documentation build.

Visitors need method and evidence links beside the values they are using. A
separate documentation hostname would create an unnecessary product boundary;
the useful destination is the existing
`https://panchangam.astrochaganti.com/docs/` site area.

The existing GitHub Pages branch cannot safely accept another independent docs
publisher. Multiple workflows layer the landing site and generated calendar
data into that branch, preserve each other's files, and maintain the production
`panchangam.astrochaganti.com` CNAME. Documentation must therefore join the
landing build atomically rather than introduce another branch writer. The
workflows are frozen unless the owner explicitly approves a change.

## Decision drivers

- source must be reviewable in the same pull request as code;
- existing Markdown and Mermaid should remain useful on GitHub;
- local full-text search and clear navigation should work without an external
  indexing service;
- the renderer must not force framework syntax into canonical pages;
- generated output must be reproducible and disposable;
- public references must use stable URLs on the same origin as the feature UI;
- the build path must remain isolated even though the result shares the product
  origin;
- no new workflow may compete with existing `gh-pages` writers;
- the maintenance burden should fit a small project in maintenance mode.

## Options considered

| Option | Strengths | Costs and risks | Disposition |
|---|---|---|---|
| GitHub-native Markdown | No added dependencies or hosting; Mermaid renders on GitHub | Weak cross-page navigation and discovery; repository search is not a documentation search experience | Keep as permanent fallback |
| [VitePress](https://vitepress.dev/guide/what-is-vitepress) | Small Markdown/Vite model, default docs theme, local search, and straightforward `/docs/` base/output configuration; aligns with the existing Vite build | Mermaid needs integration; the next major line is still published as an alpha, so the pilot must pin and assess the stable line | Recommended local pilot |
| [Astro Starlight](https://starlight.astro.build/) | Documentation-focused navigation, accessibility defaults, and built-in local [Pagefind search](https://starlight.astro.build/guides/site-search/) | Adds a second application framework to the current Vite site; external-source loading and Mermaid require more integration | Pilot fallback |
| [Docusaurus](https://docusaurus.io/) | Mature docs platform and official Mermaid support | Larger React/MDX surface than this project needs; official search guidance favours hosted Algolia while local search is community-maintained | Do not adopt now |
| [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) | Excellent established docs experience, search, and diagrams | Maintainers have announced end of life for November 2026 | Do not start a new site |
| [Zensical](https://zensical.org/about/) | Open-source successor from the Material creators with a promising migration path | Described by its own project as alpha | Monitor; reconsider after stability |
| External CMS or GitHub Wiki | Friendly browser editing | Creates a second source/repository and a drift path away from code, tests, and provenance registries | Reject as canonical source |

## Decision

1. Keep all canonical documentation and computation metadata in this repository
   under the directory contract in
   [`docs/README.md`](https://github.com/socraticsurge/telugu-calendar-utilities/blob/master/docs/README.md).
2. Keep the canonical pages renderer-neutral and usable through GitHub alone.
3. Use the stable VitePress line for a **local, disposable projection**,
   not as a new source format. The same Vite ecosystem and a `/docs/` build
   target make it the smallest fit for the clarified same-site requirement.
4. Use Starlight as the fallback if VitePress cannot meet accessibility,
   source-loading, search, or Mermaid requirements cleanly.
5. Publish an approved projection under
   `https://panchangam.astrochaganti.com/docs/` by composing `dist/docs/` into
   the landing build. Do not create a second documentation deployment workflow
   or change the production CNAME.
6. Map every public computation to a stable route such as
   `/docs/computations/<computation-id>/`. Feature screens should link to the
   method and, where safe, pass non-sensitive result context for verification.
7. Do not deploy or alter `.github/workflows/` in story #171. Updating the
   frozen landing-workflow path contract requires a later explicit owner
   approval after the local result is reviewed.

## Acceptance gates

The VitePress projection is acceptable only if it can:

- load the selected root and `docs/` Markdown without copied source files;
- exclude plans, specs, tracking, and generated product data from default
  navigation and search;
- index the reference corpus locally without a hosted search dependency;
- render existing Mermaid diagrams while preserving GitHub rendering;
- preserve relative links or report each required source-link change;
- build deterministically into `dist/docs/` after the landing Vite build without
  deleting or replacing landing or generated-data artifacts;
- keep `/docs/computations/<computation-id>/` URLs stable and validate that
  contextual product links resolve;
- pass a keyboard, contrast, mobile, broken-link, and representative-page
  review; and
- remain easy to remove without losing documentation source.

If those gates fail, keep GitHub-native documentation and evaluate the
Starlight fallback. A public site is useful, but it is not required for the
documentation to remain authoritative and maintained.

## Consequences

- Documentation can improve immediately without waiting for hosting.
- Visitors stay on the current site when they move from a result to its method,
  evidence, and verification context.
- The first projection adds a small VitePress toolchain that must be maintained
  and security-reviewed.
- Existing historical material stays auditable but will not crowd the supported
  documentation experience.
- The landing build becomes the atomic owner of `/docs/`; no DNS change or new
  `gh-pages` writer is needed.
- The frozen landing-workflow path filter must eventually include canonical
  docs inputs so docs-only changes deploy. That change needs explicit owner
  approval and regression checks for every layered artifact.

## Revisit triggers

Revisit this decision if VitePress changes its stable contract, if Starlight
becomes materially simpler to integrate with the existing Vite site, if the
Mermaid integration becomes unmaintained, or if the documentation corpus no
longer fits a static site.
