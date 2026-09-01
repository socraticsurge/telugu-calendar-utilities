---
title: UX release scorecard
description: Reusable local gate for primary journeys, responsive behavior, accessibility signals, and product trust before owner testing.
---

# UX release scorecard

Use this scorecard for every meaningful user-experience change. It turns the
canonical product journeys into a repeatable local gate and keeps engineering
verification separate from owner acceptance.

Passing this scorecard means **ready for owner testing**. It does not authorize a
push, merge, deployment, or production change, and it does not claim observed
user validation or full WCAG conformance.

## Run record

| Field | Value |
|---|---|
| Date / time zone | 2026-08-29 / Asia/Kolkata |
| Reviewer | Codex synthetic product-design audit; independent read-only release review |
| Branch | `codex/product-wide-ux-audit` |
| Commit / working-tree reference | Implementation `62feeda`; screenshots and evidence are stored with this scorecard |
| Epic and stories | #205 / #207, #209, #211, #212, #213, #236 |
| Local application URL | `http://127.0.0.1:4176/` |
| Documentation URL | `http://127.0.0.1:4176/docs/` |
| Browser and version | Chromium 151.0.7922.34 automated; Codex in-app browser visual walkthrough |
| Operating system | macOS / Darwin |
| Profile fixtures | Complete: Hyderabad, New York, London / partial: Manual boundary test |
| City / system baseline | Hyderabad / Drik unless the story specifies otherwise |
| Console clear at start | Yes; optional Daily Horoscope lookup changed to a stable artifact so a normal deterministic fallback no longer emits a 404 |

## Release rule

The local gate passes only when all of the following are true:

- every P0 and P1 has an owner, implementation, regression check, and linked
  evidence;
- all canonical-task rows pass at the required viewport(s);
- automated tests, type checks, production build, and documentation output
  checks pass;
- no uncaught exception, unhandled rejection, failed required request, or new
  console error appears in the walkthrough;
- no text collision, horizontal page scroll, inaccessible closed-drawer focus,
  or stale context result appears at a release width;
- residual P2/P3 findings are recorded with a story or an explicit defer reason;
- the branch remains local until the owner has reviewed the screenshots and
  tested the flow.

Any P0 failure stops the run. A P1 failure means “not ready for owner test,” even
when the automated suite passes.

## Automated checks

Run from the repository root and paste the result, duration, and relevant log or
artifact path below each command.

```bash
npm run typecheck
npm test
npm run build
.venv/bin/python -m pytest tests/
```

`npm run build` includes the site build, documentation build, and documentation
output checks. The Python suite is the frozen computation contract and must pass
without changing existing assertions merely to accommodate presentation work.

| Check | Result | Duration | Evidence / notes |
|---|---|---:|---|
| `npm run typecheck` | Pass | 1.9 s | Both strict core and relaxed panel configurations compile. |
| `npm test` | Pass | 1.53 s | 14 files / 180 tests, including stale request, Janma-only, profile onward, festival-next, and latest-artifact regressions. |
| `npm run build` | Pass | 14.7 s | Site, 62 computation pages, 10 Mermaid diagrams, sitemap, and 94 landing/public artifacts verified. |
| `.venv/bin/python -m pytest tests/` | Pass | 112.23 s | 1,368 tests, including 28 built-browser cases and the frozen computation contract. |

## Viewport matrix

Capture the named journey at the exact CSS viewport. A full-page screenshot may
be added, but also inspect the initial viewport because a long capture can hide
above-the-fold hierarchy and sticky-layout defects.

| Viewport | Required focus | Result | Screenshot(s) | Notes |
|---|---|---|---|---|
| 390 × 844 | Phone title hierarchy, drawer, focus visibility, profile onward actions, Horoscope disclosure, Muhurtam entry/results, no horizontal scroll | Pass | 20, 21; automated browser matrix | Direct actions, closed evidence, 44 px controls, and drawer isolation verified. |
| 768 × 1024 | Tablet title hierarchy, context controls, content width, result disclosures | Pass | Automated browser matrix | Compact shell remains active and page title stays stacked. |
| 853 × 900 | Narrow-desktop failure zone | Pass | 22, 23, 24, 25; automated browser matrix | Audit found the sidebar squeeze here; unified 959/960 breakpoints remove it with zero page overflow. |
| 1024 × 768 | Compact desktop sidebar, settings, daily glance, result hierarchy | Pass | Automated browser matrix | Full sidebar and centered canvas remain usable. |
| 1440 × 900 | Full desktop rhythm, line length, primary/secondary action hierarchy, long-result scan | Pass | Baseline 01–11 plus automated browser matrix | Automated exact-width reflow and interaction pass; in-app visual inspection used its available compact width. |

