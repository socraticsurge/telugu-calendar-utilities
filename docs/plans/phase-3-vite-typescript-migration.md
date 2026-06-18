
# Phase 3 — Vite + TypeScript migration plan

## 1. Executive summary

Phase 3 splits today's single-file SPA at `docs/index.html` (4,356 lines: ~950 lines of CSS, ~2,715 lines of inline JS, plus an 182-line sidecar `docs/muhurta-scorer.js`) into a Vite + TypeScript src tree that builds to `dist/` and continues to deploy to GitHub Pages on the pinned custom domain `panchangam.astrochaganti.com`. The frozen engine core stays untouched. The only Python work in scope is adding read-only export scripts (`tools/export_activity_rules.py`, `tools/export_parity_fixture.py`) so the TS scorer and Python engine share a single source of truth for the `ACTIVITY_RULES` table and a slot-level parity fixture.

The plan is built on three opinions. First: **stay vanilla TypeScript (no React/Svelte) in Phase 3.** The page is imperative DOM mutation today and works; framework choice can layer on later and is not on the critical path for PWA (Phase 5). Vite + native TS modules + per-component `mount(container)` classes is the minimum diff that gets us typed code, a real build step, Vitest, and HMR. Second: **the Verify critique is right about scope inflation.** The Design proposal underbid `muhurta-scorer.js` (182 lines, not the 700-line surface the Design hinted at), underbid the parseDescription regex risk, and missed at least six concrete things that break on the first PR — `tests/test_deploy_drift.py`, `tests/test_browser_smoke.py`, `MORE.moveIds` form state, `onclick=` inline attributes, `keep_files: true` plus hashed bundle names, and help-sheet source-node hoisting. These all become explicit PRs or in-PR steps below. Third: **devotee-visible value at each step.** The PR sequence ships HMR/dev-server first (devs benefit), then bundle parity (no user change), then per-panel TS rewrites paired with one user-visible win per PR where possible (Tarabalam mobile-card fix, Muhurta loading state, Today print stylesheet, etc.).

The parity strategy is **codegen, not re-typing.** A new `tools/export_activity_rules.py` reads `telugu_panchangam.personal.muhurta.ACTIVITY_RULES` (already a dict in Python at `telugu_panchangam/personal/muhurta.py:107-225`) and writes `src/data/activity-rules.generated.json`. CI fails if the committed JSON is stale. A parity fixture (`src/data/parity-fixture.generated.json`, ~50 (day, activity, profiles) → expected tier+dosha tuples) is consumed by both `tests/test_js_parity.py` (Python side) and `src/scorer/__tests__/parity.test.ts` (TS side). The three known drifts — yoga-name spellings, `MU_NITYA_PARTIAL_WINDOW_MIN` unit, the personal-dosha inline cascade — are fixed *in* the migration by deleting the inline copies and importing from `src/scorer/`.

