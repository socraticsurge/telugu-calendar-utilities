---
title: Product-wide UX audit
description: Evidence-backed baseline and remediation priorities for the one-shell Panchangam experience.
date: 2026-08-29
status: local pre-owner gate passed
tracking: Epic #205, baseline story #207
---

# Product-wide UX audit

## Decision

The product direction is sound: preserve the calm, almanac-like visual system and
make each journey answer one user question before exposing its evidence. This is
an information-hierarchy uplift, not a visual rebrand or a calculation-engine
rewrite.

The baseline is **11/20** on the repository's Impeccable health check. The score
is not a usability benchmark and does not represent observed users. It records a
source review, browser review, and synthetic expert cognitive walkthrough so the
team can compare the same release gates before and after remediation.

Owner testing is a separate gate. It starts only after every P0 and P1 item in
this record has a passing implementation and evidence entry in the
[UX release scorecard](../operations/ux-release-scorecard.md).

## Product and audience baseline

The audit uses the product contract in `PRODUCT.md` and `DESIGN.md`:

- Telugu devotees and diaspora users need a seconds-long daily glance and
  occasional deeper tasks such as finding a Muhurtam, reading Daily Horoscope,
  subscribing to a calendar, or checking a computation.
- The interface must feel sacred, precise, calm, and trustworthy.
- One responsive shell is the product. Mobile is not a second presentation.
- Times, city, calculation system, and next-day markers are primary information.
- WCAG AA is the target; this review does not certify conformance.

## Method and evidence boundary

The baseline combined four forms of evidence:

1. A source-level review of shell, panel, state, accessibility, and loading
   behavior.
2. Browser walkthroughs of the primary and supporting journeys at desktop,
   tablet, and phone-sized viewports.
3. A synthetic expert cognitive walkthrough using the canonical tasks below.
4. A comparison mock for the Daily Horoscope information hierarchy.

This was **not** an observed-user usability study. It did not include an
assistive-technology matrix, production performance telemetry, network
throttling, or independent validation of astrology claims. A screenshot can
show clipping, density, and hierarchy; it cannot prove accessibility or task
success by itself.

## Canonical tasks

The same tasks should be used for every release review:

1. **Daily glance:** identify today's Tithi and Rahu Kalam, and confirm the city
   and calculation system.
2. **Change context:** switch city and calculation system quickly; verify the
   final result belongs to the final selection.
3. **Return through a saved profile:** open the roster, inspect a complete
   profile, and continue to Daily Horoscope and Muhurtam without re-entering
   known facts.
4. **Understand today's horoscope:** find the first useful guidance, confirm it
   is Janma-Rashi based, and inspect the supporting transit evidence.
5. **Find a Muhurtam:** choose a profile, run a 14-day search, and explain why
   the first slot ranks above the next one.
6. **Find an observance:** locate the next upcoming festival and continue to its
   Panchangam date.
7. **Subscribe:** choose a feed, copy its URL, and find the Google Calendar
   instructions.
8. **Verify a computation:** open Documentation and locate a method, formula,
   process, and reference for a named computation.

## Baseline health

| Area | Score | Baseline evidence |
|---|---:|---|
| Accessibility | 2/4 | Strong landmarks, skip link, dialog semantics, and mostly usable target sizes; open P1s remain around closed-drawer focus, headings, state semantics, date focus, and contrast. |
| Performance | 2/4 | The application bundle is reasonable, but large feed and Lagna data are loaded eagerly and stale asynchronous results can overwrite current context. |
| Responsive behavior | 3/4 | The one-shell layout is coherent across widths; phone and tablet titles concatenate, and dense Horoscope content can collide with the chart. |
| Theming and visual system | 2/4 | The light, warm palette is coherent; several local hard-coded colors and legacy accents bypass the token contract. |
| Interface anti-patterns | 2/4 | Core tasks are discoverable, but Horoscope and Muhurtam front-load explanatory detail and saved-profile details end without a next action. |
| **Total** | **11/20** | Baseline for comparison only; not a release score or observed-user metric. |

## What is already healthy

- The one-shell navigation, restrained maroon/green/amber palette, typography,
  and whitespace preserve the product's calm voice.
- Panchangam keeps timing data and context prominent, and its settings are
  disclosed without creating a parallel mobile experience.
- Profiles use labelled forms, dialog semantics, an accessible natal-chart
  table, and request-sequence guards in the birth-data flow.
- Subscribe exposes feed choice, copy behavior, and platform instructions in
  one journey.
- Documentation is discoverable in the shared navigation and is served from the
  repository's maintained source rather than a separate content system.
- The desktop, tablet, and phone layouts are structurally consistent even where
  specific responsive defects remain.

## Findings and required remediation

### P0 — computation trust boundary

| Finding | Evidence | Required outcome | Tracking |
|---|---|---|---|
| Daily Horoscope describes a Moon-sign/Janma-Rashi method in its UI and computation registry while the runtime also applies the same favourable-house and vedha sets to Lagna and narrates the result as “from your lagna.” | `index.html`, `docs/reference/computations.json`, and `src/panels/gochara.ts` disagree. The existing provenance test checks the static promise but does not catch the runtime path. | Daily Horoscope must consume and explain Janma Rashi only. Lagna remains a saved profile and natal-chart fact and may be used by separately supported journeys. A future Lagna transit lens requires its own sourced method, computation identifiers, regression coverage, and explicit opt-in story. | #207, #211 |

