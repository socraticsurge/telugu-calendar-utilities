# ADR 0001: Repository-first documentation with a separate projection

- **Status:** Proposed for owner review
- **Date:** 2026-08-27
- **Decision owner:** repository owner
- **Related work:** [epic #164](https://github.com/socraticsurge/telugu-calendar-utilities/issues/164),
  [story #171](https://github.com/socraticsurge/telugu-calendar-utilities/issues/171)

## Context

The repository already contains extensive architecture, computation,
provenance, activity-profile, operational, plan, and tracking material. The
reference documents are committed to Git, but their index incorrectly called
them local and gitignored. There is no declared authoring/publication contract
and no browsable documentation build.

The existing GitHub Pages branch cannot safely absorb an unrelated docs
generator. Multiple workflows layer the landing site and generated calendar
data into that branch, preserve each other's files, and maintain the production
`panchangam.astrochaganti.com` CNAME. Those workflows are frozen unless the
owner explicitly approves a change.

## Decision drivers

- source must be reviewable in the same pull request as code;
- existing Markdown and Mermaid should remain useful on GitHub;
- local full-text search and clear navigation should work without an external
  indexing service;
- the renderer must not force framework syntax into canonical pages;
- generated output must be reproducible and disposable;
- publication must be isolated from product data and frozen workflows;
- the maintenance burden should fit a small project in maintenance mode.

## Options considered

| Option | Strengths | Costs and risks | Disposition |
|---|---|---|---|
| GitHub-native Markdown | No added dependencies or hosting; Mermaid renders on GitHub | Weak cross-page navigation and discovery; repository search is not a documentation search experience | Keep as permanent fallback |
| [Astro Starlight](https://starlight.astro.build/) | Documentation-focused navigation, accessibility defaults, and built-in local [Pagefind search](https://starlight.astro.build/guides/site-search/); Astro content loaders can read committed Markdown | Adds an Astro build layer; Mermaid requires a maintained integration; the project remains on a pre-1.0 release line | Recommended local pilot |
| [VitePress](https://vitepress.dev/guide/what-is-vitepress) | Small Markdown/Vite model, default docs theme, and local search; aligns with the repository's existing Vite knowledge | Mermaid needs integration; the next major line is still published as an alpha, so choosing the stable line now creates an expected migration decision | Pilot fallback |
| [Docusaurus](https://docusaurus.io/) | Mature docs platform and official Mermaid support | Larger React/MDX surface than this project needs; official search guidance favours hosted Algolia while local search is community-maintained | Do not adopt now |
| [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) | Excellent established docs experience, search, and diagrams | Maintainers have announced end of life for November 2026 | Do not start a new site |
| [Zensical](https://zensical.org/about/) | Open-source successor from the Material creators with a promising migration path | Described by its own project as alpha | Monitor; reconsider after stability |
| External CMS or GitHub Wiki | Friendly browser editing | Creates a second source/repository and a drift path away from code, tests, and provenance registries | Reject as canonical source |

## Proposed decision

1. Keep all canonical documentation and computation metadata in this repository
   under the directory contract in [`docs/README.md`](../README.md).
2. Keep the canonical pages renderer-neutral and usable through GitHub alone.
3. Use Starlight for a **local, disposable projection pilot**, not as a new
   source format. It wins the first evaluation on built-in local search,
   documentation-oriented navigation, and accessibility defaults.
4. Use VitePress stable as the fallback if the Starlight pilot cannot render
   the current Markdown and Mermaid corpus without source coupling or excessive
   dependencies.
5. If a public projection is later approved, build it on a separate hosting
   project and documentation subdomain. Do not publish it to this repository's
   existing `gh-pages` branch.
6. Do not deploy, change DNS, or alter `.github/workflows/` in story #171.

## Pilot acceptance gates

The Starlight pilot is acceptable only if it can:

- load the selected root and `docs/` Markdown without copied source files;
- exclude plans, specs, tracking, and generated product data from default
  navigation and search;
- index the reference corpus locally without a hosted search dependency;
- render existing Mermaid diagrams while preserving GitHub rendering;
- preserve relative links or report each required source-link change;
- produce a deterministic build without interfering with the landing-page
  Vite build or Python package;
- pass a keyboard, contrast, mobile, broken-link, and representative-page
  review; and
- remain easy to remove without losing documentation source.

If those gates fail, keep GitHub-native documentation and evaluate the
VitePress fallback. A public site is useful, but it is not required for the
documentation to remain authoritative and maintained.

## Consequences

- Documentation can improve immediately without waiting for hosting.
- A site can add navigation and search later without creating content drift.
- The first projection adds a small, isolated JavaScript toolchain that must be
  maintained and security-reviewed.
- Existing historical material stays auditable but will not crowd the supported
  documentation experience.
- Hosting and DNS remain a separate owner-approval decision with a reviewable
  local result first.

## Revisit triggers

Revisit this proposal if Starlight reaches or changes its stable contract, if
Zensical leaves alpha with a compelling migration path, if the Mermaid
integration becomes unmaintained, or if the documentation corpus no longer
fits a static site.
