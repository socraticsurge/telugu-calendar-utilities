# Telugu Calendar Utilities — Improvement Plan

_Created 2026-06-16. Last updated 2026-06-16 — **Phases 1 / 2 / 6 / 7 + housekeeping fully shipped** (14 PRs total). **Phases 3 / 4 / 5 / 8 PAUSED 2026-06-16** — the application is in good shape; remaining work is quality-of-life polish. See "Pause notes" section below for the precise state and resume path. Living tracker — gitignored under `docs/tracking/`. **This file is the source of truth for the plan.**_

---

## Pause notes (2026-06-16)

The project is in genuinely good shape after Phases 1 / 2 / 6 / 7. Nothing is broken. Nothing blocks devotee use. Remaining work is quality-of-life polish.

**Today's state — confirmed working:**
- 846 tests passing, 1 skipped on master
- DP-verified festival regression covers 2027–2028 (Phase 6 PR #89)
- All festival rules table-driven (Phase 6 PR #90)
- MCP server at 1.8.0 on PyPI, all 11 tools accessible
- Release pipeline gated by version-sync + CHANGELOG + pytest
- Branch protection with 6 required CI contexts; CodeQL + pip-audit weekly
- SEO surface in place; ICS golden snapshot guarding subscriber feed format
- Per-anga ICS variant generators built (not yet deployed — deliberate follow-up)

**What's paused:**
- **Phase 3** — Vite + TypeScript migration. Full plan at [docs/plans/phase-3-vite-typescript-migration.md](../plans/phase-3-vite-typescript-migration.md). PR 2a WIP preserved on local branch `chore/p3-pr2a-vite-vitest-typescript-scaffold`. Resume by checking out that branch + continuing with PR 2b (codegen scripts).
- **Phase 4** — UI/UX harvest (a11y, wayfinding, mobile hero, popovers, subscribe wizard). Designed to ride on top of Vite; doable pre-Vite at higher per-PR cost. Cherry-pickable individually.
- **Phase 5** — PWA / offline access. Depends on Vite.
- **Phase 8** — Additive features (festivals page, embed widget, visual timeline, etc.).

**Resume options when you come back:**
1. Continue Phase 3 → 4 → 5 → 8 as planned (Vite first, then unlock everything else cheaply)
2. Cherry-pick high-value Phase 4 items directly against `docs/index.html` (no Vite). Good candidates: sub-AA contrast fix, 1-click "Add to Google Calendar" button, `<main>` + skip-to-content link, "times shown in city time" affordance — each ~half-day.
3. Ship Phase 4-style improvements via Jules bot's automated PRs (the bot still has access to the repo per the "decide later" call).

Either resume path stays consistent with the durable state in this doc and the plan docs under `docs/plans/`.

---

---

## State protocol

> Persist plans, decisions, and progress in this file as we work. The chat transcript is not durable; this doc is. Update this doc *in the same turn* whenever we change plans, lock decisions, or ship items. When checking project status, read this doc first.

---

## Decisions (resolved 2026-06-16)

| Decision | Choice | Implication |
|---|---|---|
| Vite + TypeScript pipeline | **Adopt** | Gating structural step for UI work. Phase 3. |
| Hosting | **Stay on GitHub Pages** | REST API per-request muhurta is killed. Static + build step is enough. |
| `jules-dev` branch | **Retire** | Delete `jules-dev`; sweep 14 closed-not-merged `jules-*` branches; turn on `delete-branch-on-merge`. |
| Jules bot itself | **Decide later** | Left running for now. Revisit if it produces noise after `jules-dev` is gone. |
| PWA / offline support | **Yes** | Promoted to P1. Phase 5, blocks on Vite. |
| Ayanamsa selector in UI | **Not now** | Engine-level parameter still built (Cluster A); UI surface parked indefinitely. |
| Forward-year verification scope | **4 years (2027–2030)** | Cluster A item bumps M → L. One-time investment. |

## Killed / parked

**Killed:**
- REST API for per-request muhurta (was Cluster I, P3) — staying on GitHub Pages.

**Parked indefinitely** (each entry names its reactivation trigger):

| Item | Why parked | Reactivation trigger |
|---|---|---|
| Ayanamsa selector in public UI | Engine-level parameter not yet built; UI adds explainer burden | A devotee asks for Raman / Krishnamurti / true Chitrapaksha visibly OR the engine-level ayanamsa parameter ships |
| **`EngineCore` refactor** (Phase 6 PRs 2, 4–8 of original plan) | Architectural cleanup with no devotee-visible value; engines work and are DP-verified | A new engine variant is requested OR a real bug traces to the duplication. Full design preserved at [docs/plans/phase-6-engine-unification.md §A](../plans/phase-6-engine-unification.md) |
| **`facts_at` signature enrichment** (named deciding moments union) | Internal convenience for a refactor that's parked | EngineCore refactor reactivates |
| **`SankrantiPolicy` strategy** + SS/Vakya `is_sankranti` convergence | Three sankranti conventions are an internal inconsistency, not a user bug; no DP authority for SS/Vakya | A devotee reports SS or Vakya feed `is_sankranti` flag wrong |
| **Eclipse precision audit** (decade scope vs USNO/NASA) | Multi-week project; zero devotee complaints; today's SS/Vakya use Swiss-derived eclipse times silently | A devotee reports an eclipse-timing discrepancy OR we decide to compute SS/Vakya eclipses natively |
| **Public Python library API** (`from telugu_panchangam import day_for(...)`) | Surfaces existing MCP-internal API; debatable value vs MCP layer | A Python user requests it OR a notebook/script use case appears |

---

## Setup reality check

| Layer | Verdict | Notes |
|------|---------|-------|
| GitHub Pages + `panchangam.astrochaganti.com` CNAME | **Keep** | Static + free + fast. CNAME is load-bearing for subscribers and SEO. |
| `peaceiris/actions-gh-pages@v4` deploy | **Keep, pin SHA** | Floating tag = supply-chain risk. |
| Monthly cron for ICS feeds (`generate.yml`, `gochara.yml`, `lagna.yml`) | **Keep** | Right cadence for monthly-stable content. Add concurrency groups. |
| `scripts/build_landing_page.py` 18-line copier | **Replace** | Becomes a Vite/esbuild build step in the deploy workflow. |
| Hand-edited 4321-line `docs/index.html` | **Replace** | Modular `src/` → built into `dist/`. The actual UI-velocity bottleneck. |
| Inline JS mirror of Python `ACTIVITY_RULES` + scoring weights | **Replace** | Generated TS types or JSON fixture; never re-typed by hand. |
| Static `.ics` feeds in `public/feeds/` | **Keep** | |
| PyPI `mcp-server-panchangam` distribution | **Keep** | Trusted publishing via OIDC is correct. |
| Three engines (Drik / SS / Vakya) | **Refactor** | Asymmetric inheritance; unify around an `EngineCore`. |
| `requirements.txt` + `pyproject.toml` duplicating runtime deps | **Consolidate** | `pip install -e .[test]`. |
| Python 3.11-only CI | **Matrix 3.10–3.13** | `pyproject.toml` declares `>=3.10`. |
| `pytest` + `node --test` for JS scorer | **Keep** | After Vite, JS scorer is a TS module with shared interfaces. |
| MCP server runs locally | **Keep** | Narrow attack surface per `SECURITY.md`. |

---

## How to read this doc

- **Effort:** XS (<1h) · S (~half day) · M (1–2 days) · L (3–7 days) · XL (>1 week)
- **Priority:** P0 (urgent — real damage if missed) · P1 (high leverage, do soon) · P2 (medium ROI) · P3 (speculative / nice-to-have)
- **Tags in `[]`:** `[P_, Effort, Area]` where Area is one of:
  - **E** Engine & computation
  - **G** Library, generators & API
  - **U** UI/UX behavior
  - **I** Infrastructure (build, loading, SEO)
  - **T** Tests & verification
  - **R** Release & distribution
  - **C** CI/CD & repo hygiene
  - **D** Project docs
  - **F** Additive features
- **Two ways to navigate:** the Phased sequencing section below is the **action order** (what to do next). The Clusters section is **by area** (full detail per item, file refs, first steps).

---

## Phased sequencing

Eight phases plus a Tier 3 backlog. Each item is a checkbox. **When you ship an item, mark it `[x]` here _and_ in its cluster, with PR/SHA.**

### Phase 1 — Week 1: First Six (P0 must-dos) — **SHIPPED 2026-06-16**

The locked floor. All six landed; 3 PRs + 1 set of repo ops.

- [x] **[P0, XS, R]** Bump `server.json` to 1.8.0 + `tests/test_version_sync.py` (3 asserts) — **PR #74** (`chore/release-safety-version-sync-pytest-gate`)
- [x] **[P0, S, R]** Gate `publish.yml` on `pytest tests/` before `python -m build` — **PR #74** (bundled with version sync)
- [x] **[P0, XS, R]** Add `get_panchangam_range`, `get_daily_horas`, `get_lagna_transitions` to `README_PYPI.md` — **PR #75** (`docs/pypi-1.8-tools-and-coc-email`). Note: also caught `get_panchangam_range` missing, fixed in same PR.
- [x] **[P0, XS, D]** Fill in `cvk.atreya@gmail.com` enforcement email in `CODE_OF_CONDUCT.md` — **PR #75** (bundled with PyPI catch-up)
- [x] **[P0, XS, T]** CNAME-pin guard — `test_deploy_workflow_pins_cname` parametrised over the 4 deploy workflows — **PR #76** (`test/cname-pin-guard`). Suite: 516 passed, 1 skipped.
- [x] **[P0, XS, C]** Branch sweep — `delete-branch-on-merge` enabled; 14 branches deleted (2 merged-and-unpruned + `jules-dev` + 11 closed-not-merged `jules-*`). Remote count 52 → 29. Audit estimates (19+14) were slightly stale; deleted everything that actually qualified. Remaining 29 branches are non-jules abandoned `code-health/*` / `fix-unused-*` PRs — out of Phase 1 scope, can be addressed in a later hygiene pass.

**Merged 2026-06-16:** [#74](https://github.com/socraticsurge/telugu-calendar-utilities/pull/74) → `de53474` · [#75](https://github.com/socraticsurge/telugu-calendar-utilities/pull/75) → `6b3dd43` · [#76](https://github.com/socraticsurge/telugu-calendar-utilities/pull/76) → `0ec8802`. Branches auto-deleted. Post-merge: 519 passed, 1 skipped; 26 remote branches.

### Phase 2 — Weeks 2–3: Banked stabilizers — **mostly SHIPPED 2026-06-16**

7 PRs merged, 1 awaiting user review (#86 SEO), branch protection live.

**CI/security:**
- [x] **[P1, XS, C]** Dependabot config — **PR #77** (`64670eb`)
- [x] **[P1, XS, C]** Concurrency groups on every workflow — **PR #77**
- [x] **[P1, XS, C]** Python matrix 3.10–3.13 in `ci.yml` — **PR #77**
- [x] **[P1, XS, C]** Branch protection on master — live 2026-06-16. 6 required contexts: `test (3.10/11/12/13)`, `CodeQL (Python)`, `pip-audit (requirements.txt)`. `enforce_admins=false`, `strict=false`.
- [x] **[P2, XS, C]** `ci.yml` nullglob fix — **PR #77**
- [x] **[P1, XS, R]** Sync `server.json` version in `publish.yml` — **PR #81** (`db11787`)
- [x] **[P1, XS, R]** CHANGELOG/Unreleased gate in `publish.yml` — **PR #81**
- [x] **[P1, S, C]** Pin third-party Actions to commit SHAs (23 substitutions across 7 workflows) — **PR #84** (`fab77dc`)
- [x] **[P1, S, C]** CodeQL + pip-audit security workflow — **PR #82** (`ff3fa32`). Baseline: 0 known CVEs.
- [x] **[P1, S, R]** Auto-create GitHub Release with CHANGELOG section on tag push — **PR #81**

**Quality / reproducibility:**
- [x] **[P2, S, C]** Reconcile `requirements.txt` and `pyproject.toml` (`-e .[test]` shim) — **PR #83** (`0b0bcf1`)
- [x] **[P2, S, C]** Lockfile via `uv pip compile` — **PR #88** (`5fe6333`). 732-line `requirements.lock`, hashes, Py 3.11. Passive record; CI not yet using it.
- [x] **[P2, S, C]** `.editorconfig` + minimal pre-commit — **PR #83**

**SEO head tags:**
- [x] **[P1, XS, I]** JSON-LD structured data (`WebSite` + `SoftwareApplication`) — **PR #86** (`2714dfb`)
- [x] **[P1, XS, I]** `<link rel="canonical">` + `og:image:width/height` — **PR #86**
- [x] **[P1, XS, I]** `sitemap.xml` + `robots.txt` — **PR #86**
- [x] **[P2, XS, I]** OG / Twitter share preview polish — **PR #86**

**Docs:**
- [x] **[P1, M, D]** `ARCHITECTURE.md` — **PR #85** (`173ca36`)
- [x] **[P1, M, D]** `MAINTENANCE_RUNBOOK.md` — **PR #85**

**Merged 2026-06-16:** [#77](https://github.com/socraticsurge/telugu-calendar-utilities/pull/77) · [#78](https://github.com/socraticsurge/telugu-calendar-utilities/pull/78) (Dependabot: `setup-node v4→v6`) · [#79](https://github.com/socraticsurge/telugu-calendar-utilities/pull/79) (Dependabot: `checkout v5→v6`) · [#81](https://github.com/socraticsurge/telugu-calendar-utilities/pull/81) · [#82](https://github.com/socraticsurge/telugu-calendar-utilities/pull/82) · [#83](https://github.com/socraticsurge/telugu-calendar-utilities/pull/83) · [#84](https://github.com/socraticsurge/telugu-calendar-utilities/pull/84) · [#85](https://github.com/socraticsurge/telugu-calendar-utilities/pull/85) · [#86](https://github.com/socraticsurge/telugu-calendar-utilities/pull/86) · [#87](https://github.com/socraticsurge/telugu-calendar-utilities/pull/87) (Node runtime 20→24, Active LTS) · [#88](https://github.com/socraticsurge/telugu-calendar-utilities/pull/88) (lockfile). Post-merge suite: **525 passed**, 1 skipped.

**Phase 2 fully closed.** Branch protection live on master with 6 required contexts: `test (3.10/11/12/13)`, `CodeQL (Python)`, `pip-audit (requirements.txt)`. `delete-branch-on-merge` on. Dependabot working (weekly pip + github-actions).

### Phase 6 — Week 4: Engine cleanup (NARROWED scope) — **SHIPPED 2026-06-16**

**📋 Migration plan: [`docs/plans/phase-6-engine-unification.md`](../plans/phase-6-engine-unification.md)** — drafted 2026-06-16 via Ultracode planning workflow (416 lines). All 5 open decisions resolved; scope deliberately narrowed.

**Narrowed scope (~1 week of work) — full architectural refactor parked.** The owner reviewed the workflow's 8-PR plan and concluded that 6 of the 8 PRs were architecture-only with no devotee-visible value. The full `EngineCore` refactor is preserved as parked work in the plan doc (Appendix §A) and revisits only when a real driver appears (new ayanamsa request, reported SS/Vakya bug, etc.).

**Active scope — 2 PRs:**

- [x] **[P1, L, T]** **PR 1: Forward-year DP-verified festival pin** — [#89](https://github.com/socraticsurge/telugu-calendar-utilities/pull/89) merged at `90be3e2` (2026-06-16). 30 cells × 10 assertions = 300 new tests. Vinayaka Hyderabad 2027 fully DP-verified; 4 high-risk cells owner-spot-checked; 25 cells engine-pinned with DP day-page URLs for future upgrade. Suite: 525 → 825 passed.
- [x] **[P1, S, E]** **PR 2: Table-driven festival rules** — [#90](https://github.com/socraticsurge/telugu-calendar-utilities/pull/90) merged at `8d6f24d` (2026-06-16). Lifted 4 inline-cased rules (Karthika Somavaram, Varalakshmi Vratam, Sankashti Chaturthi, **Masa Shivaratri**) into named tables. Byte-identical behaviour across 63 DP-verification cells (33 existing + 30 forward-year). Suite stays at 825 passed.

**Investigation only (no PR):**

- Three-sankranti-convention finding — Drik symmetric ±24h vs SS/Vakya asymmetric sunrise-to-sunset vs `_is_makara_day` after-sunset. Documented in `ARCHITECTURE.md` (small edit). No code unification — owner declined per Decision 2.
- Eclipses-via-Swiss in SS/Vakya documented as a known inconsistency in `ARCHITECTURE.md`. No fix scoped — owner declined per Decision 4.

**Ayanamsa note (decided 2026-06-16):** Drik uses Lahiri (`swe.SIDM_LAHIRI` at `engines/utils.py:32`) — Indian Astronomical Ephemeris standard, same default Drik Panchang uses. Not changing.

**Parked from original Phase 6 plan** (revisit when there's a real driver): `EngineCore` class refactor, `facts_at` signature enrichment, `SankrantiPolicy` strategy, caller migrations to factory functions, deletion of duplicated engine method bodies, `CLAUDE.md` frozen-core text revision.

### Phase 7 — Engine quality + library polish (NARROWED scope) — **SHIPPED 2026-06-16**

All 5 PRs merged. Suite: 825 → 846 (+21 new tests). Zero behaviour regressions.

- [x] **PR 1** **[P1, S, G]** Fix `find_muhurta` MCP signature drift — [#91](https://github.com/socraticsurge/telugu-calendar-utilities/pull/91) merged at `8cae163`. Now exposes `janma_rasis`, `janma_lagnas`, `chandra_mode` to MCP clients (were unreachable).
- [x] **PR 2** **[P2, S, T]** MCP tool tests for `tool_get_daily_horas` + `tool_get_lagna_transitions` — [#92](https://github.com/socraticsurge/telugu-calendar-utilities/pull/92) merged at `49cf0bc`. +9 tests covering planetary-hour rule across full weekday sweep + lagna cyclic order.
- [x] **PR 3** **[P2, S, T]** ICS golden-snapshot test — [#93](https://github.com/socraticsurge/telugu-calendar-utilities/pull/93) merged at `f2a93f3`. 5,131-byte fixture pins byte-stable subscriber feed format for Hyderabad/drik 2026-06-11..13.
- [x] **PR 4** **[P2, M, G]** Per-anga ICS variant feeds — [#94](https://github.com/socraticsurge/telugu-calendar-utilities/pull/94) merged at `8f5b5aa`. New `generators/anga_variants.py` with Ekadashi-only / Festivals-only / Moon-Cycles generators. `ICSGenerator.generate` extended with `variant_label` kwarg, default empty → existing dense feeds byte-identical.
- [x] **PR 5** **[P2, XS, cleanup]** Dead code cleanup — [#95](https://github.com/socraticsurge/telugu-calendar-utilities/pull/95) merged at `26150b9`. Removed 3 unused Vakya imports + 1 dead `timedelta` rebind. Verified byte-identical via 846 tests pass unchanged.

**Backlog (per top-of-doc backlog table):**
- Eclipse precision audit (decade scope vs USNO/NASA) — no devotee complaints
- Public Python library API — defer until a Python user actually asks

### Phase 3 — Vite + TypeScript migration (L)  ← **NEXT (plan refreshed 2026-06-18 against master @ 1.10.4)**

**📋 Migration plan: [`docs/plans/phase-3-vite-typescript-migration.md`](../plans/phase-3-vite-typescript-migration.md)** — drafted 2026-06-16; **refreshed 2026-06-18** with a dated addendum that corrects ~204 commits of drift (file:line anchors, Node-24/SHA-pinned deploy diffs) and enlarges the TS-scorer-port scope to mirror the 1.9.0 round. Strategy is LOCKED and unchanged; only staleness and scope were corrected.

**Headline shape:** still 5 required PRs + 3 optional. Phase 3 closes after PR 5 (deploy cutover). PRs 6–8 are component-refactor backlog that doesn't gate PWA (Phase 5).

**Why the refresh:** since the plan was drafted the project shipped 1.9.0 → 1.10.4. The 1.9.0 round (`218d981`) grew `ACTIVITY_RULES` from 24→30 activities (7→17 per-row keys) and added a whole tier of day-skips + slot signals to `muhurta.py` — **without updating the website mirror**. The TS scorer port (PR 2) is therefore ~2–3× bigger than first estimated and must be mirrored from `telugu_panchangam/personal/muhurta.py` (+ ~544 lines of helpers), NOT from the pre-1.9.0 `docs/muhurta-scorer.js` sidecar (which is deleted, not ported). The parity fixture expands to cover Mrityu −3, Panchaka, Anandadi, Nakshatra Mukha, Bhadra Puchha, Simha-Stha, dual-lagna (Lagna Shuddhi) and day-skip/dropped-day cases.

**Engines-before-Vite gate:** Phase 9 transit work (1.10.0–1.10.3) is shipped and independent — does NOT block. Master's scorer surface is quiescent (all Group-A `feat/*` branches `behind=204`, already merged via 1.9.0). The real precondition is now *"website scorer caught up to Python (or gap frozen) + codegen parity bridge in place"* — the bridge does not exist yet and is the FIRST step of PR 2.

**Open decision for owner (BIGGEST):** whether the website muhurta-scorer is brought to full parity with current master's scorer (1.10.4) AS PART of the migration (recommended — the codegen path makes it nearly free and eliminates the drift permanently) or ported as-is and left lagging until a later Phase-8 pass. (NB: the scorer *feature surface* originated in the 1.9.0 round; nothing since 1.10.0 changed it — Phase-9 transit tools + ayanamsa are independent. Target = current master, not a stale version.) See plan §Refresh / New open decisions.

**Parity strategy (unchanged, locked):** codegen not re-typing — `tools/export_activity_rules.py` → `src/data/activity-rules.generated.json`, consumed by both Python tests and the TS scorer; CI fails on stale fixture.

**Deploy strategy (unchanged, locked):** `keep_files:false` on the landing deploy + feeds rsync-back into `dist/`; `keep_files:true` on the three monthly-cron workflows; CNAME pin survives all four. **Correction:** new Set-up-Node step must pin `actions/setup-node@…#v6.4.0` / Node 24 (matching ci.yml), NOT `@v4`/Node 20.

One sustained workstream. The structural step that unblocks Phases 4, 5, 8.

- [ ] **[P1, L, I]** **Adopt Vite + TS** (5 PRs). See refreshed plan + addendum.
- [ ] **[P1, S, I]** Self-host fonts (or preload with `crossorigin`) as part of the build setup
- [ ] **[P1, S, T]** **Python ↔ JS parity test** for `ACTIVITY_RULES` (30 activities, 17 keys) + the 1.9.0 scoring signals — locked down by the codegen bridge so the architecture stays correct

_(Test baseline note: master now collects 1032 tests, not 846; current version 1.10.4.)_

### Phase 4 — Weeks 15–16: UI/UX harvest (post-Vite)

Now that source is modular, knock these down in 3–4 batched PRs by theme.

**A11y:**
- [ ] **[P1, S, U]** Sub-AA text contrast site-wide (darken `--label-muted`)
- [ ] **[P1, XS, U]** `<main>` landmark + skip-to-content link on desktop tree
- [ ] **[P1, S, U]** Mobile drawer & help-sheet as real dialogs (`role="dialog"`, focus trap, Esc)
- [ ] **[P2, S, U]** `<details>`/`<summary>` for the collapsible Muhurtam section

**Wayfinding:**
- [ ] **[P1, S, U]** City auto-detect (geolocation prompt + IP fallback) + searchable selector
- [ ] **[P1, S, U]** "Times shown in <city> local time" affordance under selector
- [ ] **[P1, XS, U]** 1-click "Add to Google Calendar" button (`calendar.google.com/calendar/r?cid=…`)
- [ ] **[P2, S, U]** Subscribe wizard with per-platform 1-click flows
- [ ] **[P2, XS, U]** Cross-link MCP card to `modelcontextprotocol.io` ecosystem

**Comprehension:**
- [ ] **[P1, S, U]** Per-anga "what is this" inline popovers (Tithi / Nakshatra / Yoga / Karana)
- [ ] **[P1, M, U]** Hero focal point on mobile — collapse brand, anga grid above the fold

**Resilience:**
- [ ] **[P2, S, U]** Skeleton / empty / error states for feed fetches
- [ ] **[P2, S, T]** Browser smoke: muhurta tier rendered assertion (Excellent/Good/Fair/Avoid)
- [ ] **[P1, S, T]** Deploy-drift guard for runtime JSON sidecars (lagna + gochara)

### Phase 5 — Week 17: PWA (M)

- [ ] **[P1, M, F]** **PWA installability**: web manifest · service worker · install prompt · offline cache for `feeds/*.ics` (yesterday's panchangam available in patchy network / temple-visit context)

### (Phase 6 + Phase 7 moved up — see top of "Phased sequencing" above)

### Phase 8 — Weeks 18+: Additive features (Vite + EngineCore both available)

**Devotee education:**
- [ ] **[P2, M, F]** Festival explainer module — structured "why this date" for each festival
- [ ] **[P2, M, F]** Linkable `festivals.html` page (one section per festival with deciding-moment prose)
- [ ] **[P2, M, D]** On-site Troubleshooting page — "why does my city show a different time than Drik Panchang"
- [ ] **[P2, S, D]** What's-new page on the site mirrored from `CHANGELOG.md`
- [ ] **[P2, S, U]** Onboarding tooltip on first visit (3-tab explainer)

**Sharing & embedding:**
- [ ] **[P2, M, F]** Embeddable widget (`src/embed/`) for blogs / temple sites — `?city=…&system=…` query params
- [ ] **[P2, M, U]** Save image of today / Print this day affordances
- [ ] **[P2, S, U]** Print stylesheet for paper output

**Bigger UI surfaces (cheap now that source is modular + engines are unified):**
- [ ] **[P2, M, U]** Visual sun/moon timeline (00:00 → 24:00 with sunrise/sunset/Rahu/Abhijit blocks)
- [ ] **[P2, M, U]** Month grid view for the 30-day Special-days preview
- [ ] **[P2, M, U]** Compare engines side-by-side for one date (Drik vs SS vs Vakya)
- [ ] **[P2, S, F]** Weekly digest ICS feed (one all-day event per week)

**1.9.0 computations on the website — muhurta scorer parity:**
- [ ] **[P2, S, U]** Group A — JS-only: Disha Shoola, Anandadi Yoga, Nakshatra Mukha, Panchaka Nakshatra, Panchaka Rahita (lagna.json already available), Pitru Paksha (parseable from ICS). Zero new feeds; changes only `muhurta-scorer.js` and activity rules in `index.html`.
- [ ] **[P2, M, U]** Group B — New planetary feed: Simha-Stha Guru/Shukra + Guru/Shukra Maudhya + Sankramana avoidance + Khar Maasa. Requires a new `{city}-timing-flags.json` generated by Python build script and added to `lagna.yml` cron.
- [ ] **[P3, L, U]** Group C — Ghati-clock features: Vishaghati windows + Bhadra Mukha/Puchha. Needs within-day ghati arithmetic; substantial new data + JS infrastructure.

**Maintenance polish:**
- [ ] **[P2, M, R]** Backfill `CHANGELOG.md` for v1.0.5..v1.7.1 from `git log`
- [ ] **[P2, M, R]** MCP-registry mcp-publisher workflow on tag push (JSON-Schema-validate + re-sync registry)

### Phase 9 — Transit Computations + Panchanga Shuddhi (new, 2026-06-17)

Five standalone PRs. Each adds a new module that consumes engine outputs; none touch the frozen core. MCP bump per PR group.

- [ ] **PR 1 [P1, M, E+G]** All-planet Maudhya calendar — new `maudhya_calendar.py`; range-query returning combustion entry/exit for Mars, Mercury, Jupiter, Venus, Saturn with direction-differentiated thresholds (Mercury 14°/12°, Venus 10°/8°, Mars 17°, Jupiter 11°, Saturn 15°). New MCP tool `tool_get_combustion_calendar`. DP-verified. **Version 1.10.0.**
- [ ] **PR 2 [P1, M, E+G]** Graha Yuddha — new `graha_yuddha.py`; detects planetary war (proximity < 1° ecliptic longitude) for the five true planets (not Rahu/Ketu); returns start/end timestamps + winner (northern latitude). New MCP tool `tool_get_graha_yuddha`. DP-verified. **Version 1.10.1.**
- [ ] **PR 3 [P2, S, E+G]** Planet ingress calendar — new `ingress.py`; finds rashi sign-change moments for any planet (Guru and Shani most significant); flags retrograde re-entries. New MCP tool `tool_get_planet_ingresses`. DP-verified. **Version 1.10.2.**
- [ ] **PR 4 [P2, XS, G]** Eclipse calendar MCP tool — `list_eclipses_in_range` already in `eclipses.py`; expose as `tool_get_eclipse_calendar(start_date, end_date, city)`. Pin 2026 eclipse dates in tests. **Bundle with PR 3.**
- [ ] **PR 5 [P2, M, E+G]** Panchanga Shuddhi — new `panchanga_shuddhi.py`; evaluates all 5 angas (Vaaram, Tithi, Nakshatra, Yoga, Karana) against classical malefic lists (Rikta tithis, inauspicious nakshatras, 27 Nithya Yogas quality, Vishti karana, cross-anga combinations: Dagdha, Hutasana, Marana, Tri-pushkara, Amrita Siddhi). Returns per-anga verdict + composite score. Differentiator: Drik Panchang shows categorical flags only — no public numeric score. New MCP tool `tool_get_panchanga_shuddhi`. **Version 1.10.3.**

### Tier 3 / speculative (no fixed week)

File or pick up when relevant; not on the critical path.

- [ ] **[P3, M, U]** Dark mode (cream theme is brand; dark variant for evening pooja)
- [ ] **[P3, M, U]** Audio pronunciation for transliterated terms (diaspora)
- [ ] **[P3, M, F]** Personal almanac ICS (`personal/almanac.py`) — per-devotee Tarabalam/Chandrabalam-only feed
- [ ] **[P3, L, F]** Kuta-score compatibility (`personal/kuta.py`) — Ashta Kuta 36-point match
- [ ] **[P3, S, G]** Generator: HTML one-pager for printing/forwarding
- [ ] **[P3, M, G]** Generator: image of today (Pillow or headless Chrome)
- [ ] **[P3, S, G]** CLI subcommands (`panchangam today hyderabad`, `panchangam muhurta wedding …`)
- [ ] **[P3, S, E]** Pada-level nakshatras (4 padas per nakshatra)
- [ ] **[P3, M, E]** Non-Telugu maasam conventions (Purnimanta) as engine parameter

---

## Phase-at-a-glance — **revised 2026-06-16: engines before Vite**

| Phase | When | Theme | Scale |
|---|---|---|---|
| 1 | Week 1 | First Six (P0 must-dos) | XS each, 1 day total ✓ |
| 2 | Weeks 2–3 | Banked stabilizers (CI, SEO head, docs starts) | 10 PRs ✓ |
| **6** | **Weeks 4–7** | **Engine unification** (forward-year pin → EngineCore → facts_at → flags → vocab → ayanamsa) | **L — next** |
| **7** | **Weeks 8–10** | **Engine quality + library polish** (eclipses, public Python API, MCP tests, ICS golden, per-anga ICS) | **several S** |
| **3** | **Weeks 11–14** | **Vite + TS migration** (now against final Python shape) | L, 1 sustained PR |
| 4 | Weeks 15–16 | UI/UX harvest (now cheap) | 3–4 batched PRs |
| 5 | Week 17 | PWA | M, 1 PR |
| 8 | Week 18+ | Additive features (festival explainer, embed, timeline, etc.) | varied |
| T3 | n/a | Speculative backlog | filed as needed |

**Why engines first** (decided 2026-06-16): the Python↔JS scorer parity that Vite is meant to unify needs Python to be in its final shape, otherwise the TS scorer gets rebuilt against post-Phase-6 changes. Doing engines first means TS is built once. Festival explainer (Phase 8) also benefits from the expanded deciding-moment vocab landing in Phase 6.

**Interruption-safe points (revised):** after Phase 2 ✓, **after Phase 7** (engines stable, library API exposed, but no UI shift yet), after Phase 5 (Vite + PWA shipped, UI/UX harvested). Each leaves the project strictly better; stopping at any is fine.

---

## Clusters (reference detail)

Same items as in the phased sequencing, organized by area. Detailed first-steps and file references live here. Check items off in **both** places when you ship them.

### Cluster A — Engine & computation

- [ ] **[Phase 6] [P1, L, E]** Unify the three engines around one `EngineCore`. _First step:_ extract the SS implementation into `EngineCore` and verify Vakya/Drik against the existing 515-test pin.
- [ ] **[Phase 6] [P1, M, E]** Refactor `facts_at` to consume `PanchangamDay` spans instead of re-deriving at every slot.
- [ ] **[Phase 6] [P1, S, E]** Reconcile `_special_flags` across engines. DP-verify Drik's 3-point vs SS's 2-point sankranti check; unify in `EngineCore`. Refs: [drik.py:179](telugu_panchangam/engines/drik.py:179), [surya_siddhanta.py:214](telugu_panchangam/engines/surya_siddhanta.py:214), [vakya.py:176](telugu_panchangam/engines/vakya.py:176).
- [ ] **[Phase 6] [P1, M, E]** Expand festival deciding-moment vocabulary. Convert inline-cased festivals to the vocabulary.
- [ ] **[Phase 6] [P2, M, E]** **Ayanamsa as engine parameter (engine-only — UI surface parked indefinitely).** Threaded through `EngineCore`. Lahiri default; add Raman, Krishnamurti, true Chitrapaksha.
- [ ] **[Phase 7] [P2, M-L, E]** Eclipse precision audit against USNO/NASA tables for the next 10 years. Add `tests/test_eclipses_decade.py`.
- [ ] **[Phase 6 prelude] [P1, L, T]** **Forward-year festival regression (2027–2030)** — 4 anchor festivals × 4 years × 3 engines, DP-verified. Pin before EngineCore refactor.
- [ ] **[Phase 6] [P2, S, E]** Sub-anga (ghati / vighati) precision pass on Tara nakshatra cusps.
- [ ] **[Tier 3] [P3, S, E]** Pada-level nakshatra resolution.
- [ ] **[Tier 3] [P3, M, E]** Non-Telugu maasam conventions (Purnimanta).
- [ ] **[Phase 7] [P2, XS, E]** Remove dead Vakya imports at [vakya.py:7](telugu_panchangam/engines/vakya.py:7).

### Cluster B — Library, generators & public API

- [ ] **[Phase 7] [P1, S, G]** Public Python library API — `from telugu_panchangam import day_for(city, date, system='drik')`.
- [ ] **[Phase 7] [P2, M, G]** Per-anga ICS variant feeds (Ekadashi-only, Festivals-only, Pournami/Amavasya-only).
- [ ] **[Phase 7] [P2, S, T]** ICS golden-snapshot test — Hyderabad / drik, 3-day stretch, byte-equality after DTSTAMP normalization.
- [ ] **[Phase 7] [P2, S, G]** Fix `find_muhurta` MCP signature drift at [mcp/server.py:167](telugu_panchangam/mcp/server.py:167).
- [ ] **[Phase 7] [P2, XS, G]** Remove dead `d += timedelta(days=1)` at [tools.py:395](telugu_panchangam/mcp/tools.py:395).
- [ ] **[Tier 3] [P3, S, G]** Generator: HTML one-pager.
- [ ] **[Tier 3] [P3, M, G]** Generator: image of today.
- [ ] **[Tier 3] [P3, S, G]** CLI subcommands.

### Cluster C — UI/UX (public site behavior)

Most of these block on Phase 3 (Vite swap) to be done cheaply.

- [ ] **[Phase 4] [P1, S, U]** Fix sub-AA muted-label contrast. Refs: `docs/index.html:173, 86, 175, 180, 253, 232, 228, 224`.
- [ ] **[Phase 4] [P1, XS, U]** `<main>` landmark + skip-to-content link.
- [ ] **[Phase 4] [P1, S, U]** Mobile drawer & help-sheet as real dialogs. Refs: `#m-more-drawer` (`:1018`), `#m-help-sheet` (`:1040`).
- [ ] **[Phase 4] [P1, S, U]** City auto-detect + searchable selector.
- [ ] **[Phase 4] [P1, S, U]** "Times shown in <city> local time" affordance.
- [ ] **[Phase 4] [P1, XS, U]** 1-click "Add to Google Calendar".
- [ ] **[Phase 4] [P1, S, U]** Per-anga "what is this" popovers (Tithi / Nakshatra / Yoga / Karana).
- [ ] **[Phase 4] [P1, M, U]** Hero focal point on mobile — collapse brand, anga grid above fold.
- [ ] **[Phase 8] [P2, M, U]** Visual sun/moon timeline for sunrise→sunset windows.
- [ ] **[Phase 8] [P2, M, U]** Compare engines side-by-side for one date.
- [ ] **[Phase 8] [P2, S, U]** Print stylesheet.
- [ ] **[Phase 4] [P2, S, U]** Subscribe wizard with per-platform 1-click flows.
- [ ] **[Phase 4] [P2, S, U]** Skeleton / empty / error states for feed fetches.
- [ ] **[Phase 8] [P2, M, U]** Month grid view for "Special days".
- [ ] **[Phase 4] [P2, S, U]** `<details>`/`<summary>` for the Muhurtam collapsible at [index.html:1268](docs/index.html:1268).
- [ ] **[Phase 8] [P2, M, U]** Save image of today / Print this day next to WhatsApp share.
- [ ] **[Phase 8] [P2, S, U]** Onboarding tooltip on first visit.
- [ ] **[Tier 3] [P3, M, U]** Dark mode.
- [ ] **[Tier 3] [P3, M, U]** Audio pronunciation for transliterated terms.

### Cluster D — Infrastructure (build, loading, SEO)

- [ ] **[Phase 3] [P1, L, I]** **Vite + TypeScript build pipeline.** Replace `scripts/build_landing_page.py` 18-line copier and the 4321-line monolith with `src/` modules → `dist/`.
- [ ] **[Phase 2] [P1, XS, I]** JSON-LD structured data (`WebSite` + `SoftwareApplication`).
- [ ] **[Phase 2] [P1, XS, I]** `<link rel="canonical">` + OG image width/height.
- [ ] **[Phase 2] [P1, XS, I]** `sitemap.xml` + `robots.txt`.
- [ ] **[Phase 3] [P1, S, I]** Self-host fonts or preload (Fraunces / Libre Baskerville / Inter currently render-blocking).
- [ ] **[Phase 2] [P2, XS, I]** OG / Twitter share preview polish.
- [ ] **[Phase 5] [P1, M, F]** **PWA installability** — manifest, service worker, install prompt, offline cache.

### Cluster E — Tests & verification

- [x] **[Phase 1] [P0, XS, T]** CNAME pin guard (First Six) — PR #76.
- [x] **[Phase 1] [P0, XS, T]** Version-sync test `pyproject.toml ↔ server.json` (First Six) — PR #74.
- [ ] **[Phase 3] [P1, S, T]** Python ↔ JS parity test for `ACTIVITY_RULES` + scoring weights.
- [ ] **[Phase 6 prelude] [P1, L, T]** Forward-year festival regression (2027–2030) — pin before EngineCore refactor.
- [ ] **[Phase 4] [P1, S, T]** Deploy-drift guard for runtime JSON sidecars (lagna + gochara fetches).
- [ ] **[Phase 7] [P2, S, T]** MCP tool test for `tool_get_daily_horas` ([mcp/tools.py:280](telugu_panchangam/mcp/tools.py:280)).
- [ ] **[Phase 7] [P2, S, T]** MCP tool test for `tool_get_lagna_transitions`.
- [ ] **[Phase 7] [P2, S, T]** ICS golden-snapshot test.
- [ ] **[Phase 4] [P2, S, T]** Browser smoke: muhurta tier rendered assertion.

### Cluster F — Release & distribution

- [x] **[Phase 1] [P0, XS, R]** Bump `server.json` to 1.8.0 + version-sync test (First Six) — PR #74.
- [x] **[Phase 1] [P0, XS, R]** README_PYPI catch-up (First Six) — PR #75.
- [x] **[Phase 1] [P0, S, R]** Gate `publish.yml` on pytest (First Six) — PR #74.
- [ ] **[Phase 2] [P1, XS, R]** Sync `server.json` version in `publish.yml`.
- [ ] **[Phase 2] [P1, S, R]** Auto-create GitHub Release with CHANGELOG section on tag push.
- [ ] **[Phase 2] [P1, XS, R]** CHANGELOG/Unreleased gate in `publish.yml`.
- [ ] **[Phase 8] [P2, M, R]** Backfill `CHANGELOG.md` v1.0.5..v1.7.1.
- [ ] **[Phase 8] [P2, M, R]** MCP-registry mcp-publisher workflow.

### Cluster G — CI/CD & repo hygiene

- [x] **[Phase 1] [P0, XS, C]** Branch sweep + `delete-branch-on-merge` + retire `jules-dev` + sweep 11 `jules-*` (First Six) — 2026-06-16. Remote count 52 → 29.
- [ ] **[Phase 2] [P1, XS, C]** Dependabot config.
- [ ] **[Phase 2] [P1, XS, C]** Concurrency groups on every workflow.
- [ ] **[Phase 2] [P1, XS, C]** Python matrix 3.10–3.13 in `ci.yml`.
- [ ] **[Phase 2] [P1, XS, C]** Branch protection on master with `required_status_checks=[test]`.
- [ ] **[Phase 2] [P1, S, C]** Pin third-party Actions to SHAs.
- [ ] **[Phase 2] [P1, S, C]** CodeQL + pip-audit security workflow.
- [ ] **[Phase 2] [P2, S, C]** Reconcile `requirements.txt` and `pyproject.toml`.
- [ ] **[Phase 2] [P2, S, C]** Lockfile via `uv pip compile`.
- [ ] **[Phase 2] [P2, S, C]** `.editorconfig` + minimal pre-commit.
- [ ] **[Phase 2] [P2, XS, C]** `ci.yml` nullglob fix.

### Cluster H — Project documentation

- [x] **[Phase 1] [P0, XS, D]** Fill blank CoC enforcement email (First Six) — PR #75.
- [ ] **[Phase 2] [P1, M, D]** `ARCHITECTURE.md` — mermaid layer-cake + engine-core boundary.
- [ ] **[Phase 2] [P1, M, D]** `MAINTENANCE_RUNBOOK.md` — release flow, cron map, add-a-city, add-a-festival.
- [ ] **[Phase 8] [P2, M, D]** On-site Troubleshooting page.
- [ ] **[Phase 8] [P2, S, D]** What's-new page on site mirrored from CHANGELOG.

### Cluster I — Additive features (devotee-facing)

- [ ] **[Phase 8] [P2, M, F]** Embeddable widget (`src/embed/`).
- [ ] **[Phase 8] [P2, S, F]** Weekly digest ICS feed.
- [ ] **[Phase 8] [P2, M, F]** Festival explainer module + linkable `festivals.html`.
- [ ] **[Phase 5] [P1, M, F]** PWA installability (cross-listed in Cluster D).
- [ ] **[Tier 3] [P3, M, F]** Personal almanac ICS (`personal/almanac.py`).
- [ ] **[Tier 3] [P3, L, F]** Kuta-score compatibility (`personal/kuta.py`).

**Killed:** REST API for per-request muhurta — staying on GitHub Pages.

---

## Maintenance note

- **When an item ships:** mark `[x]` in BOTH the phased sequencing AND its cluster entry. Append the PR/SHA in parens. Example: `- [x] [Phase 1] [P0, XS, T] CNAME-pin guard (PR #71, 2026-06-17)`.
- **When a new opportunity surfaces:** file it under the closest cluster with `[Phase ?] [P_, Effort, Area]` tags, and add it to the appropriate phase below.
- **When a decision changes:** update the Decisions table at the top, then propagate consequences down through Phases and Clusters in the same edit.
- **When the plan goes stale:** the file's last-updated date at the top is your tell. Re-read and reconcile against the current `master` before starting a new phase.