This contradiction blocks owner testing because it affects how authority is
claimed, not merely how information is arranged. The remediation must stay in
the presentation/personalization layer and must not change the frozen engines.

### P1 — must resolve before owner testing

| Finding | User risk | Acceptance evidence | Tracking |
|---|---|---|---|
| An older asynchronous Panchangam response can render after a rapid city/system change. | A user can see the wrong context while the picker displays the final selection. | A deterministic rapid-switch test and browser walkthrough show that only the latest request can update the result. Loading and error states remain tied to that request. | #207, #209 |
| The closed mobile drawer remains keyboard-focusable off screen. | Keyboard users can move into invisible navigation. | Closed drawer is removed from the focus order; opening restores focusability and closing returns focus to its trigger. | #209 |
| Primary tools lack a semantic page heading, and several visual state controls do not expose their selected/expanded state. | Screen-reader structure and control state are ambiguous. | One semantic page heading per primary view; navigation, time-format, tab, and disclosure states expose the corresponding ARIA state. | #209 |
| The visually hidden date input has no visible focus treatment. | Keyboard users cannot see where focus moved. | The visible date control receives a clear `:focus-within` treatment at every audited width. | #209 |
| Muted labels and copied/success text use local colors below the AA target. | Small supporting text can be difficult to read. | Spot checks meet the applicable AA contrast ratio and use the maintained token vocabulary. | #209 |
| The saved-profile detail page confirms readiness but does not offer a direct onward action. | A returning user must infer that Daily Horoscope and Muhurtam can use the saved profile, then navigate and reselect it. | Complete profiles show direct, labelled actions that carry the selected profile into both journeys; partial profiles state what is missing without overstating readiness. | #236 |
| Daily Horoscope puts a long sequence of deterministic transit paragraphs before its visual evidence and can overlap the chart on mobile. | The first answer is hard to find and the evidence becomes visually unreliable. | Show a concise Janma-Rashi result first and disclose the detailed transit checks on demand. Preserve the full deterministic evidence and documentation link. No overlap or clipping at the release widths. | #211 |
| Muhurtam says “best first,” but tier caps can place a lower-score Excellent slot above a higher-score Good slot; every reason group is expanded. | The ranking looks inconsistent and the result list becomes several screens long. | Explain “tier first, score within tier” before the list and disclose each slot's reason groups on demand. Computed rank, tier, score, and cautions remain unchanged. | #211 |
| Phone/tablet page-title spans concatenate because a responsive override removes their column layout. | Tool identity and purpose read as one broken phrase. | Title and subtitle remain distinct at 390 and 768 widths without changing the desktop hierarchy. | #207, #209 |

### P2 — tracked improvements after the owner-test gate

- **Festivals activation (resolved in this pass):** the next upcoming
  observance now leads the year list and carries its date into Panchangam.
- **Loading cost:** defer or scope the approximately 1 MB feed and approximately
  192 KB Lagna payload where the active journey does not need them. Validate the
  effect with production-like network and performance measurements before
  claiming improvement.
- **Breakpoint ownership (resolved in this pass):** JavaScript and CSS now use
  the same compact-shell boundary through 959 px, with an explicit 853 px
  regression for the narrow-desktop failure zone.
- **Reduced motion:** extend the preference across every animated transition,
  not only the current core set.
- **Visual-system debt:** replace remaining hard-coded interface colors and
  legacy gradient/stripe accents when the owning surface is next changed.
- **Profile-option information scent:** the stable saved-profile option text
  still says “Rashi + Lagna.” The result boundary immediately below now states
  that Daily Horoscope is Janma-Rashi based; changing the option contract is
  deferred until its existing compatibility assertion can be migrated in its
  owning visual-system story.

These items should not be silently forgotten, but they need not expand the
current P0/P1 remediation unless a verification run shows that one blocks a
canonical task.

## Information-design rationale

The recommended changes are grounded in the task, not decoration:

- **Miller's Law and Hick's Law:** chunk the Horoscope and Muhurtam evidence and
  reveal details on demand so a user does not have to parse every branch before
  deciding what to do.
- **Von Restorff effect:** give the day's primary answer one clear visual
  position instead of making every paragraph and badge compete for emphasis.
- **Pirolli–Card information scent:** use explicit onward labels such as “View
  Daily Horoscope” and “Find Muhurtam,” carrying the selected profile so the
  destination fulfills the promise.
- **Gestalt grouping and layer-cake scanning:** keep context, answer, supporting
  evidence, and method reference as distinct layers that can be scanned in that
  order.

The comparison in screenshot 19 illustrates this hierarchy. It is a design
decision aid, not production acceptance evidence. It reduces the first-layer
vertical presentation from roughly 2,268 px to 744 px at the comparison
viewport, while retaining a path to the detailed checks.