The deploy path is the riskiest single surface. `deploy-landing.yml`, `generate.yml`, `gochara.yml`, `lagna.yml` all currently push to gh-pages with `cname: panchangam.astrochaganti.com`; three of four use `keep_files: true`. Vite produces hashed filenames (`assets/main-<hash>.js`), so `keep_files: true` would let stale bundles accumulate forever on gh-pages. The plan flips the **landing deploy** to `keep_files: false` (it's the workflow that owns the landing surface) while **generate/gochara/lagna keep `keep_files: true`** (they only touch `feeds/`, `gochara.json`, `*-lagna.json` — they must not wipe the bundled assets). To make this safe, the landing deploy stages the currently-live feeds back into `dist/` before publishing. The CNAME pin test (`tests/test_deploy_drift.py:154-175`) stays green; the four deploy workflows keep their `cname:` lines verbatim.

Finally, **the migration ends with `docs/index.html` and `docs/muhurta-scorer.js` removed, but `docs/tracking/`, `docs/plans/`, `docs/specs/`, `docs/superpowers/`, `docs/NOW.md`, `docs/GUIDELINES.md` all moved to a new top-level `tracking/`/etc directories in PR 1** so the user's living-state workflow doesn't disappear mid-migration. `ARCHITECTURE.md:139,175` and `MAINTENANCE_RUNBOOK.md:124` get a doc-sweep PR before cutover.

## 2. Current state — what's in docs/index.html today

All line ranges from the Map.

| Lines | What | Phase 3 destination |
|---|---|---|
| 1–2 | `<!DOCTYPE><html lang="en">` | `index.html` (root) |
| 3–1005 | `<head>` — meta, OG/Twitter, JSON-LD, fonts preconnect, inline `<style>` | `index.html` head + `src/styles/main.css` |
| 53–1004 | Inline `<style>` (~950 lines) | Split: global `src/styles/main.css` (53–440), per-component `*.css` (441–1004 mobile shell + panel-specific blocks) |
| 1006–1024 | `<header id="m-topbar">` | `src/components/MobileShell/MobileTopbar.ts` |
| 1026–1047 | `<nav id="m-bottomnav">` | `src/components/MobileShell/MobileBottomNav.ts` |
| 1049 | scrim | `src/components/MobileShell/index.ts` |
| 1053–1072 | `<aside id="m-more-drawer">` | `src/components/MobileShell/MoreDrawer.ts` |
| 1075–1085 | `<aside id="m-help-sheet">` | `src/components/MobileShell/HelpSheet.ts` |
| 1089–1161 | `#today-help-src` (hidden help reservoir) | **Hoisted to top-level `<template>` in `index.html`** (Verify point 9 — also do this for `#go-help`, `#tb-help`) |
| 1163–1181 | Hero | `src/components/HeroBrand/` |
| 1183–1219 | Tool tabs + `#tp-selector-row` | `src/components/ToolTabs/` + `src/components/SelectorRow/` |
| 1214–1219 | `#panel-today` mount point | `src/components/TodayPanel/` |
| 1221–1369 | `#panel-tarabalam` — note `#mu-section` is **nested inside** this panel (Verify point 11) | `src/components/TarabalamPanel/` containing `MuhurtaSearch.ts` as a child |
| 1371–1423 | `#panel-gochara` | `src/components/GocharaPanel/` |
| 1426–1430 | `#special-days-card` | `src/components/SpecialDaysCard/` |
| 1432–1488 | `#subscribe` (own `sub-city`/`sub-system` selects — distinct from `tp-city`/`tp-system`) | `src/components/SubscribeCard/` |
| 1490–1610 | `#card-system`, `#card-mcp` | `src/components/SystemCard/`, `src/components/McpCard/` |
| 1612–1616 | `<footer>` | `src/components/SiteFooter/` |
| 1623 | `<script src="muhurta-scorer.js">` (182 lines, exposes `mu*`/`computePersonalDosha` to `window`) | `src/scorer/` TS modules, NO `window` assignment |
| 1624–4338 | Primary inline `<script>` (~2,715 lines) | `src/lib/` + `src/data/` + `src/components/*/index.ts` + `src/scorer/` |
| 1625 | `FEED_BASE_URL='https://panchangam.astrochaganti.com/feeds/'` | `src/lib/feed-loader.ts` |
| 1627–1631 | `CITY_GROUPS` (22 cities × 3 display groups) | `src/data/cities.ts` (JS-only display metadata — explicitly NOT pushed to Python; Verify point 13) |
| 1632 | `SYSTEMS` | `src/data/systems.ts` |
| 1697–1738 | ICS parsing | `src/lib/ics.ts` |
| 1740–1774 | `TIME_FMT` (localStorage `tc-time-fmt`) | `src/lib/time-fmt.ts` |
| 1776–1842 | Ekadashi/festival/choghadiya night tables | `src/data/festivals.ts`, `src/data/choghadiya.ts` |
| 1844–1928 | Horas | `src/data/horas.ts` + `src/lib/horas.ts` |
| 1930–1988 | Lagna async layer | `src/lib/lagna-loader.ts` |
| 1994–2099 | `parseDescription` (highest-risk regex surface) | `src/lib/parse-description.ts` — separate PR with golden-snapshot test before anything else consumes it |
| 2122–2292 | `renderPreview` | `src/components/TodayPanel/render.ts` |
| 2294–2323 | `renderUpcoming` | `src/components/SpecialDaysCard/` |
| 2325–2366 | `FEED_CACHE`, `LAST_EVENTS`, `loadFeed` | `src/lib/feed-loader.ts` |
| 2368–2439 | Today WhatsApp share | `src/lib/share.ts` |
| 2441–2660 | Tarabalam data + state + `calcTarabalam` | `src/components/TarabalamPanel/calc.ts` + `src/lib/profiles-store.ts` |
| 2662–2801 | `renderTarabalam` | `src/components/TarabalamPanel/render.ts` |
| 2802–2827 | Tarabalam share | `src/lib/share.ts` |
| 2836–2866 | Help-sheet glue | `src/components/MobileShell/HelpSheet.ts` |
| 2868–2887 | `switchTool` (tabs + hash routing + lazy Gochara) | `src/components/ToolTabs/router.ts` |
| 2889–3016 | Gochara data layer + `loadGochara` | `src/lib/gochara-loader.ts` |
| 3018–3292 | `renderGochara` | `src/components/GocharaPanel/render.ts` |
| 3293–3315 | Gochara share | `src/lib/share.ts` |
| 3317–3378 | `muAssignTiers`/`muMin`/`muSubtract` + nitya tables | `src/scorer/tiers.ts` + `src/scorer/nitya.ts` |
| 3380–3524 | Meeus low-precision Sun/Moon longitudes + special-yogas tables + `muFactsAt` | `src/scorer/ephemeris.ts` + `src/scorer/special-yogas.ts` |
| 3526–3553 | Tithi-family helpers | `src/data/tithis.ts` |
| 3555–3664 | `MU_ACTIVITY` (inline duplicate of Python `ACTIVITY_RULES`) | **Deleted** — imported from `src/data/activity-rules.generated.json` |
| 3666–3672 | `htmlEsc` | `src/lib/html.ts` |
| 3674–4060 | `findMuhurta` (~387 lines) | `src/components/MuhurtaSearch/find.ts` (uses `src/scorer/`) |
| 4081–4152 | `renderMuhurta` | `src/components/MuhurtaSearch/render.ts` |
| 4154–4174 | Muhurta share | `src/lib/share.ts` |
| 4176–4203 | Page bootstrap | `src/main.ts` |
| 4205–4337 | `mobileShell()` IIFE (~130 lines) | `src/components/MobileShell/index.ts` |
| 4339–4340 | GoatCounter `<script async>` | Stays in `index.html` (must load before `analytics.ts`) |
| 4341–4354 | Outbound-link delegated tracking | `src/lib/analytics.ts` |

**Inline `onclick=` handlers (Verify point 14, must be rewired in every component PR):** `docs/index.html:1185-1190` `switchTool(...)`, `docs/index.html:1209` `setTimeFmt(...)`, `docs/index.html:1304` `muToggleMobile()`, `docs/index.html:1353` `findMuhurta()`, `docs/index.html:1375,1498,1507,1524,1540,1566` `toggleReadMore(...)`. All replaced by `addEventListener` wiring inside each component's `mount()`. **No `window.*` re-exports.** `tests/test_browser_smoke.py:160-166` asserts `typeof window.findMuhurta === 'function'` and must be updated in lockstep (PR 5).

**Eclipse handling cross-cuts (Verify point 12):** `docs/index.html:2070-2079` (parse), `:2114-2120` (`eclipseChip`), `:2311` (upcoming), `:3712-3717` (muhurta day-skip). All four consumers go through `src/lib/parse-description.ts` (eclipse field) + `src/lib/eclipse-chip.ts` (one shared chip component).

## 3. Proposed src/ layout

```
telugu-calendar-utilities/
├── index.html                  # Vite entry at REPO ROOT (not docs/). HTML SKELETON ONLY.
│                               # <head>: meta/OG/JSON-LD/fonts preconnect (copy of legacy 3-52)
│                               # <body>:
│                               #   <template id="today-help-src">…</template>  ← HOISTED from legacy 1089-1161
│                               #   <template id="go-help-src">…</template>      ← HOISTED from #panel-gochara
│                               #   <template id="tb-help-src">…</template>      ← HOISTED from #panel-tarabalam
│                               #   <header id="m-topbar">…</header>             ← static markup, hydrated by JS
│                               #   <nav id="m-bottomnav">…</nav>
│                               #   <div id="scrim"></div>
│                               #   <aside id="m-more-drawer">…</aside>
│                               #   <aside id="m-help-sheet">…</aside>
│                               #   <div id="app" class="page"></div>            ← mount target (was <div class="page">)
│                               #   GoatCounter <script async> tag
│                               #   <script type="module" src="/src/main.ts"></script>
├── vite.config.ts              # See §5
├── tsconfig.json               # strict, ES2022, moduleResolution: bundler
├── package.json                # See §5
├── public/                     # Vite publicDir. Files here copied verbatim to dist/ at build.
│   ├── CNAME                   # 'panchangam.astrochaganti.com\n' — belt-and-braces. peaceiris/
│   │                           # actions-gh-pages re-asserts via the cname: input, but bundling
│   │                           # CNAME means a hand-deployed dist/ also works.
│   ├── og-image.png            # Moved from docs/
│   ├── robots.txt              # Moved from docs/
│   ├── sitemap.xml             # Moved from docs/
│   ├── feeds/                  # POPULATED AT DEPLOY TIME by generate.yml / lagna.yml + the
│   │                           # rsync-back step in deploy-landing.yml. NOT committed.
│   └── gochara.json            # Same — populated at deploy time by gochara.yml.
├── src/
│   ├── main.ts                 # ~80 LOC bootstrap. Imports './styles/main.css', wires components,
│   │                           # starts MobileShell, attaches analytics delegate.
│   ├── styles/
│   │   └── main.css            # Global CSS (legacy 53-440 minus the panel-specific blocks that
│   │                           # move into components/). CSS variables, hero, base reset, .page,
│   │                           # .card, .selector, .btn shared across panels.
│   ├── scorer/                 # PURE: no DOM, no fetch, no globals. Importable from Node (Vitest).
│   │   ├── index.ts            # Re-exports: scoreTier, relativeTier, lagnaPosition, lagnaVerdict,
│   │   │                       # isFavourableLagna, lagnaClassOf, computePersonalDosha,
│   │   │                       # computeDayDosha, factsAt, evaluateSlot, assignTiers.
│   │   ├── types.ts            # ActivityKey union (auto-generated from activity-rules.generated.json),
│   │   │                       # LagnaClass ('Chara'|'Sthira'|'Dvisvabhava'), TithiFamily, ChandraBand,
│   │   │                       # PersonalDoshaLabel, DayDoshaLabel, ScoredSlot.
│   │   ├── tiers.ts            # scoreTier + relativeTier + assignTiers (port of legacy 3317-3378 +
│   │   │                       # muhurta-scorer.js's tier helpers).
│   │   ├── lagna.ts            # lagnaPosition/Verdict/Class/AtMin + MU_LAGNA_KENDRA/TRIKONA
│   │   │                       # (port of muhurta-scorer.js).
│   │   ├── dosha.ts            # computePersonalDosha + computeDayDosha (single source of truth —
│   │   │                       # the inline cascade at legacy ~4025-4026 is DELETED, not migrated).
│   │   ├── ephemeris.ts        # muJD/muLahiri/muSunLong/muMoonLong (port of legacy 3380-3524).
│   │   ├── special-yogas.ts    # MU_SARVARTHA / MU_AMRITA_SIDDHI / MU_VISHA_TITHI / MU_DAGDHA /
│   │   │                       # MU_PUSHKARA + specialYogasAt (port of legacy 3380-3524).
│   │   ├── facts.ts            # factsAt(dt, vaaram) — composes ephemeris + nakshatra + tithi + yoga.
│   │   ├── nitya.ts            # NITYA_HARD_AVOID/PENALTY/AUSPICIOUS/BONUS/PARTIAL constants —
│   │   │                       # match telugu_panchangam.personal.nitya_yoga (already a Python source
│   │   │                       # of truth, imported at muhurta.py:27-29).
│   │   ├── activity.ts         # readActivityRule(key): reads ACTIVITY_RULES from
│   │   │                       # src/data/activity-rules.generated.json. NO inline duplicate of
│   │   │                       # the Python table.
│   │   ├── evaluate-slot.ts    # evaluateSlot(day, activity, profiles): pure function, the deep
│   │   │                       # extraction Verify point 1 calls out. Equivalent to legacy
│   │   │                       # 3700-3950 (the per-slot loop body of findMuhurta), but pure.
│   │   └── __tests__/
│   │       ├── tiers.test.ts
│   │       ├── lagna.test.ts
│   │       ├── dosha.test.ts
│   │       ├── ephemeris.test.ts        # Reuses tests/js/test_muhurta_scorer.js golden cases.
│   │       └── parity.test.ts           # Loads parity-fixture.generated.json, asserts evaluateSlot
│   │                                    # matches the Python-computed expectation.
│   ├── data/                   # PURE DATA. Two kinds:
│   │                           #  (a) Hand-typed display metadata with no Python source.
│   │                           #  (b) *.generated.json codegen'd from Python; in git; CI-checked.
│   │   ├── cities.ts           # CITY_GROUPS (22 cities × 3 display groups). JS-ONLY per Verify
│   │   │                       # point 13 — does NOT push to telugu_panchangam/cities.py.
│   │   ├── systems.ts          # SYSTEMS
│   │   ├── nakshatras.ts       # TB_NAKSHATRAS, TARA_NAMES, TARA_GOOD
│   │   ├── rashis.ts           # TB_RASIS
│   │   ├── tithis.ts           # EKADASHI_NAMES, TITHI_NAMES_ORDER, TITHI_ALIASES, TITHI_NUMBER_FAMILY
│   │   ├── horas.ts            # HORA_LORDS, HORA_GLYPH, HORA_PALETTE_CLASS, HORA_FAVOURABILITY,
│   │   │                       # WEEKDAY_TO_LORD_IDX
│   │   ├── choghadiya.ts       # CHOG_NIGHT_START, CHOG_NIGHT_SEQ
│   │   ├── festivals.ts        # festivalNames, chipEmoji, specialLabel (display labels only;
│   │   │                       # rules live in engines/base.py, untouched)
│   │   ├── gochara-tables.ts   # GO_FAV, GO_VEDHA, GO_EXEMPT, GO_NODES, GO_LAYOUT
│   │   ├── activity-rules.generated.json   # GENERATED. Codegen'd by tools/export_activity_rules.py.
│   │   │                                   # CI fails if stale (drift test).
│   │   └── parity-fixture.generated.json   # GENERATED. ~50 (day, activity, profiles) → expected
│   │                                       # (score, tier, personal_dosha, day_dosha) cases.
│   ├── lib/                    # Pure JS utilities; no DOM, no inline rules.
│   │   ├── ics.ts              # unfoldICS + parseEvents (legacy 1697-1738)
│   │   ├── parse-description.ts # The regex state machine (legacy 1994-2099). HAS GOLDEN-SNAPSHOT TEST.
│   │   ├── feed-loader.ts      # FEED_CACHE + LAST_EVENTS + loadFeed (legacy 2325-2366). Shared by
│   │   │                       # TodayPanel, TarabalamPanel, MuhurtaSearch, SpecialDaysCard.
│   │   ├── lagna-loader.ts     # LAGNA_CACHE + loadLagna + lagnaDayFor + lagnaSegments (legacy 1930-1988).
│   │   ├── gochara-loader.ts   # loadGochara fetching /gochara.json (legacy 2889-3016).
│   │   ├── time-fmt.ts         # TIME_FMT + fmtT + dayMark + fmtRange + setTimeFmt (legacy 1740-1774).
│   │   ├── profiles-store.ts   # SHARED state. tbProfiles, tbSaveProfiles, localStorage 'tc-tb-profiles',
│   │   │                       # tiny pub/sub so TarabalamPanel + GocharaPanel + MuhurtaSearch react.
│   │   ├── selection-store.ts  # Persists tp-city / tp-system / tp-date / tc-time-fmt + sub-city /
│   │   │                       # sub-system to localStorage so mobile drawer re-mount (or any tab
│   │   │                       # re-mount) restores state — addresses Verify point 10.
│   │   ├── horas.ts            # computeHoras + markFirstMidnightCrossing + horaCell rendering
│   │   │                       # (legacy 1844-1928 split: data → data/, logic → here).
│   │   ├── eclipse-chip.ts     # Single chip component shared by Today + SpecialDays + Muhurta
│   │   │                       # (Verify point 12).
│   │   ├── share.ts            # buildShareText + share* (legacy 2368-2439, 2802-2827, 3293-3315, 4154-4174).
│   │   ├── analytics.ts        # gcEvent() + outbound-link delegate (legacy 4341-4354). Loaded last.
│   │   └── html.ts             # htmlEsc (legacy 3666-3672).
│   └── components/             # ONE FOLDER per visible UI unit. Each exports a class with
│                               # `mount(container: HTMLElement)` and (where needed) `update(state)`
│                               # and `unmount()`. CSS is co-located and imported in index.ts.
│       ├── HeroBrand/{index.ts, HeroBrand.css}
│       ├── ToolTabs/{index.ts, router.ts, ToolTabs.css}
│       ├── SelectorRow/{index.ts, SelectorRow.css}
│       ├── TodayPanel/{index.ts, render.ts, TodayPanel.css}
│       ├── TarabalamPanel/{index.ts, calc.ts, render.ts, ProfileEditor.ts, TarabalamPanel.css}
│       ├── MuhurtaSearch/{index.ts, find.ts, render.ts, MuhurtaSearch.css}
│       │                       # NOTE: lives inside TarabalamPanel in markup terms (legacy 1303-1369
│       │                       # is a child of #panel-tarabalam at 1221-1369) — Verify point 11.
│       │                       # In TS, MuhurtaSearch is a sibling component that TarabalamPanel
│       │                       # mounts into its own DOM, sharing tb-from/tb-to via SelectorRow state.
│       ├── GocharaPanel/{index.ts, render.ts, GocharaPanel.css}
│       ├── SpecialDaysCard/{index.ts, render.ts, SpecialDaysCard.css}
│       ├── SubscribeCard/{index.ts, SubscribeCard.css}
│       ├── SystemCard/{index.ts, SystemCard.css}
│       ├── McpCard/{index.ts, McpCard.css}
│       ├── SiteFooter/{index.ts, SiteFooter.css}
│       └── MobileShell/
│           ├── index.ts        # matchMedia(620px), scrim, hash routing, swipe gestures.
│           ├── MobileTopbar.ts
│           ├── MobileBottomNav.ts
│           ├── MoreDrawer.ts   # Conditional rendering — NOT surgical DOM relocation.
│           │                   # Uses selection-store so re-mounted selects restore state
│           │                   # (Verify point 10).
│           ├── HelpSheet.ts    # Clones from <template> hoisted into root index.html
│           │                   # (Verify point 9).
│           └── MobileShell.css
├── tools/                      # Python-side codegen scripts (NEW).
│   ├── export_activity_rules.py   # Reads telugu_panchangam.personal.muhurta.ACTIVITY_RULES,
│   │                              # writes src/data/activity-rules.generated.json.
│   └── export_parity_fixture.py   # Builds ~50 (day, activity, profiles) cases, runs
│                                  # find_muhurta() per case, writes expected (score, tier,
│                                  # personal_dosha, day_dosha) to src/data/parity-fixture.generated.json.
├── tracking/                   # MOVED FROM docs/tracking/ (Verify point 17). Living plans/decisions.
├── plans/                      # MOVED FROM docs/plans/.
├── specs/                      # MOVED FROM docs/specs/.
├── superpowers/                # MOVED FROM docs/superpowers/.
├── tests/                      # Unchanged location, several files rewritten (see §6).
└── (legacy docs/ removed at the END of the migration — never mid-flight)
```

## 4. Python ↔ TS parity strategy

**Chosen approach: codegen from Python, never re-typed by hand, two artefacts, CI drift gate.**

### Artefact A — `src/data/activity-rules.generated.json`

The `ACTIVITY_RULES` dict at `telugu_panchangam/personal/muhurta.py:107-225` (~25 activity rows with `label`, `skip_on_yoga`, `prefer_choghadiya`, `avoid_karana`, `prefer_tithi_class`, `prefer_vara`, `prefer_lagna_class`) is already a Python dict literal. The legacy JS inline copy at `docs/index.html:3555-3664` is a hand-typed duplicate.

**`tools/export_activity_rules.py` sketch:**

```python
#!/usr/bin/env python3
"""Codegen ACTIVITY_RULES → src/data/activity-rules.generated.json.

Runs in CI; commit-checked so a stale export fails the suite.
The TS scorer (src/scorer/activity.ts) reads this file at build time.
"""
import json
import pathlib
import sys
from telugu_panchangam.personal.muhurta import ACTIVITY_RULES

OUT = pathlib.Path(__file__).resolve().parent.parent / 'src/data/activity-rules.generated.json'

def _normalise(rule: dict) -> dict:
    out = {}
    for k, v in rule.items():
        if isinstance(v, tuple):
            out[k] = list(v)
        elif isinstance(v, list):
            out[k] = list(v)
        else:
            out[k] = v
    return out

payload = {
    'generated_by': 'tools/export_activity_rules.py',
    'source': 'telugu_panchangam.personal.muhurta.ACTIVITY_RULES',
    'activities': {k: _normalise(v) for k, v in ACTIVITY_RULES.items()},
}

before = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
after = json.dumps(payload, indent=2, sort_keys=True) + '\n'
OUT.write_text(after, encoding='utf-8')
if before != after and '--check' in sys.argv:
    print('activity-rules.generated.json is stale; re-run without --check.', file=sys.stderr)
    sys.exit(1)
```

A new test `tests/test_activity_rules_export.py` invokes this with `--check` and asserts no drift. CI runs it. The Phase-3 parity tests (Python `tests/test_js_parity.py` and TS `src/scorer/__tests__/parity.test.ts`) both load the same JSON.

### Artefact B — `src/data/parity-fixture.generated.json`

`tools/export_parity_fixture.py` runs the Python `find_muhurta()` over a fixed matrix: 3 cities × 3 systems × 5 dates × 4 representative activities (`travel`, `wedding`, `vehicle`, `gruhapravesha`) × 2 profile shapes (0 profiles, 1 profile with a specific nakshatra/lagna), recording for each top slot: `dt_start`, `dt_end`, `score`, `tier`, `personal_dosha`, `day_dosha`, `reasons[]`. The TS parity test loads the same fixture and asserts `evaluateSlot()` returns the same tuple. Both sides regenerate the fixture from a deterministic seed.

### What handles the three known drifts

- **MU_YOGA_NAMES_27 spellings (`Priti`/`Shula`/`Variyana` vs Python `Preeti`/`Shoola`/`Variyan`)**: `src/scorer/facts.ts` imports `NITYA_YOGA_NAMES` from `src/data/tithis.ts`, which is hand-typed but covered by a new `tests/test_yoga_name_parity.py` asserting `set(JS_NAMES) == set(NITYA_YOGAS_PY)`.
- **`MU_NITYA_PARTIAL_WINDOW_MIN` unit drift**: replaced by `NITYA_PARTIAL_DOSHA_WINDOW` from `telugu_panchangam.personal.nitya_yoga` (already a `timedelta` in Python). The TS side imports the minute-count from `src/scorer/nitya.ts`; the Python export script writes the minute-count into `parity-fixture.generated.json` as the canonical value.
- **Inline personal-dosha cascade at legacy ~4025-4026**: deleted. `src/components/MuhurtaSearch/find.ts` calls `computePersonalDosha()` from `src/scorer/dosha.ts`.

### What is explicitly NOT in scope (Verify points 3 and 13)

- **`scoring-weights.json`**: NOT in Phase 3. The inline integer deltas in `docs/index.html:3777, 3795-3800, 3842, 3858, 3901, 3911-3914, 3935-3950` (+1/-1 tara/chandra/lagna, +2 Abhijit/Amrita, -2 Rikta) are also inline-integer in Python `_evaluate_slot` and friends. Surfacing them as a named `SCORING_WEIGHTS` dict in `muhurta.py` first is a separate prerequisite that belongs in Phase 6, not Phase 3. The TS port matches the inline integers and is covered by the parity fixture.
- **`CITY_GROUPS` push to Python**: NOT in Phase 3. Stays JS-only display metadata in `src/data/cities.ts`.

## 5. Vite config + npm dependencies

**Tool choices and justifications:**

- **Vite 5.x**: stable, framework-agnostic, fast HMR, first-class TS, `publicDir` semantics match the GitHub Pages copy-verbatim deploy story, mature plugin ecosystem for PWA in Phase 5.
- **TypeScript 5.x with `strict: true`**: catches the parseDescription regex output shape mismatches that today only surface at runtime.
- **Vitest 1.x**: same engine as Vite, no separate config, runs the parity test in Node, can import the same `src/scorer/` modules the browser uses.
- **No framework** (no React/Svelte/Preact/Lit): keeps the diff minimum, doesn't preclude PWA (Phase 5 needs service worker + manifest, neither requires a UI framework), keeps the migration reviewable. Imperative DOM mutation is already how the legacy code works.
- **No CSS framework**: 950 lines of hand-written CSS already work and look the way the user signed off on. Don't rewrite.
- **`@vitejs/plugin-legacy` NOT included**: subscribers are on modern browsers; the feeds work on legacy clients independently. If a request comes in, add later.

### `package.json` (excerpt)

```json
{
  "name": "telugu-calendar-utilities-site",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "typecheck": "tsc --noEmit",
    "parity:export": "python tools/export_activity_rules.py && python tools/export_parity_fixture.py",
    "parity:check": "python tools/export_activity_rules.py --check && python tools/export_parity_fixture.py --check"
  },
  "devDependencies": {
    "vite": "^5.4.0",
    "vitest": "^1.6.0",
    "typescript": "^5.5.0",
    "@types/node": "^20.14.0",
    "jsdom": "^24.0.0"
  }
}
```

### `vite.config.ts`

```ts
import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({
  // Site is served at panchangam.astrochaganti.com/ — root path.
  base: '/',
  publicDir: resolve(__dirname, 'public'),
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: resolve(__dirname, 'index.html'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: false,
    include: ['src/**/__tests__/**/*.test.ts'],
  },
});
```

**Decision recorded:** hashed filenames are kept (default Vite behaviour). The `keep_files` strategy below handles the accumulation risk (Verify point 7).

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true
  },
  "include": ["src", "vite.config.ts"]
}
```

## 6. Deploy workflow changes — exact diffs

### 6.1 `.github/workflows/deploy-landing.yml`

```diff
 name: Deploy Landing Page

 on:
   push:
     branches: [master]
     paths:
