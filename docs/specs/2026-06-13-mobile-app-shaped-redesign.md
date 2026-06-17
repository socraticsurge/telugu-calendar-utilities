# Mobile-app-shaped redesign

**Status:** planned — not started
**Owner:** Vinay (decisions), Claude (execution)
**Branch:** `feature/mobile-app-shape` (to be created from `feature/mobile-polish`)
**Created:** 2026-06-13

---

## Why this exists

The current site is a desktop-shaped page that has been *responsively shrunk* for
mobile. After several polish passes (subtitles, tap targets, Tarabalam day-cards,
specials-list stacking) it works, but it still asks a phone visitor to scroll
through a 6-card long-form page laid out for a 1280px canvas.

A devotee on a phone is not *browsing* — they're on an **errand**:

- *"What is today?"* — 5-second glance at the bus stop
- *"Can we travel Saturday?"* — sitting down, intentional, weekly
- *"Is Sade Sati on me?"* — quarterly, when someone asks

Three different attention patterns, one current UI for all of them. A mobile app
gives each errand its own surface. This redesign delivers that — without
touching the engine, the tests, or the desktop layout.

## Hard rules — do not violate

- **Desktop is unchanged.** Every change ships behind `@media (max-width: 620px)`
  or the equivalent JS branch (`matchMedia` check). Verify the existing desktop
  audit (system selection card collapsed, MCP card collapsed, three-tab segmented
  nav at equal widths) is byte-identical after each commit.
- **Engine is frozen-core.** `telugu_panchangam/` is not touched. All redesign
  work is in `docs/index.html` and any new asset files under `docs/`. CLAUDE.md
  rules still apply.
- **All 376+ tests must stay green.** This is a presentation-layer change.
- **No new dependencies.** Vanilla JS, vanilla CSS, no framework, no build step.
  The deploy pipeline (Pages → CNAME) must keep working as-is.
- **Custom domain `panchangam.astrochaganti.com`** continues to serve. Both
  workflow `cname:` pins stay.
- **GoatCounter analytics continue.** Existing event hooks (`tab-*`,
  `subscribe-copy`, `share-*`, `consult-click`, `pypi-click`) preserved. Any new
  surfaces emit their own events at the same grain.
- **The `?src=` attribution tags in WhatsApp shares** remain.
- **AstroChaganti consultation pathways** stay subtle and need-triggered, per the
  `feature-work-guardrails` rule. The Sade Sati banner link and the disclaimer
  link are preserved.

## The reframe (single mental model)

> **A mobile-app-shaped experience for devotees on phones, served from the same
> static page, sharing one engine with the desktop site.**

Two presentation layers over one data layer. "Responsive" stops scaling at
~620px on this content; below that, we render a different shape.

## What changes — at a glance

| Component / pattern | Desktop today | Mobile redesign |
|---|---|---|
| Navigation | Top tabs (segmented) | **Bottom tab bar** (fixed, thumb-reach) |
| Tab switching | Click tab | **Swipe left/right** + tap |
| Hero / marketing | Full hero card | **Hidden**; lives behind ☰ |
| Subscribe card | Full card mid-page | **Lives behind ☰** (Settings drawer) |
| MCP / system selection / footer | Cards | **Lives behind ☰** |
| Today's preview | Stacked sections | **Single screen**: date strip → 4 anga tiles → **live timeline** with **now-line** |
| Choghadiya + Rahu/Varjyam/Abhijit/Amrita | Separate tile grids | **One chronological timeline** (replaces 4 grids) |
| Special days card | Stacked list | **Compact pill row** at top of Today screen |
| Gochara intro + guide | Paragraph + collapsible | **Header info icon**; chart full-bleed |
| Gochara controls | Date + Viewing dropdown | Compact pill row above chart |
| Coming-up grahas | Inline `·` separated paragraph | **Chip list**, one per line |
| Tarabalam profiles | Form rows | **Avatar dock** at top; tap to edit |
| Tarabalam date range / mode | Form rows | Compact horizontal pills |
| Tarabalam results | Stacked day-cards (just shipped) | Same |
| Muhurtam slot finder | Always-visible section under Tarabalam | **"Find a time slot" expandable row** inline |
| Footer | Three centred lines | Lives in Settings drawer |