## Canonical task walkthrough

For each task, start from the listed entry state without relying on memory of the
implementation. Record what the interface makes obvious, not what the reviewer
knows from the code.

Scoring fields:

- **Complete:** yes/no, with the expected result visible.
- **First-action clarity:** 0 = no credible action; 1 = guessed; 2 = discoverable
  after scanning; 3 = immediately clear.
- **Steps:** user actions after the entry state; do not count passive reading.
- **Backtracks:** route reversals or reopened surfaces caused by uncertainty.
- **Errors/recovery:** what failed and whether the interface explained recovery.
- **Context continuity:** whether city, system, date, time format, and selected
  profile remained correct where the next surface needed them.

| ID | Task and entry state | Expected result | Required widths | Complete | First action (0–3) | Steps | Backtracks | Errors / recovery | Context continuity | Evidence |
|---:|---|---|---|---|---:|---:|---:|---|---|---|
| T1 | **Daily glance.** Open Panchangam on the baseline context. | Today's Tithi and Rahu Kalam are findable without expanding help; Hyderabad, Drik, local date, and time format are explicit. | 390, 1024, 1440 | Yes | 3 | 0 | 0 | None | City, system, date, and 12h format visible | 02, 13, 18, 24; browser matrix |
| T2 | **Change context.** Rapidly change city and system more than once. | Loading belongs to the active choice and only the final request renders. The result context matches the visible final city/system. | 390, 1024 | Yes | 3 | 4 | 0 | Active error is announced; retry is a new selection/load | Request key and sequence reject stale feed and Lagna responses | `today-request-order.test.ts`; browser matrix |
| T3 | **Return through a profile.** Open the roster, view a complete profile, then continue once to Daily Horoscope and once to Muhurtam. Repeat the detail check with a partial profile. | The complete profile is selected automatically in each destination. The partial profile states missing inputs and does not claim unsupported readiness. No known fact is re-entered. | 390, 1440 | Yes | 3 | 6 | 0 | Partial profile names the missing Padam | New York remains selected in both destinations | 20; profile panel and browser regressions |
| T4 | **Understand today's horoscope.** Enter Daily Horoscope with a complete profile. | A concise result appears before detailed checks; the method and all user-facing verdicts are explicitly Janma-Rashi based. Detailed deterministic checks and the documentation path remain available on demand. No Lagna verdict, “from your lagna” narrative, or Lagna-derived share text is present. | 390, 768, 1440 | Yes | 3 | 1 | 0 | Deterministic fallback remains useful if interpretation is unavailable | Saved profile and Janma Rashi remain explicit | 15 vs 21; runtime and provenance regressions |
| T5 | **Find a Muhurtam.** Choose a profile and run a 14-day search. | The first slot is easy to identify; the UI states “tier first, score within tier” before the list. Opening reasons explains the tier, score, and cautions without changing their computed values. | 390, 1024, 1440 | Yes | 3 | 2 | 0 | Empty/feed error states give a recovery direction | Selected profiles remain visible above results | 07 vs 22/23; browser regression |
| T6 | **Find an observance.** Open Festivals and locate the next upcoming event. | The next upcoming date is distinguishable from past dates. If date-to-Panchangam is deferred, record that limitation and its owning P2 story. | 390, 1440 | Yes | 3 | 1 | 0 | No future event keeps the maintained year archive | Next date transfers directly into Panchangam | 08 vs 25; festival-next unit/browser checks |
| T7 | **Subscribe.** Choose a feed, copy its URL, and locate Google Calendar instructions. | Selection and copied/success state are explicit; instructions are reachable without leaving the journey. | 390, 1024 | Yes | 3 | 2 | 0 | Clipboard failure receives an explicit failure state | City/system and selected feed remain in the URL | 09; copy/status browser checks |
| T8 | **Verify a computation.** Open Documentation and find a named computation. | The page exposes inputs, outputs, process/formula, implementation boundary, regression evidence, and references—or clearly marks an evidence gap. | 390, 1440 | Yes | 3 | 2 | 0 | Evidence gaps are marked instead of invented | Computation route remains stable | 10; docs source/output checks |

## Product-trust checks