-      - 'docs/index.html'
-      - 'docs/og-image.png'
-      - 'docs/muhurta-scorer.js'
-      - 'docs/sitemap.xml'
-      - 'docs/robots.txt'
+      - 'index.html'
+      - 'src/**'
+      - 'public/**'
+      - 'package.json'
+      - 'package-lock.json'
+      - 'vite.config.ts'
+      - 'tsconfig.json'
   workflow_dispatch:

 concurrency:
   group: gh-pages-deploy
   cancel-in-progress: false

 permissions:
   contents: write

 jobs:
   deploy:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3

-      - name: Stage landing page
-        run: mkdir -p public && cp docs/index.html docs/og-image.png docs/muhurta-scorer.js docs/sitemap.xml docs/robots.txt public/
+      - name: Set up Node
+        uses: actions/setup-node@v4
+        with:
+          node-version: '20'
+          cache: 'npm'
+
+      - name: Install JS dependencies
+        run: npm ci
+
+      - name: Typecheck
+        run: npm run typecheck
+
+      - name: Test (Vitest, including scorer parity)
+        run: npm test
+
+      - name: Build site
+        run: npm run build
+
+      # The landing deploy uses keep_files: false to prune historical
+      # hashed bundles (Verify point 7). But feeds/ + gochara.json +
+      # *-lagna.json are owned by other workflows and MUST survive this
+      # deploy. We explicitly rsync them back from the currently-live
+      # gh-pages branch into dist/ before publishing.
+      - name: Preserve currently-live feeds + gochara.json + lagna JSONs
+        run: |
+          git fetch origin gh-pages --depth=1
+          mkdir -p dist/feeds
+          git --work-tree=. checkout origin/gh-pages -- feeds/ gochara.json 2>/dev/null || true
+          if [ -d feeds ]; then cp -r feeds/* dist/feeds/ 2>/dev/null || true; fi
+          if [ -f gochara.json ]; then cp gochara.json dist/gochara.json; fi
+          # *-lagna.json files live in feeds/, picked up by the cp above.

       - name: Deploy to GitHub Pages
         uses: peaceiris/actions-gh-pages@84c30a85c19949d7eee79c4ff27748b70285e453 # v4
         with:
           github_token: ${{ secrets.GITHUB_TOKEN }}
-          publish_dir: ./public
+          publish_dir: ./dist
           publish_branch: gh-pages
           cname: panchangam.astrochaganti.com
-          keep_files: true
+          keep_files: false
```

**Why `keep_files: false` is safe here despite Verify point 7's mitigation list:** the "Preserve currently-live feeds" step explicitly checks out feeds and `gochara.json` from gh-pages into `dist/` before deploy. This is more defensible than `keep_files: true` because it makes the dependency explicit and version-controlled. The CNAME pin is unchanged. `panchangam.astrochaganti.com` keeps resolving.

**Alternative if the rsync-back is judged too clever:** keep `keep_files: true` but add a `cleanup-stale-assets` step using `gh-pages` history. Recommendation: ship the explicit rsync-back first; it's auditable.

### 6.2 `.github/workflows/generate.yml`

```diff
 name: Generate Panchangam Feeds

 on:
   schedule:
     - cron: '0 2 1 * *'
   workflow_dispatch:

 concurrency:
   group: gh-pages-deploy
   cancel-in-progress: false

 permissions:
   contents: write

 jobs:
   generate:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3

       - name: Set up Python
         uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6
         with:
           python-version: '3.11'

       - name: Install dependencies
         run: pip install -r requirements.txt

       - name: Run tests
         run: python -m pytest tests/ -v

       - name: Generate feeds
         run: python -m telugu_panchangam.generate

-      - name: Rebuild landing page
-        run: python scripts/build_landing_page.py
+      # Landing page is NOT rebuilt here — deploy-landing.yml owns it.
+      # We only publish the freshly-generated feeds/, with keep_files: true
+      # so the landing bundle (assets/main-<hash>.js etc) on gh-pages survives.
+      - name: Stage feeds for publish
+        run: |
+          mkdir -p publish/feeds
+          cp -r feeds/*.ics publish/feeds/

       - name: Deploy to GitHub Pages
         uses: peaceiris/actions-gh-pages@84c30a85c19949d7eee79c4ff27748b70285e453 # v4
         with:
           github_token: ${{ secrets.GITHUB_TOKEN }}
-          publish_dir: ./public
+          publish_dir: ./publish
           publish_branch: gh-pages
           cname: panchangam.astrochaganti.com
+          keep_files: true   # Preserve landing bundle + gochara.json + *-lagna.json
```

`gochara.yml` and `lagna.yml` keep `keep_files: true` and need only the `publish_dir` rename matching the new convention; otherwise unchanged. CNAME lines preserved.

### 6.3 `scripts/build_landing_page.py`

**Deleted.** Vite's `npm run build` replaces it. `generate.yml` no longer invokes it (see diff above). One PR (PR 5 — see §7) handles the deletion together with `tests/test_deploy_drift.py` rewrite.

### 6.4 `tests/test_deploy_drift.py` (rewritten in PR 5)

The current test parametrises over `<script src="*.js">` references in `docs/index.html`. After Vite, there is one root `index.html` with `<script type="module" src="/src/main.ts"></script>`. Vite injects hashed `assets/*.js` at build, not in source.

**Replace the parametrised sidecar tests:**

```python
# Replace lines 26-30:
REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / 'index.html'
DEPLOY_WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'deploy-landing.yml'
VITE_CONFIG = REPO_ROOT / 'vite.config.ts'
PUBLIC_DIR = REPO_ROOT / 'public'

# Replace SEO_STATIC_ASSETS path — now in public/, not docs/.
@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_exists_in_public(asset: str):
    assert (PUBLIC_DIR / asset).is_file()

# NEW: Vite build artifact sanity. Runs `npm run build` (or skips if Node
# unavailable in dev) and asserts dist/index.html exists, dist/assets/
# contains at least one .js, and CNAME is in dist/.
def test_vite_build_produces_expected_artifacts():
    if not (REPO_ROOT / 'node_modules' / '.bin' / 'vite').exists():
        pytest.skip('node_modules not installed; run `npm ci` first.')
    subprocess.check_call(['npm', 'run', 'build'], cwd=REPO_ROOT)
    dist = REPO_ROOT / 'dist'
    assert (dist / 'index.html').is_file()
    assert (dist / 'CNAME').is_file()
    assert any((dist / 'assets').glob('*.js'))
```

**The CNAME pin tests at `tests/test_deploy_drift.py:154-175` are unchanged** — all four workflows keep their `cname: panchangam.astrochaganti.com` lines.

### 6.5 `tests/test_browser_smoke.py`

Playwright fixture changes the served directory from `docs/` to `dist/` and the fixture must `npm run build` first if `dist/` is empty. Tests that check `typeof window.findMuhurta === 'function'` (line 160) and `typeof window.muLagnaPosition === 'function'` (line 124) are **deleted** — those globals are intentionally gone after the Vite migration. They are replaced by:

- A `data-testid="mu-find-button"` selector + Playwright `.click()` that drives the search through the real button event listener.
- An assertion that the rendered `#mu-result` HTML contains at least one `.mu-tier-*` chip and does NOT contain the catch-all "Could not load the feed" string.
- A separate test that asserts no `pageerror` events fired on initial load.

This preserves the v1.8.0-regression net (Verify point 5) without depending on `window.*` globals.

## 7. PR breakdown — 6 PRs (PRs 6–8 are optional follow-ups)

Each PR is on a feature branch off master, merges to master only when tests pass and (where the UI is touched) screenshots are signed off. `master` stays releasable at every merge.

### PR 1 — Move tracking docs out of `docs/`; doc-sweep

- **Scope:** `git mv docs/tracking → tracking/`, `docs/plans → plans/`, `docs/specs → specs/`, `docs/superpowers → superpowers/`, `docs/NOW.md → NOW.md`, `docs/GUIDELINES.md → GUIDELINES.md`. Update `ARCHITECTURE.md:139,175` and `MAINTENANCE_RUNBOOK.md:124` to mention the upcoming Vite migration. Sweep `glama.json`, `README_PYPI.md`, `.jules/sentinel.md` for `docs/index.html` mentions.
- **Risk:** None to subscribers — these files are not deployed.
- **Review burden:** Low. Mostly file moves + path updates.
- **Dependencies:** None.
- **Verification:** `python -m pytest tests/` green. `git grep -n 'docs/tracking\\|docs/plans\\|docs/specs\\|docs/superpowers\\|docs/NOW.md\\|docs/GUIDELINES.md'` returns empty.
- **Devotee-visible value:** None directly; preserves the user's living-state workflow before the cutover.

### PR 2 — Add Vite scaffold + parity codegen + scorer TS modules; DO NOT touch deploy yet

- **Scope:** Add `package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `tools/export_activity_rules.py`, `tools/export_parity_fixture.py`. Create `src/scorer/` (all files), `src/data/` (hand-typed + generated JSON), `src/scorer/__tests__/*.test.ts` including `parity.test.ts`. Add `tests/test_activity_rules_export.py`, `tests/test_parity_fixture_export.py`, `tests/test_yoga_name_parity.py`. **Do NOT modify any workflow yet; do NOT modify `docs/`.**
- **Risk:** Low. `docs/index.html` is untouched; the deployed site is unchanged.
- **Review burden:** Medium. ~1,500 lines of new TS reviewed against the legacy code. The parity fixture is the load-bearing test artefact — review focuses on whether the fixture covers the dosha cascade, lagna verdict bands, and tier transitions.
- **Dependencies:** PR 1.
- **Verification:** `npm test` green. `python -m pytest tests/ -v` green. `python tools/export_activity_rules.py --check && python tools/export_parity_fixture.py --check` exits 0.
- **Devotee-visible value:** None directly — but this is the safety net for every subsequent PR.

### PR 3 — Hoist help-source templates + selection-store + parse-description module; landing page still served from `docs/`

- **Scope:** In `docs/index.html`: hoist `#go-help` (line 1376) and `#tb-help` (line 1226) into top-level hidden source divs next to the existing `#today-help-src` (line 1089). Update `openHelpSheet()` (line 2849) to read from the hoisted sources only. Add `localStorage`-backed selection state for `tp-city`/`tp-system`/`tp-date`/`fmt-toggle` so the existing `mobileShell()` IIFE's surgical DOM move doesn't lose selected values across resize. (Tiny preparatory change to the legacy file so the next PR's conditional-render approach has a place to read state from.) Also: in `src/lib/parse-description.ts`, port the regex state machine from `docs/index.html:1994-2099` and add a golden-snapshot test using existing ICS fixtures (`tests/fixtures/`).
- **Risk:** Medium. Touches `docs/index.html` — the legacy production file. The hoist must not change `openHelpSheet()` behaviour; the selection-store must not change which feed gets loaded.
- **Review burden:** Medium. The diff to `docs/index.html` is small; parse-description test fixtures need owner review.
- **Dependencies:** PR 2 (uses parity-fixture and `src/scorer/`).
- **Verification:** Existing `tests/test_browser_smoke.py` still green. Screenshots before/after on mobile + desktop for the help sheet open/close and for resize between 619px ↔ 621px.
- **Devotee-visible value:** Help sheet content stops occasionally showing stale text after switching tabs on mobile (real bug: source nodes were inside the panels and could be in any state). Selected city/system survives mobile drawer open/close more reliably.

### PR 4 — Vite build runs in CI shipping equivalent bytes; deploy still uses `docs/`

- **Scope:** Add `index.html` at repo root (Vite entry) with the static skeleton, `<template>` elements hoisted from PR 3, mount points for the components. Add `src/main.ts` that imports `docs/index.html`'s entire inline `<script>` body as a single legacy module (`src/legacy.ts` — temporary). The site at `panchangam.astrochaganti.com` is still served from `docs/index.html` via the unchanged `deploy-landing.yml`. **No deploy changes.** CI builds the Vite bundle in a separate job (`ci.yml` gains a `vite-build` job) and runs Vitest parity tests. The two files (`docs/index.html` and `dist/index.html`) coexist briefly. Update `tests/test_browser_smoke.py` to take a `--target` flag and run against both `docs/` (legacy, must pass) and `dist/` (new, must also pass).
- **Risk:** Medium. No deploy change, so no subscriber impact. The risk is that `src/legacy.ts` doesn't quite work in Vite because of `onclick=` global expectations — that's the point of the smoke test running against `dist/`.
- **Review burden:** Low–Medium. The new files are mostly mechanical; the load-bearing review is whether the browser smoke test passes against both targets.
- **Dependencies:** PR 3.
- **Verification:** CI green on both `docs/` smoke and `dist/` smoke. Exact pixel snapshots (Playwright `page.screenshot()`) match between `docs/` and `dist/` at 380px / 760px / 1280px viewport widths.
- **Devotee-visible value:** None yet. This is the dual-shipping gate.

### PR 5 — Cut over the deploy to Vite `dist/`; smoke test gates the deploy

- **Scope:** Apply the `.github/workflows/deploy-landing.yml`, `generate.yml`, `gochara.yml`, `lagna.yml` diffs from §6. Delete `scripts/build_landing_page.py`. Rewrite `tests/test_deploy_drift.py` to the new structure (§6.4). Rewrite `tests/test_browser_smoke.py` to drop `window.*` global assertions (§6.5). Move `docs/og-image.png`, `docs/sitemap.xml`, `docs/robots.txt` to `public/`. Add `public/CNAME` as belt-and-braces. **`docs/index.html` and `docs/muhurta-scorer.js` stay in the tree** (not deleted) — they're no longer referenced by any workflow but their continued existence is a one-PR-revert safety net if production breaks.
- **Risk:** HIGHEST. If `dist/` is missing anything or the rsync-back of feeds fails, subscribers' webcal:// URLs could break, the landing page could 404, or the JS could throw `ReferenceError`.
- **Mitigation:** PR-time checklist: (a) `gh workflow run deploy-landing.yml --ref <branch>` against a throwaway fork's gh-pages first, verify CNAME and assets land; (b) verify `tests/test_browser_smoke.py` against the throwaway URL; (c) verify subscriber feeds at `panchangam.astrochaganti.com/feeds/hyderabad-drik.ics` return 200 during the rsync-back step.
- **Review burden:** HIGH. Owner sign-off required. Screenshots at all three viewport widths required.
- **Dependencies:** PR 4 (CI must be green on `dist/` smoke for at least 7 days before merge).
- **Verification:** Pre-merge: dry-run on a fork's gh-pages. Post-merge: subscribe a fresh device to one ICS feed and confirm next-event arrives; load `panchangam.astrochaganti.com` and verify no console errors, all three tabs render, muhurta search returns slots.
- **Devotee-visible value:** Faster page load — Vite's hashed chunks + tree-shaking should shrink the initial JS payload from ~120 KB (the legacy inline script) to roughly 50–70 KB gzipped for the Today tab, with the rest lazy-loaded on tab switch. Print stylesheet (a small win shipped in this PR) makes the Today panel print cleanly.

**Phase 3 may be declared CLOSED after PR 5 merges and stays stable for 30 days.** PRs 6–8 below are quality-of-life follow-ups that do not gate Phase 5 (PWA).

### PR 6 — Per-component refactor (low-risk presentational): HeroBrand, SelectorRow, ToolTabs, SubscribeCard, SystemCard, McpCard, SiteFooter, SpecialDaysCard

- **Scope:** Extract the low-risk components from `src/legacy.ts` into proper `src/components/*` folders with their own CSS and `mount()` methods. Replace `onclick="toggleReadMore(...)"` (legacy lines 1375, 1498, 1507, 1524, 1540, 1566) with `addEventListener` wiring. `src/legacy.ts` shrinks but is still the home of Today/Tarabalam/Muhurta/Gochara render logic.
- **Risk:** Low. These are presentational components with minimal state; the SelectorRow change is the most involved because it wires to `selection-store`.
- **Review burden:** Medium. Per-component CSS extraction is mechanical; reviewer checks for unintentional specificity changes.
- **Dependencies:** PR 5.
- **Verification:** Pixel-snapshot screenshots match at 380px / 760px / 1280px on Today / Tarabalam (untouched panels — should be byte-identical). `npm test` green.
- **Devotee-visible value:** Subscribe card gets a copy-success toast. MCP card's `claude_desktop_config.json` snippet gets a syntax-highlighted block.

### PR 7 — Per-component refactor: TodayPanel + MobileShell with conditional rendering

- **Scope:** Extract `renderPreview` (legacy 2122-2292) + `parseDescription` (already done in PR 3) + Today's share button + hora/lagna/eclipse helpers into `src/components/TodayPanel/`. Rewrite `mobileShell()` (legacy 4205-4337) into `src/components/MobileShell/index.ts` using conditional rendering (no surgical DOM relocation). The six `MORE.moveIds` cards are now conditionally rendered in either the desktop tree or the MoreDrawer based on `selection-store.isMobile`. State survives via `selection-store` (form values persisted to localStorage on every change, restored on mount). Inline `onclick="switchTool(...)"` (legacy 1185-1190), `onclick="setTimeFmt(...)"` (legacy 1209) replaced by listeners.
- **Risk:** Medium-high. MobileShell is the most subtle piece. Mobile users are the majority of devotee traffic.
- **Review burden:** High. Screenshots required at 380px (mobile), at the breakpoint (619px / 621px), and at 760px (desktop). Test the drawer open/close 10 times in sequence.
- **Dependencies:** PR 6.
- **Verification:** Manual: switch between Today / Gochara / Tarabalam 30 times on a real phone, no orphaned drawers, no double-mount. Automated: Playwright test asserting that resize from 1280→380→1280 leaves identical DOM structure to baseline.
- **Devotee-visible value:** Drawer animation is smoother (CSS-only conditional render vs JS DOM thrashing). Today panel's flag strip gains a tap-to-explain on mobile.

### PR 8 (optional) — Per-component refactor: TarabalamPanel + MuhurtaSearch + GocharaPanel; delete `docs/` and `src/legacy.ts`

- **Scope:** Extract the remaining three panels. `src/legacy.ts` is deleted at the end. `docs/index.html` and `docs/muhurta-scorer.js` are deleted (their one-PR-revert safety net from PR 5 is no longer needed once PR 5 has been stable for 30 days).
- **Risk:** Medium. Muhurta is the deepest entanglement (Verify point 1). The TS scorer parity test from PR 2 is the safety net.
- **Review burden:** High. Reviewer focuses on whether the parity test catches a regression in `findMuhurta` results between `src/legacy.ts` and `src/components/MuhurtaSearch/find.ts`.
- **Dependencies:** PR 7.
- **Verification:** Parity test (PR 2's fixture) green. Manual: run the muhurta search for `wedding` at Hyderabad/drik for next 30 days and verify slot list matches the pre-extraction output to the minute.
- **Devotee-visible value:** Loading-state spinner for muhurta search (currently the button just sits there for 2–3 seconds). Tarabalam date pickers gain keyboard navigation. Gochara chart gains a print stylesheet.

**Cut points:** Phase 3 can be declared complete after PR 5 (the Vite cutover). PRs 6–8 are quality-of-life refactors that don't gate PWA (Phase 5) — they layer onto PR 5's `dist/` just as easily.

## 8. Risk register

| PR | Risk to devotee-visible behaviour | Mitigation |
|---|---|---|
| PR 1 | None | n/a |
| PR 2 | None (no production change) | Parity tests are CI-gated. |
| PR 3 | Help sheet shows wrong tab's content after PR | Hoist test: open each panel's help sheet on mobile, screenshot before/after, owner sign-off. |
| PR 3 | Mobile selected city resets to default on resize | New `selection-store` + manual test: change city, resize browser, verify city persists. |
| PR 4 | None (dual-shipping; deploy still uses `docs/`) | Dual smoke test in CI. |
| PR 5 | `panchangam.astrochaganti.com` 404s after deploy | Pre-merge: fork dry-run with own gh-pages; verify CNAME, assets, feeds all land. Post-merge: same-session manual verification + revert PR pre-staged. |
| PR 5 | Subscriber `webcal://` URLs break | `feeds/*.ics` paths under `panchangam.astrochaganti.com/feeds/` MUST keep responding 200 throughout the deploy. The rsync-back step in `deploy-landing.yml` is the explicit guarantee. Post-merge: re-subscribe a test device, confirm next event lands. |
| PR 5 | `keep_files: true` accumulates stale assets | The cutover deploy uses `keep_files: false` with explicit feeds rsync-back; this prunes any historical `assets/main-*.js`. |
| PR 5 | `tests/test_deploy_drift.py` fails on the first merge | Replace it in the same PR. The CNAME pin test (lines 154-175) is preserved verbatim. |
| PR 5 | `tests/test_browser_smoke.py` fails because globals are gone | Rewrite it in the same PR to use `data-testid` selectors + DOM-rendered output assertions instead of `typeof window.findMuhurta`. |
| PR 6 | CSS specificity regression — collapsed `!important` rules un-collapse | Pixel snapshots at three viewport widths gate the merge. Owner reviews any non-zero diff. |
| PR 7 | MobileShell conditional render orphans nodes / re-fires `change` listeners | Tab-switching stress test + Playwright DOM-snapshot regression. selection-store is the explicit state-survival mechanism. |
| PR 7 | The legacy `body[data-mode="mobile"]` descendant selectors lose their ancestry when nodes move | Replace the global descendant selectors with component-scoped CSS classes (`.mobile-shell-active`) wired by `MobileShell.mount()`. |
| PR 8 | Muhurta scoring drifts vs Python | Parity fixture from PR 2 — any score/tier/dosha mismatch fails CI. |
| ALL | CNAME pin accidentally removed | `tests/test_deploy_drift.py:154-175` enforced across all 4 workflows; CI fails before merge. |
| ALL | PyPI version bump expectation | Phase 3 does NOT touch engines or MCP. `tools/export_activity_rules.py` is read-only export; explicit decision recorded in this plan that **no PyPI bump is needed unless an engine constant changes**. Confirm with owner before PR 2 merges. |

## 9. Open decisions

See `open_decisions` field (original draft). **Superseded by the refresh's "New open decisions" subsection below** — read that first.

---

## Refresh against current master — 2026-06-18

> This section supersedes the stale parts of §1, §2, §3, §4, §6, §7 above. The **strategy is unchanged** (vanilla TS, codegen `ACTIVITY_RULES`→JSON parity, landing deploy `keep_files:false` + feeds rsync-back, CNAME pin across all four workflows, `docs/index.html` removed only at the very end). What changed is the *surface*: the 1.9.0 round (commit `218d981`) roughly doubled the muhurta-scorer the TS port must mirror, and the page/workflows/tests have drifted ~14–18 lines and one Node-version generation since the plan was drafted. Verified against master at version **1.10.4** (`pyproject.toml`), **1032 tests collected** (plan baseline of 846 is ~186 stale). Produced via a 5-facet parallel audit workflow; every anchor below was re-derived with `grep -n` on master.

> **Terminology — read once.** Wherever this addendum says "the 1.9.0 round," it names the *release that introduced* these scorer features; **the parity target is always current `master` (1.10.4).** Nothing changed the scorer between 1.9.0 and 1.10.4 except a dead-code cleanup (#100 `c10fe65`, no behaviour change). 1.10.0–1.10.4 added Phase-9 transit tools + ayanamsa, all independent of the website scorer. So "1.9.0 scorer surface" and "1.10.4 scorer surface" denote the **same logic** — the TS port mirrors whatever is on master now.

### A. Corrected file totals and top-level anchors

| Plan claim | Current master | Note |
|---|---|---|
| `docs/index.html` 4,356 lines | **4,370 lines** | grew via #86/#97/#99 |
| `docs/muhurta-scorer.js` 182 lines | **182 lines** (still) | line count holds; **currency does NOT** — see §D |
| `muhurta.py` "scorer runs past 1079" | **1,194 lines total** | `_evaluate_slot` ends 1017; `day_slots` 1019–1194; no separate scorer "past 1079" |
| 846 tests / 1 skipped | **1032 collected** | baseline ~186 stale |

**Every §2 line-range below ~line 1000 has drifted +13 to +18 lines.** Re-anchor the §2 table to these (verified):

`<style>` 53–1014 · `</head>` 1015 · `#m-topbar` 1019 · `#m-bottomnav` 1036 · `#m-more-drawer` 1063 · `#m-help-sheet` 1085 · `#today-help-src` 1099 · `#panel-tarabalam` 1234 · `#mu-section` 1316 (still nested inside panel-tarabalam — Verify point 11 holds) · `#panel-gochara` 1384 · `#special-days-card` 1439 · `#subscribe` 1445 · `#card-system` 1503 · `#card-mcp` 1568 · `<script src=muhurta-scorer.js>` 1636 · inline `<script>` opens 1637 · `FEED_BASE_URL` 1638 · `CITY_GROUPS` 1640–1644 (still 22 cities × 3 groups) · `SYSTEMS` 1645 · `parseDescription` 2013 · `renderPreview` 2135 · `renderUpcoming` 2309 · `loadFeed` 2341 · `calcTarabalam` 2571 · `renderTarabalam` 2675 · `switchTool` 2881 · `loadGochara` 2914 · `renderGochara` 3030 · `muAssignTiers` 3343 · `muFactsAt` 3516 · `MU_ACTIVITY` 3573–3676 · `htmlEsc` 3680 · `findMuhurta` 3686 · `renderMuhurta` 4093 · `mobileShell` IIFE 4220–4351 · GoatCounter 4353 · analytics 4355–4370.

Eclipse cross-cut re-anchored: parse 2070–2092 · `eclipseChip` 2127 · `renderUpcoming` chip 2322–2324 · muhurta day-skip 3711/3723–3726.

PR 3 help-source hoist targets re-anchored: `#tb-help` 1239 (plan said 1226) · `#go-help` 1389 (plan said 1376) · `#today-help-src` 1099 (plan said 1089).

### B. Corrected Python anchors (§2 / §3 / §4)

- `ACTIVITY_RULES` is at **`telugu_panchangam/personal/muhurta.py:115`**, closed by `ACTIVITIES = tuple(...)` at **:291** — **30 activities, 17 distinct per-row keys** (plan said `107–225`, ~25 rows, 7 keys).
- `_evaluate_slot` **:794–1017** · `day_slots` **:1019–1194** · `assign_tiers` **:83–101** (the dosha→tier cap is at **:97–99**) · `_score_lagna` **:421–536** · `_anandadi_day_modifier` **:778–791** · `diagnose_day` **:658–746**.
- **`find_muhurta()` does not live in `muhurta.py`.** It is the MCP wrapper at `telugu_panchangam/mcp/server.py:239` → `tool_find_muhurta` at `telugu_panchangam/mcp/tools.py:968`, which calls `day_slots()` per day and re-tiers across the whole search via `assign_tiers` at `tools.py:1010`. **`tools/export_parity_fixture.py` must import `day_slots` and/or `tool_find_muhurta` explicitly** — the §4/§5 "runs find_muhurta()" sketch is wrong. Tier is a *batch* property (per-day in `day_slots`, whole-search ceiling/floor in `tool_find_muhurta`), so the fixture must pin which seam it captures or TS tiers will not reproduce.

### C. The 17 ACTIVITY_RULES keys (was 7) — `types.ts` ActivityRule must model all

`label`, `skip_on_yoga`, `prefer_choghadiya`, `avoid_karana`, `prefer_tithi_class`, `prefer_vara`, `prefer_lagna_class` (the original 7), **plus the 10 added in 1.9.0**: `skip_on_sankramana`, `skip_on_khar_maasa`, `skip_on_adhika`, `skip_on_pitru_paksha`, `skip_on_simha_stha_guru`, `penalty_on_simha_stha_shukra`, `skip_on_combust`, `prefer_nakshatra_mukha`, `skip_on_panchaka_nakshatra`, `prefer_bhadra_puchha`. The `ActivityKey` union is now **30 members**. `export_activity_rules.py` serializes whatever keys exist, so the codegen is automatic — the work is the TS reader + `evaluateSlot` honoring each key.

**The inline `MU_ACTIVITY` (24 keys) has DIVERGED from Python (30).** The 6 Python-only activities the website has never scored: `construction_roof`, `coronation`, `cremation`, `litigation`, `well_digging`, `wood_cutting`. This is a devotee-visible behaviour change the plan does not acknowledge — see New Open Decision 1.

### D. The TS scorer port (PR 2) is ~2–3× bigger than the plan assumed

**Stop treating `docs/muhurta-scorer.js` as the port source.** It is a pre-1.9.0 snapshot: it contains only rashi/lagna/chandra sets, `score_tier`/`relative_tier`, `computePersonalDosha` (5-branch) and `computeDayDosha` (4-branch). It has **none** of the 1.9.0 logic. The inline `findMuhurta()` (3686–4060) is also pre-1.9.0 and additionally its inline `day_dosha` cascade (3995–4011) is **missing the `amavasya` branch** Python has (`muhurta.py:1004`) — i.e. it is a duplicate that is already *wrong*. **The TS scorer must be mirrored from `telugu_panchangam/personal/muhurta.py`, not from the sidecar; delete the sidecar, do not port it.**

Surface to mirror: ~1,080 lines of `muhurta.py` (line 34 down) **plus ~544 lines of imported helpers** — `nitya_yoga.py` (63), `lagna_position.py` (112), `panchaka.py` (110), `lagna_hora.py` (127), `tithi_class.py` (70), parts of `special_yogas.py` (132). The plan's implicit ~182 (sidecar) + ~250 (inline loop) is replaced by roughly 2–3× that. **PR 2's "~1,500 lines of new TS" estimate should rise to ~2,500–3,500.**

**Updated `src/scorer/` module inventory** (additions to §3 in **bold**):

- `tiers.ts` — `scoreTier` (≥7/≥4/≥1) + `relativeTier` (bands 0.75/0.5/0.25) + `assignTiers`. **`assignTiers` must re-apply the Excellent→Good cap when `personal_dosha` OR `day_dosha` is set (muhurta.py:97-99).** These two functions are unchanged from the sidecar and the §3 port target is correct.
- `lagna.ts` — kendra {1,4,7,10}/trikona {1,5,9}/ashtama 8 + class sets (correct as far as they go). **Must add the dual-lens evaluation:** `_score_lagna` (muhurta.py:421–536) scores position-from-janma-**rashi** AND position-from-janma-**lagna** (Lagna Shuddhi), +1 each, emitting symmetric neutral audit lines. Needs a **`janma_lagnas` profile dimension** the sidecar's single `muLagnaPosition` does not have.
- `dosha.ts` — `computePersonalDosha` (5-branch: ashtama_chandra > chandra_avoid > ashtama_lagna > chandra_remedial > tara_dosha, muhurta.py:981–996) + `computeDayDosha` (rikta > amavasya > visha_dagdha > vyatipata_vaidhriti, muhurta.py:1002–1011). The sidecar's versions match Python; the *inline* copy is the broken one (no amavasya).
- `ephemeris.ts`, `special-yogas.ts`, `facts.ts`, `nitya.ts` — unchanged. `nitya_yoga.py` (63 lines) is still the source of truth, imported at muhurta.py:26–30; `NITYA_PARTIAL_DOSHA_WINDOW` is a `timedelta` dict (the minute-unit drift fix in §4 is still right).
- **`panchaka.ts` (NEW)** — mirrors `panchaka.py` (110 lines): mod-9 Panchaka Rahita dosha computed per-slot from the slot's rising lagna (muhurta.py:919–958), with the **Mrityu Panchaka hard cap −3** (936–937) and the **activity-matched non-Rahita penalty −2** (951–955). These are *score caps*, distinct from the dosha→tier cap.
- **`anandadi.ts` (NEW)** — the Anandadi day modifier +1/−1 (`_anandadi_day_modifier`, muhurta.py:778–791) using `ANANDADI_AUSPICIOUS`/`ANANDADI_INAUSPICIOUS` from `special_yogas.py:114–126`.
- **`hora.ts` (NEW)** — the hora→vaaram +1 bonus: when `prefer_vara` is set, a slot earns +1 if the planetary hora it starts in maps to a preferred weekday lord (muhurta.py:885–898, `lagna_hora.get_horas`).
- **`day-skips.ts` (NEW)** — the 10 day-level hard-skip gates in `day_slots` (muhurta.py:1082–1131): sankramana, khar-maasa, adhika, pitru-paksha, simha-stha-guru, combust-loop (Guru/Shukra Maudhya), panchaka-nakshatra, plus the existing eclipse/disha-shoola. Returns `[]` + a dropped-day reason for the day.
- **`evaluate-slot.ts` (EXPANDED)** — beyond the legacy per-slot loop body, must reproduce: Panchaka Rahita slot recompute, hora→vaaram +1, Nakshatra Mukha bonus (871–878), Bhadra Puchha bonus (867–870), Simha-Stha Shukra −2 (846–849), Anandadi ±1. The pure-slot body is muhurta.py:794–1017 (~224 lines), not the ~250-line guess.
- **`diagnose-day.ts` (CONDITIONAL)** — only if the UI surfaces dropped-day reasons (mirrors `diagnose_day`, 89 lines). Otherwise mark out of scope so PR 8 reviewers know. See New Open Decision 3.

**The slot's rising sign comes from a Swiss-Ephemeris Lahiri bisection in Python** (`lagna_hora.get_lagna_transitions`, lagna_hora.py:58–127). In TS it is supplied by the precomputed `lagna.json` (the sidecar's `muLagnaAtMin` reads `lagnaDayData`). **The parity fixture must pin the lagna transitions** so the TS side does not re-derive ascendants — `lagna.ts` is a reader of precomputed data, not an ephemeris port.

### E. Expanded parity fixture (§4 Artefact B)

The "4 representative activities (travel/wedding/vehicle/gruhapravesha) × 2 profile shapes" matrix under-samples the 1.9.0 surface. Keep those 4 as the score-stacking cases and **add coverage-driven cases**:

- `cremation` OR `construction_roof` — exercises `skip_on_panchaka_nakshatra`.
- `litigation` — exercises `prefer_bhadra_puchha`.
- `well_digging` or `coronation` — exercises `prefer_nakshatra_mukha`.
- at least one samskara (wedding/upanayana) on a **sankramana / khar-maasa / adhika / pitru-paksha / simha-stha-guru / combust** day, with expected output = **empty slots + dropped_days reason** (none of these is reachable by random dates).
- hand-picked dates/profiles forcing `day_dosha=amavasya` (muhurta.py:1004) and `personal_dosha=ashtama_lagna` (988) — neither is guaranteed by 5 random dates, and amavasya is the exact regression the inline JS already has.
- a **`janma_lagnas` profile dimension** to exercise the dual lagna / Lagna-Shuddhi audit trail.

Expected tuple must capture the new **score-cap interactions**: Mrityu Panchaka −3, non-Rahita Panchaka −2, Anandadi ±1, Nakshatra Mukha bonus, Bhadra Puchha bonus, Simha-Stha Shukra −2 — in addition to `(score, tier, personal_dosha, day_dosha, reasons[])`.

**Three known drifts → "three legacy drifts PLUS the 1.9.0 surface gap."** The legacy three still hold: yoga-name spellings (Priti/Shula/Variyana vs Preeti/Shoola/Variyan, docs/index.html:3416–3418 vs nitya_yoga.py — `test_yoga_name_parity.py` set-equality is the right fix); `MU_NITYA_PARTIAL_WINDOW_MIN` unit (values match numerically, drift is representation only); the inline personal-dosha cascade (now at 3995–4011, not ~4025–4026). The dominant *new* drifts: (a) 6 missing activities + 10 missing rule fields in MU_ACTIVITY; (b) all 1.9.0 day-skips absent from inline `findMuhurta`; (c) all 1.9.0 slot signals absent. Also reconcile the JS-internal inconsistency: `MU_YOGA_NAMES_27` spells "Shula" (3417) but `MU_NITYA_PARTIAL_WINDOW_MIN` keys "Shoola" (3361) — port to Python's "Shoola" or the window lookup key-misses in TS.

### F. Corrected §6 deploy diffs (re-pin to current workflow contents)

The §6 "before" states still apply cleanly (every `-`/context line exists verbatim: deploy-landing.yml push paths 7–11, Stage step 31–32, publish_dir 40, keep_files 43, cname 42; checkout pinned `@df4cb1c…#v6.0.3`, gh-pages `@84c30a8…#v4` in all four). **But the §6.1 `+` lines are wrong on two counts** and would *regress* the repo:

1. **Node version + action pin.** The plan adds `actions/setup-node@v4` / `node-version: '20'`. master pins by SHA at `actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e # v6.4.0` running **Node 24** (ci.yml:54,56 — its own comment notes "Node 20 hit EOL in April 2026"). **Change the `+` block to:**

   ```yaml
   - name: Set up Node
     uses: actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e # v6.4.0
     with:
       node-version: '24'
       cache: 'npm'        # only if package-lock.json is committed (PR 2); else drop it
   ```

2. **`generate.yml` has no `keep_files` line today** (it relies on the peaceiris default). The §6.2 diff adds `keep_files: true` as a brand-new line — correct, but call it out so a reviewer does not look for a pre-existing line to diff against. `gochara.yml:44` and `lagna.yml:44` already carry `keep_files: true` + cname (45) — they need only the `publish_dir` rename, as the plan says.

**§6.4 scope is incomplete.** `tests/test_deploy_drift.py` defines `BUILD_SCRIPT = REPO_ROOT/'scripts'/'build_landing_page.py'` at **line 29** and consumes it in **two functions** the plan does not mention: `test_sidecar_listed_in_build_landing_page_script` (lines 104–114) and `test_seo_asset_staged_in_build_landing_page_script` (lines 141–151). Replacing only lines 26–30 leaves a `NameError`. PR 5 must delete/rewrite both functions when `build_landing_page.py` is deleted. The CNAME pin test `test_deploy_workflow_pins_cname` (154–175) and `INDEX_HTML` constant (line 27) are accurate and stay.

**Give `ci.yml` (PR 4) the same exact-diff treatment** §6.1/§6.2 give the deploy workflows: slot the `vite-build` job in after the existing "Run JS scorer tests" step (ci.yml:58–72), reusing the v6.4.0 SHA / Node 24. The plan currently gives no ci.yml diff.

**Ordering note (PR 5 depends on PR 2–4):** §6's diffs reference `index.html` (root), `package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`, `src/` — **none exist on master yet**; PR 2/PR 3 create them. State this dependency explicitly.

**Stale untracked artifacts on disk:** `dist/main.js` (gitignored stub) and `public/` (feeds + gochara.json, gitignored) already exist. The §6.5 smoke fixture's "build if dist/ empty" check must `rm -rf dist` for a clean build rather than trusting a non-empty `dist/`.

### G. §2 / §6.5 window-globals framing is inaccurate

`docs/index.html` does **NOT** re-export `window.findMuhurta` or `window.muLagnaPosition`. Its only own window assignment is **`window.renderAll` (line 2365)** — which the plan never inventories and PR 7 must remove/replace. `findMuhurta` is a plain function reached via `onclick="findMuhurta()"` (1366). `window.muLagnaPosition` exists only because `docs/muhurta-scorer.js:180` does `Object.assign(root, api)`. So the `test_browser_smoke.py` assertions (`typeof window.findMuhurta` line 160; `muLagnaPosition`-family loop 124–128) pass *via the scorer module*, and **deleting the scorer's `window.assign` is what actually breaks them** — not anything in index.html.

The inline `onclick=` surface is also ~2× the plan's footnote. Full set to budget for PRs 6–8: `switchTool` 1219/1221/1223, `setTimeFmt` 1212/1213, `muToggleMobile` 1317, `findMuhurta` 1366, `toggleReadMore` 1238/1388/1511/1520/1537/1553/1579, plus **`tbResetProfiles` 1278, `tbAddRow` 1281, `calcTarabalam` 1308, `copyUrl` 1460, `showAppTab` 1465–1467, `tbRemoveRow` 2537, `tbExtendTo` 2710, `shareTodayOnWhatsApp` 2258, `shareTarabalamOnWhatsApp` 2689, `shareGocharaOnWhatsApp` 3189, `shareMuhurtaOnWhatsApp` 4115** (~20+ handlers).

### H. "Engines before Vite" gate — status

The gate is **effectively satisfied, but its precondition was misstated.** Phase 9 (transit modules: `maudhya_calendar.py`, `graha_yuddha.py`, `ingress.py`, `panchanga_shuddhi.py` + 5 MCP tools) shipped in 1.10.0–1.10.3 and is **genuinely independent** of the scorer — none import `ACTIVITY_RULES` or `find_muhurta` (only a docstring mention in `panchanga_shuddhi.py`). It does **not** block the TS port. Phase 6 (narrowed) and Phase 7 are shipped; the full EngineCore refactor stays parked per CLAUDE.md/ARCHITECTURE.md.

**However:** the real scorer-surface churn came from the **1.9.0 round (Phase-8 Group A/B/C material), not Phase 6** — and the website mirror was never re-synced. So the true precondition is now *"website scorer caught up to Python (or the gap consciously frozen) + codegen parity bridge in place"*, not merely "engines shipped". The Group-A `feat/*` branches are all `behind=204` and already merged via 1.9.0, so **master's scorer surface is quiescent — this is the moment to lock it with the parity test before TS porting begins.** No live branch is poised to mutate `muhurta.py`/`ACTIVITY_RULES`. The codegen bridge the plan assumes exists (`tools/export_activity_rules.py`, generated JSON, parity test) does **not** exist on master yet — building it must be the *first* step of PR 2, not an assumed artifact.

### I. Refreshed PR breakdown (still 5 required + 3 optional)

| PR | Title | Scope delta vs original §7 | Risk |
|---|---|---|---|
| **PR 1** | Move tracking docs out of `docs/`; doc-sweep | Essentially unchanged. Verify `ARCHITECTURE.md`/`MAINTENANCE_RUNBOOK.md` anchors before editing rather than trusting 139/175/124. No subscriber impact. | none |
| **PR 2** | Vite scaffold + **codegen parity bridge** + **full current-master (1.10.4) TS scorer port** | MUCH BIGGER. (1) Build the codegen bridge FIRST (`tools/export_activity_rules.py` → `src/data/activity-rules.generated.json` + CI parity test) — it does not exist on master and the hand-mirror is what caused the 24-vs-30 drift. (2) Mirror the TS scorer from `muhurta.py` + ~544 lines of helpers, **NOT** the pre-1.9.0 sidecar (delete it). (3) Add `panchaka.ts`, `anandadi.ts`, `hora.ts`, `day-skips.ts`; expand `evaluate-slot.ts`; dual-lens `lagna.ts`; `assignTiers` dosha cap. (4) `types.ts` ActivityRule = 17 keys, `ActivityKey` = 30. (5) Parity fixture imports `day_slots`/`tool_find_muhurta`, pins lagna transitions, covers panchaka-skip/nakshatra-mukha/bhadra-puchha/samskara-on-skip-day/amavasya/ashtama_lagna. ~2,500–3,500 new TS, not ~1,500. | medium |
| **PR 3** | Hoist help-source templates + selection-store + parse-description module | Same intent; re-anchor hoists to `#tb-help` 1239, `#go-help` 1389, `#today-help-src` 1099. `parseDescription` 2013–2112; eclipse cross-cut 2070–2092/2127/2322/3711–3726. Onclick rewiring surface ~2× the footnote (~20 handlers). | medium |
| **PR 4** | Vite build in CI shipping equivalent bytes; deploy still uses `docs/` | Add the missing `ci.yml` exact diff: slot a `vite-build` job after the existing "Run JS scorer tests" step (ci.yml:58–72), reusing `setup-node@…#v6.4.0` / Node 24. `rm -rf dist` so the stale `dist/main.js` stub can't mask a build failure. | medium |
| **PR 5** | Cut over deploy to Vite `dist/`; smoke test gates the deploy | §6.1 `+` block must pin `setup-node@48b55a0…#v6.4.0` / Node 24 (NOT `@v4`/Node 20 — EOL + unpinned). `generate.yml keep_files:true` is a NEW line. `test_deploy_drift.py` rewrite must also delete/rewrite `test_sidecar_listed_in_build_landing_page_script` (104–114) and `test_seo_asset_staged_in_build_landing_page_script` (141–151) which reference the deleted `BUILD_SCRIPT` (line 29). `test_browser_smoke.py` window assertions break when the sidecar's `window.assign` is removed; also remove index.html's own `window.renderAll` (2365). CNAME pin test 154–175 preserved verbatim. | **highest** |
| PR 6 | Per-component refactor (presentational) | Unchanged intent; re-anchor `toggleReadMore` onclicks. Optional; does not gate Phase 5. | low |
| PR 7 | TodayPanel + MobileShell (conditional rendering) | `renderPreview` 2135; `mobileShell` IIFE 4220–4351; also remove `window.renderAll` (2365); `switchTool` 1219/1221/1223; `setTimeFmt` 1212/1213. Optional. | medium |
| PR 8 (optional) | Tarabalam + MuhurtaSearch + Gochara; delete `docs/` + `src/legacy.ts` | `findMuhurta` 3686–4060; `renderMuhurta` 4093 — deepest entanglement. If UI surfaces dropped-day reasons, add `diagnose-day.ts` (muhurta.py:658–746); else mark out of scope. `docs/` deleted only at the very end. PR 2's parity fixture is the safety net. | medium |

### J. New open decisions (supersede §9)

1. **BIGGEST — website scorer parity timing.** The website scorer is pre-1.9.0: it lacks all Group-A day-skips and slot signals, scores only 24 of Python's 30 activities, and its inline `day_dosha` cascade is already missing the `amavasya` branch. Choose:
   - **(A) RECOMMENDED — bring the TS scorer to full parity with current master's scorer (1.10.4) as part of the migration.** Because PR 2 builds the codegen bridge and mirrors `muhurta.py` directly, picking up all 30 activities + the new signals is nearly free and permanently eliminates the hand-mirror drift. Cost: a bigger PR 2 and 6 new activities + new day signals become devotee-visible.
   - **(B) Port as-is** (freeze today's stale 24-activity surface into TS) — faster PR 2, but the TS scorer intentionally lags Python until a later Phase-8 Group-A pass, reintroducing exactly the rebuild the "engines first" gate was meant to prevent.
2. **Do the 6 Python-only activities** (`construction_roof`, `coronation`, `cremation`, `litigation`, `well_digging`, `wood_cutting`) and the new day-level signals appear in the public muhurta dropdown at cutover, or stay hidden? Devotee-visible either way; a divergence-guard test must encode whichever is chosen. (Coupled to Decision 1 — choosing (A) implies surfacing them unless explicitly filtered.)
3. **Does the TS UI surface dropped-day reasons** (the `diagnose_day` explainer, muhurta.py:658–746, 89 lines)? If yes, `diagnose-day.ts` joins PR 8; if no, mark it explicitly out of scope.
4. **Which scoring seam does the parity fixture capture** — `day_slots()` (per-day tiering, the unit `evaluateSlot` ports) or `tool_find_muhurta()` (whole-search re-tier + `slots[:12]` truncation + `dropped_days`)? They tier differently, so the fixture must declare the batch composition or TS tiers won't reproduce.
5. **Confirm the no-PyPI-bump decision still holds:** Phase 3 adds only read-only export scripts and does not touch engines/MCP, so no `mcp-server-panchangam` version bump is needed. (Per CLAUDE.md, engine/MCP changes bump the version; these scripts are neither.)

### K. Biggest risks (append to §8)

| PR | New/changed risk | Mitigation |
|---|---|---|
| PR 2 | TS scorer ports the **stale sidecar** instead of 1.9.0 `muhurta.py`, silently freezing the pre-1.9.0 scorer (incl. the known `amavasya`-missing `day_dosha` bug) into TypeScript | Mirror from `muhurta.py` + helpers; delete the sidecar; parity fixture must hit every 1.9.0 differentiator. |
| PR 2 | The codegen parity bridge the whole plan leans on **does not exist on master** — until it lands (first step of PR 2), "Python is stable" is not even observable | Land `export_activity_rules.py` + generated JSON + CI parity gate first. |
| PR 2 | Codegen surfaces 30 activities → dropdown gains 6 unseen activities (devotee-visible) | Conscious decision (Decision 1/2) + divergence-guard test. |
| PR 5 | §6.1 `+` block as written reintroduces **EOL Node 20 + unpinned `@v4`** | Pin `setup-node@…#v6.4.0` / Node 24 to match ci.yml. |
| PR 5 | `test_deploy_drift.py` `NameError` from orphaned `BUILD_SCRIPT` references (104–114, 141–151) | Delete/rewrite both functions, not just lines 26–30. |
| PR 5 | Stale untracked `dist/main.js` masks a real build failure | `rm -rf dist` before the smoke build. |
| ALL | Hand-mirror rot (the very cause of the 24-vs-30 drift) | Codegen bridge + CI parity gate is the first thing PR 2 lands; it makes "Python is stable" observable. |