## Architectural decisions

### One HTML file, two layouts, switched by CSS + a `<body data-mode>` attribute

Set `data-mode="mobile"` on `<body>` when `matchMedia('(max-width: 620px)').matches`
(initial + on resize). All mobile-only markup lives in a `<template>` or is
conditionally rendered. All mobile-only CSS is scoped under `body[data-mode="mobile"]`.
Reason: keeps the deploy story trivially the same (one file, one fetch); no
framework; existing CSS continues working for desktop verbatim.

### Mobile shell

```
┌─────────────────────────────────────┐
│  ☰  AstroChaganti's Panchangam      │  ← thin top bar (40px); ☰ opens drawer
├─────────────────────────────────────┤
│                                     │
│         current screen content      │  ← swipe between screens
│                                     │
├─────────────────────────────────────┤
│  Today    Gochara    Tarabalam      │  ← bottom nav (56px); active state
└─────────────────────────────────────┘
```

- **Top bar** holds the brand wordmark + ☰ (settings drawer).
- **Settings drawer** slides from the right; holds: Subscribe (the URL builder
  and copy button), Calculation system selector, About / MCP / Source, Footer.
  Closes on tap outside or swipe-right.
- **Bottom nav** = three tabs, each carrying its question subtitle. Tap or
  swipe to switch.
- **Swipe** between screens via touch events (no library). Tap is the primary,
  swipe is the bonus.

### Live timeline component (Today screen)

The single most important new component. It replaces:
- Day Choghadiya grid (8 blocks)
- Night Choghadiya grid (8 blocks)
- Auspicious tiles (Brahma Muhurta / Abhijit / Amrita)
- Inauspicious tiles (Rahu / Gulika / Yamagandam / Varjyam / Durmuhurtham)

Visual: a vertical timeline from sunrise to next sunrise (or compressed
day-only with night collapsible), with:
- Coloured background segments for each Choghadiya block
- Overlaid coloured bars on the left for inauspicious windows (Rahu Kalam etc.)
- Overlaid coloured bars on the right for auspicious windows (Abhijit, Amrita)
- **A horizontal "now" line** crossing the timeline at the current local time,
  with a small chip labelling "now"
- Tap a segment → reveals a thin detail strip below it (block name, range,
  reason if auspicious/inauspicious)

This is *the* feature that turns the site from "a reference" into "a tool you
glance at." Cricbuzz's live ball-by-ball strip is the closest mental model.

### Settings drawer contents (full list)

In order, top to bottom:
1. **Subscribe to your calendar** — city + system selectors, the URL,
   Copy button, Apple/Google/Outlook quick links
2. **Calculation system** — Drik (default) / SS / Vakya, with a one-line
   explanation per choice