| Check | Pass condition | Result | Evidence / notes |
|---|---|---|---|
| Daily Horoscope contract | UI, runtime result, shared text, tests, and computation registry agree that the supported verdict is Janma-Rashi based. | Pass | Runtime test uses a Lagna-bearing profile and rejects Lagna marker, verdict prose, and share text. |
| Lagna boundary | Lagna remains available in saved natal facts/chart and supported Muhurtam contexts but is not silently reused as a Daily Horoscope verdict lens. | Pass | Profile detail retains Lagna; Daily Horoscope explanation explicitly states the boundary. |
| Context provenance | Every timing result states or inherits an unambiguous city, calculation system, local date, and time format. | Pass | Context line and stale-request tests. |
| Evidence depth | “Why,” method, or documentation disclosures preserve computed evidence after the first layer is simplified. | Pass | Eight transit checks and every Muhurtam reason group remain available in closed disclosures. |
| Frozen-core boundary | No engine, ICS, workflow, or existing computation-test assertion was changed for the UX work. | Pass | Diff-path check and independent review; 1,368 tests pass. |

## Accessibility and keyboard checks

These are release signals, not an accessibility certification. Record the browser,
input method, and any assistive technology actually used; do not infer a screen
reader result from DOM inspection.

| Check | Pass condition | Result | Evidence / notes |
|---|---|---|---|
| Landmarks and heading | Skip link reaches `<main>` and each primary tool has one useful semantic page heading. | Pass | Semantic `h1` plus labelled panels. |
| Mobile drawer | When closed, drawer controls cannot receive focus. On open, focus enters/traps within it; Escape and close restore focus to the trigger. | Pass | Exact keyboard/ARIA/inert browser assertions at 390, 768, and 853. |
| Keyboard order | All task controls are reachable in a meaningful sequence with no trap outside intentional modal focus management. | Pass | Profile and shell browser walkthroughs. |
| Visible focus | Links, buttons, selects, disclosures, tabs, and the date control show a visible focus indicator. | Pass | `:focus-visible` and date `:focus-within` verified. |
| Control state | Current navigation, time format, tabs, menus, and disclosures expose selected/current/expanded state programmatically. | Pass | ARIA state browser assertions. |
| Status and errors | Loading, success, copied, empty, and failure states are announced without stealing focus and include a recovery action where applicable. | Pass | Status/error regression plus request-order test. |
| Contrast spot check | Body, muted labels, success/copied text, guidance labels, focus indicators, and semantic chips meet the applicable WCAG AA ratio against their actual background. | Pass | Computed-style WCAG ratios in the built-browser suite. |
| Reduced motion | With `prefers-reduced-motion: reduce`, nonessential transitions/scroll animations are removed. | Deferred P2 | Drawer and core disclosures comply; complete transition inventory remains in #208/#213. |
| Zoom/reflow | At 200% zoom, canonical tasks remain usable without content overlap or loss. | Deferred P2 | Exact 390–1440 reflow and 853 failure-zone checks pass; a dedicated zoom/AT matrix remains in #213. |

## Responsive and visual checks

| Check | Pass condition | Result | Evidence / notes |
|---|---|---|---|
| One shell | The same information architecture adapts at all release widths; no desktop/mobile content fork appears. | Pass | Same sidebar becomes the compact drawer through 959 px. |
| Page title | Title and purpose remain separate and readable at every release width. | Pass | Screenshots 21, 24, 25 and automated bounding-box assertion. |
| Decision first | Daily Horoscope and Muhurtam show one primary answer before optional evidence. | Pass | Screenshots 21–23. |
| Layer integrity | Cards, disclosures, chart, tooltips, and sticky chrome do not overlap, clip, or cover controls. | Pass | In-app visual inspection plus exact-width browser checks. |
| Width and reflow | No page-level horizontal scroll; tables/charts use an intentional local scroll or responsive alternative if needed. | Pass | 390, 768, 853, 1024, and 1440 automated overflow diagnostics. |
| Times | Ranges, AM/PM or 24-hour format, and next-day markers remain legible and unambiguous. | Pass | Daily and Muhurtam screenshots; 12h/24h state coverage. |
| Light theme | The documentation and application remain in the maintained light theme with no dark-theme flash or toggle. | Pass | Local app/docs walkthrough and production build. |
| Brand restraint | Existing serif/sans pairing and maroon/green/amber semantics are preserved; no decorative element competes with a task result. | Pass | Before/after visual comparison. |

## Browser runtime checks