## Screenshot register

The baseline evidence is under
`docs/screenshots/ux-audit-2026-08-29/`. Long-page captures show the complete
surface; they are not all viewport-height screenshots.

| ID | File | Evidence purpose |
|---:|---|---|
| 01 | `01-profile-detail-desktop.png` | Initial desktop profile surface and fixture state. |
| 02 | `02-panchangam-desktop.png` | Desktop daily-glance hierarchy. |
| 03 | `03-panchangam-settings-desktop.png` | Expanded city, system, and time-format settings. |
| 04 | `04-horoscope-desktop.png` | Whole-sky Daily Horoscope baseline. |
| 05 | `05-horoscope-profile-desktop.png` | Personalized Horoscope density and chart relationship. |
| 06 | `06-muhurtam-desktop.png` | Muhurtam entry form and profile selection. |
| 07 | `07-muhurtam-results-desktop.png` | Expanded result reasons and total page length. |
| 08 | `08-festivals-desktop.png` | Festival ordering and current dead-end behavior. |
| 09 | `09-subscribe-desktop.png` | Feed choice, copy action, and instructions. |
| 10 | `10-documentation-landing-desktop.png` | Documentation discovery and landing hierarchy. |
| 11 | `11-profile-view-desktop.png` | Saved-profile detail, natal facts, and missing onward actions. |
| 12 | `12-profile-view-mobile.png` | Saved-profile detail at phone width. |
| 13 | `13-panchangam-mobile.png` | Direct-hash navigation-state diagnostic. This capture alone is not treated as proof of a user-facing navigation defect. |
| 14 | `14-panchangam-mobile-navigation.png` | Panchangam reached through the actual mobile navigation journey. |
| 15 | `15-horoscope-profile-mobile.png` | Personalized Horoscope title collision, density, and content/chart collision. |
| 16 | `16-muhurtam-mobile.png` | Muhurtam entry at phone width. |
| 17 | `17-mobile-navigation-drawer.png` | Drawer presentation; focus-order behavior requires DOM/keyboard evidence, not this image alone. |
| 18 | `18-panchangam-tablet.png` | Tablet shell and title collision. |
| 19 | `19-horoscope-surface-options.png` | Baseline-versus-recommended hierarchy comparison; mock only. |
| 20 | `20-profile-detail-actions-mobile.png` | Ready profile with direct Daily Horoscope and Muhurtam actions. |
| 21 | `21-horoscope-profile-mobile-after.png` | Concise Janma-Rashi answer before the closed deterministic evidence disclosure. |
| 22 | `22-muhurtam-results-mobile-after.png` | Tier-first ranking explanation and closed per-slot evidence at the compact-shell width. |
| 23 | `23-muhurtam-results-midwidth-full-after.png` | Full Muhurtam journey at the audited 853 px failure width; fixed chrome in a long capture is not used for positional judgment. |
| 24 | `24-panchangam-responsive-after.png` | Corrected 853 px Panchangam shell with no sidebar squeeze or horizontal overflow. |
| 25 | `25-festivals-next-observance-after.png` | Next observance promoted above the year archive with a direct Panchangam action. |

## Re-audit record

Update this section only after the implementation is built and the scorecard is
complete. Do not replace the baseline findings; preserving before/after evidence
is the purpose of the record.

| Field | Result |
|---|---|
| Branch / commit | `codex/product-wide-ux-audit` / implementation `62feeda`; screenshots and evidence are stored with this record |
| P0 status | Verified: UI, runtime, share text, and regression coverage are Janma-Rashi-only for Daily Horoscope. |
| P1 status | Verified: stale-request protection, status semantics, drawer focus isolation, heading/control state, date focus, contrast, onward actions, decision-first disclosures, and responsive titles pass. |
| Automated checks | TypeScript pass; 180 Vitest checks pass; 1,368 Python/browser/computation checks pass; production site/docs build passes. |
| Browser console / responsive checks | 28 built-browser cases plus the in-app walkthrough pass. Exact 390, 768, 853, 1024, and 1440 widths have no page overflow; fresh deep links produce no console errors. |
| After screenshots | 20–25 inspected; screenshot 24 records the additional mid-width defect found and fixed during the re-audit. |
| Residual P2/P3 items | Loading-cost measurement, broader reduced-motion coverage, remaining visual-token debt, and the stable “Rashi + Lagna” option label remain tracked. |
| Ready for owner test | **Yes — local pre-owner gate passed.** Push, PR, merge, and deployment remain unapproved. |

## Tracking map

- **#205** — existing UX uplift epic; no duplicate epic is needed.
- **#207** — this baseline, canonical tasks, scorecard, and P0/P1 release rule.
- **#209** — navigation, settings, shell semantics, focus, and asynchronous
  context integrity.
- **#211** — Daily Horoscope trust/hierarchy and Muhurtam result explanation.
- **#236** — saved-profile roster/detail and onward journeys.
- **#213** — final release verification after the owning stories pass.

Project status is operational state and must be updated in GitHub as work moves;
this document is the durable evidence and decision record, not a substitute for
that workflow.