3. **Time format** — 12h / 24h toggle (currently in the shared selector row;
   it's a preference, not a context)
4. **About** — one paragraph: what this is, who runs it, the consultation
   pathway to astrochaganti.com (subtle, single link)
5. **For developers** — `mcp-server-panchangam` link + PyPI button
6. **Source** — GitHub link

The drawer is where the "long tail" lives. The visitor's daily surface is
free of it.

## Commit plan

Three commits, each independently shippable and reversible. Each must:
- preserve all 376+ tests green
- preserve desktop layout byte-identical (visual diff via screenshot pair)
- include a single screenshot for review before push
- emit GoatCounter events at the same grain as before

### Commit 1 — Shell

**Scope:** the frame; no screens redesigned yet.
- `data-mode="mobile"` attribute set on `<body>` based on `matchMedia('(max-width: 620px)')`
- Top bar markup + CSS (hidden on desktop)
- Bottom nav markup + CSS (hidden on desktop); shows the three tabs with their
  question subtitles
- Settings drawer markup + CSS + open/close JS
- Settings drawer populated with: Subscribe card moved in, system selector
  moved in, MCP card moved in, About + Source moved in
- The existing hero + Subscribe card + MCP card + system selection card +
  footer all **hidden in mobile mode**
- Existing top tab bar **hidden in mobile mode**
- The three tab `<div>` panels still render at full width; bottom nav drives
  which one is visible
- Swipe-between-tabs JS (touchstart/touchend; threshold 60px; respects
  vertical scrolling)
- GoatCounter event names: `tab-today` / `tab-gochara` / `tab-tarabalam`
  preserved; new `settings-open`, `settings-close` events

**Verification before commit:**
- iPhone 13 viewport (390×844): bottom nav reachable, top bar quiet, swipe works
- Desktop unchanged (visual diff)
- Subscribe + MCP still discoverable behind ☰
- All shares still work, attribution tags intact
- 376 tests green

**Acceptance:** devotee can land on the page on a phone, see exactly the Today
screen (no marketing), navigate between tabs by swipe or bottom-nav tap, and
find subscribe/about/system inside the drawer.

### Commit 2 — Today screen

**Scope:** redesign the Today screen as a single-glance surface.
- Date strip: weekday + date + festival badge (if any) + quality color background
- Sky strip (sunrise/sunset/moonrise/moonset) compressed to a one-line chip row
- Four anga tiles (Tithi / Nakshatra / Yoga / Karana) — the existing design
  in a 2×2 grid; this part already works
- **Live timeline component** replacing the choghadiya + auspicious + inauspicious
  + night choghadiya stacks (~50% of the current Today scroll length)
- Now-line: `<div>` absolutely positioned at the timeline percentage matching
  current local time; auto-updates every minute via `setInterval`
- Tap-to-expand block details in the timeline
- Specials row (Masa Shivaratri / Shani Pradosham chips) at the top of Today
- Special days "next 30 days" remains as a *compact* pill row near the bottom
  (not a full card)
- Existing tara-chip vocabulary preserved (green/amber/red, ° and ☾ marks)
- WhatsApp share remains in the upper-right of Today (existing behaviour)

**Verification before commit:**
- Now-line position correct across the day; updates every minute
- Tapping any window block reveals its detail line
- Same data; nothing the desktop event hooks expect has been removed
- 376 tests green

**Acceptance:** a devotee opening Today on their phone at 11:47 AM sees:
date, the current Choghadiya block highlighted, Rahu Kalam visible upcoming,
Abhijit Muhurta visible. They can decide whether to step out without reading.

### Commit 3 — Gochara and Tarabalam screens

**Scope:** the other two errands.

**Gochara screen:**
- Chart full-bleed (edge to edge minus a small gutter)
- Sade Sati banner above chart (when applicable) with consult link
- Date / Viewing controls compressed to a single pill row above chart
- Centre cell simplified to just the date in large type
- "Coming up" rendered as one-per-line graha chips below chart
- Rasi Phalalu card below
- Footnotes / disclaimers fold into the ☰ guide; one-line "not a horoscope"
  remains visible above the footer area

**Tarabalam screen:**
- Avatar dock at top: small circles for each saved person; tap → edit;
  tap "+" → add (up to 4)
- Date range + ✦ standard as a compact pill row beside dock
- Existing day-card results (already shipped)
- "Find a time slot" as a single tappable row that expands inline to reveal
  activity selector + slot list (no scrolling past Tarabalam to reach Muhurtam)
- Muhurtam slot rows: condensed by default on mobile; tap "why?" to expand
  reasons (the issue you raised about 129px rows)
- Legend stacks: each chip definition self-contained, chip-above-text, not
  chip-beside-text

**Verification:**
- All existing flows reach the same outcomes
- Profile editing in the dock writes the same localStorage as the form
- Day-card data unchanged; just hosted in a different shell
- Muhurtam scoring + reasons unchanged
- 376 tests green

**Acceptance:** a devotee setting up the family the first time can do so from
the avatar dock alone. Finding a time slot for travel is one expand away,
not a scroll past the day-card list. The Sade Sati alert is the most
prominent element on the Gochara screen when applicable.

## Components — full inventory

(Cross-referenced to the 27-component walkthrough; each entry says what happens.)

1. Hero → **drawer/About**, hidden on phones
2. Top tab bar → replaced by bottom nav
3. Selector row → split: City stays on Today/Gochara/Tarabalam contextually;
   System + Time format move to drawer
4. Today preview header → date strip with quality color
5. Specials chips → kept, moved to top of Today
6. Anga tiles → unchanged (2×2 grid)
7. Auspicious/Avoid strips → **merged into timeline**
8. Choghadiya grids → **merged into timeline + now-line**
9. Special days "next 30 days" → compact pill row, lower on Today screen
10. Subscribe card → drawer
11. System selection card → drawer
12. MCP card → drawer
13. Tarabalam profiles → **avatar dock**
14. Tarabalam controls → compact pill row
15. Summary banner → unchanged
16. Tarabalam day cards → unchanged (already shipped)
17. Legend → **chip-above-text glossary** entries
18. Muhurtam input → folds into "Find a time slot" expander
19. Muhurtam slot rows → condensed; "why?" expander for reasons
20. Gochara intro + guide → guide stays as info icon in top bar of screen;
    intro removed on mobile
21. Gochara controls → compact pill row
22. Sade Sati banner → top of Gochara screen, prominent
23. South Indian chart → full-bleed, centre simplified
24. Coming up → vertical chip stack
25. Rasi Phalalu → unchanged
26. Footer notes → mostly drawer; one-line "not a horoscope" remains
27. Footer → drawer

## Risks and mitigations

- **Risk:** swipe gestures intercept vertical scroll on chart / table.
  **Mitigation:** distance threshold + dominant-axis detection in swipe JS.
- **Risk:** drawer obscures content when partly open.
  **Mitigation:** drawer is full-height; overlay dims background; ESC + tap-out close.
- **Risk:** now-line drifts when device sleeps.
  **Mitigation:** `setInterval(updateNow, 60000)` + `visibilitychange` listener
  re-aligns on tab-resume.
- **Risk:** sharing a screenshot loses the "now" context.
  **Mitigation:** the share text format already includes the date; for the
  timeline, also include the current-time anchor in the share text.
- **Risk:** matchMedia firing at edge widths (619/620) flicker.
  **Mitigation:** debounce + only re-render shell, not data.
- **Risk:** GoatCounter event grain becomes wrong if internal nav changes.
  **Mitigation:** every nav surface re-emits the same event names.

## Out of scope (explicitly)

- **Native app** (iOS / Android). The site stays a web page; we're shaping it
  *like* a mobile app, not building a mobile app.
- **Push notifications.** Not added.
- **Auth or accounts.** No user system — localStorage only, same as today.
- **Server-side rendering.** Static site stays static.
- **Build pipeline.** No webpack/vite/etc. — vanilla HTML/CSS/JS.

## How to resume this work in a fresh session

If context is lost:
1. `git checkout feature/mobile-app-shape` (or create it from `feature/mobile-polish` first)
2. Read this file end to end
3. Check `git log feature/mobile-app-shape ^master` to see which of the three
   commits have landed
4. Resume at the next commit; don't merge piecemeal — commit each is a
   deployable unit but the trio is meant to ship together
5. Memory note `feature-work-guardrails.md` in user-memory should also reflect
   that mobile redesign is in flight

## Open questions before commit 1

1. **Bottom nav style:** material-style (filled active) or iOS-style (tint only
   on active)? Default: iOS-style — matches the site's existing quiet aesthetic.
2. **Drawer side:** right (matches ☰ in top-right) or left? Default: right.
3. **Swipe sensitivity:** how forgiving of mostly-vertical drags? Default: a
   60px horizontal threshold with 1.5× more horizontal than vertical motion.
4. **What stays on the desktop hero on phones, if anything?** Default: nothing
   — drawer holds About, Today is the landing screen.

These four are tunable in commit 1 and don't block the plan. Surface them when
the shell is in front of Vinay.