| Check | Result | Evidence / notes |
|---|---|---|
| Initial load has no uncaught error | Pass | Built-browser console capture. |
| Every canonical route opens without a failed required request | Pass | Eight fresh hash routes; optional interpretation uses stable `latest.json`. |
| Rapid city/system changes render only the final selection | Pass | Feed and Lagna sequence/key regressions. |
| Profile roster/detail survives a same-browser return as designed | Pass | Storage and built-browser journeys. |
| Profile onward actions carry the intended profile | Pass | New York profile verified in both destinations. |
| Share/copy actions produce text matching the visible result | Pass | Janma-only share runtime test and copy-state checks. |
| Documentation routes and in-repo computation links resolve | Pass | Documentation source/output suites. |

## Priority register

Every open item needs a project issue/story and an explicit priority.

| Priority | Finding | Owner story | Status | Regression/evidence |
|---|---|---|---|---|
| P0 | Daily Horoscope computation boundary | #207 / #211 | Verified | Janma-only runtime, provenance, and share regressions |
| P1 | Async context, shell semantics, focus, contrast, responsive title | #209 | Verified | Request-order and 390–1440/853 browser matrix |
| P1 | Profile detail onward journeys | #236 | Verified | Unit and built-browser direct-action coverage |
| P1 | Horoscope/Muhurtam decision-first hierarchy | #211 | Verified | Screenshots 21–23 and closed-disclosure checks |
| P2 | Next observance and Panchangam handoff | #212 | Fixed | Screenshot 25; unit plus inline-action browser check |
| P2 | Payload measurement, complete reduced-motion/zoom matrix, remaining token debt, stable option label | #208 / #213 | Deferred | Explicitly retained for post-owner work |

## Evidence manifest

Store local review images under a dated folder such as
`docs/screenshots/ux-audit-YYYY-MM-DD/`. Keep baseline, comparison mock, and
after images distinguishable. Do not publish this historical review material in
the user-facing documentation projection.

| Evidence ID | Task / check | Viewport | Before / after | File or URL | Inspected by | Notes |
|---|---|---|---|---|---|---|
| E19 | Horoscope hierarchy decision | comparison | Before + mock | `19-horoscope-surface-options.jpg` | Codex | Design aid, not acceptance proof. |
| E20 | Profile onward actions | phone | After | `20-profile-detail-actions-mobile.jpg` | Codex | Ready state exposes both supported journeys. |
| E21 | Daily Horoscope | phone | Before 15 / after 21 | `15-horoscope-profile-mobile.jpg`, `21-horoscope-profile-mobile-after.jpg` | Codex | First answer reduced; Lagna verdict removed. |
| E22 | Muhurtam hierarchy | compact shell | Before 07 / after 22–23 | `07-muhurtam-results-desktop.jpg`, `22-muhurtam-results-mobile-after.jpg`, `23-muhurtam-results-midwidth-full-after.jpg` | Codex | Tier-first explanation and closed reasons. |
| E24 | Panchangam failure zone | 853 × 900 | After | `24-panchangam-responsive-after.jpg` | Codex | Zero overflow after 959/960 breakpoint alignment. |
| E25 | Next observance | compact shell | Before 08 / after 25 | `08-festivals-desktop.jpg`, `25-festivals-next-observance-after.jpg` | Codex | Direct date-to-Panchangam handoff. |

## Gate decision

| Gate | Decision | Evidence |
|---|---|---|
| P0 resolved | Yes | Daily Horoscope trust contract aligned. |
| P1 resolved | Yes | All release-blocking findings have implementation and regression evidence. |
| Automated checks pass | Yes | TypeScript, 180 Vitest, production site/docs build, and 1,368 Python/browser/computation tests. |
| Browser and console checks pass | Yes | 28 cases, eight fresh routes, and in-app journey walkthrough. |
| Responsive matrix passes | Yes | Includes the additional 853 px failure-zone regression. |
| Residual P2/P3 recorded | Yes | #208/#213 retain performance, zoom/motion, token, and option-label follow-ups. |
| **Ready for owner test** | **Yes** | Local only; no push, PR, merge, or deployment performed. |

### Reviewer statement

> I performed a synthetic expert walkthrough using this scorecard. I did not
> observe representative users, and I am not claiming full accessibility
> conformance. The evidence above supports only the local pre-owner gate.

Reviewer: Codex synthetic product-design audit

Date: 2026-08-29

Branch / commit: `codex/product-wide-ux-audit` / implementation `62feeda`

### Owner gate

Owner testing is the next distinct action only after the local gate says “Yes.”
Record owner feedback in the owning story. Push, pull request, merge, and
deployment remain separately authorized actions under the repository working
agreement.
