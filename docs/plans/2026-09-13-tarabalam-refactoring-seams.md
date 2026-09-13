# Tarabalam refactoring seams

This is the approved-boundary candidate for the sequential refactor tracked by
GitHub issue #548. It records behavior that must survive extraction without
changing the frozen calculation engines or existing test assertions.

## Baseline

- Source: `src/panels/tarabalam.ts` at `24147bf7e0d3019129d70ac8e540d405a06b88fb`.
- CodeScene local review date: 2026-09-13.
- Code Health: **2.36**.
- Functions: **175**.
- Largest method: `findMuhurta.processDay`, CC **57**, lines 2581-2829.
- Other first-order complexity targets: `muValidLagnaDayData` CC 26,
  `muCalendarDayDrop` CC 20, `muResultScopeDetail` CC 18,
  `tbSaveProfiles` CC 17, and `muScoreActivityLagna` CC 16.
- CodeScene also reports Bumpy Road findings in `muScoreActivityLagna`,
  `muChartOutcomeLabel`, `muAssignTiers`, `muChartCheckMinutes`,
  `muScoreParticipantLagna`, and `findMuhurta.processDay`.

The refactor target is Code Health 6.0 or higher for `tarabalam.ts`, with no
extracted production module below 6.0. `processDay` must fall below CC 15 and no
new function may exceed CC 20.

## Frozen boundary

The panel may consume engine results, generated activity rules, scorer modules,
profile stores, and loaders. It must not modify:

- `telugu_panchangam/engines/`;
- `telugu_panchangam/generators/ics.py`;
- `.github/workflows/`; or
- existing test assertions.

The refactor is structural. It must not change timings, ranking, eligibility,
rendered wording, storage formats, analytics events, or share payloads.

## Current public surface

The complete source export inventory is executable in
`src/__tests__/tarabalam-contract-baseline.test.ts`.

| Contract group | Exports |
| --- | --- |
| Panel lifecycle | `initTarabalamPanel`, `initTarabalamProfiles`, `invalidateMuhurtaSearch`, `tbHasDays`, `muHasLast` |
| Tarabalam workflow | `calcTarabalam`, `renderTarabalam`, `tbProfiles`, `tbRenderProfileInputs`, `tbAddRow`, `tbRemoveRow`, `tbResetProfiles`, `tbSaveProfiles`, `tbSetMode`, `tbToggleShowAll`, `tbExtendTo`, `tbChandraVerdict`, `tbChandraPresentation` |
| Muhurtam workflow | `findMuhurta`, `renderMuhurta`, `muComplexityContracts` |
| Rules and scoring | `muRelevantManualChecks`, `muClassifyManualChecks`, `muAvoidKaranaWindows`, `muNatureBonus`, `muValidLagnaDayData`, `muChartCheckMinutes`, `muChartLagnasForMinutes`, `muChartBoundaryNeedsReview`, `muScoreParticipantTarabalam`, `muScoreParticipantChandrabalam`, `muScoreParticipantLagna`, `muScoreActivityLagna` |
| Chart and result presentation | `muEventSpecificCompletionDisclosure`, `muPluralSuffix`, `muChartOutcomeLabel`, `muChartBoundaryMessage`, `muDaylightOutcomeLabel`, `muPersonalOutcomeLabel`, `muRoleStatus`, `muDroppedOutcomeLabel`, `muChartRemovalRow`, `muChartProvenanceParts`, `muDayContextHtml`, `muDroppedOutcomeHtml`, `muChartReviewDetail`, `muChartStatusDispositionClass`, `muChartValidationItems`, `muChartDispositionHtml`, `muSafetyTitle`, `muChartAssessorCanClaimComplete`, `muChartScreeningDisposition`, `muChartAssessmentTitle`, `muSafetyOverrideFor` |
| Share | `muShareableMuhurtaReasons`, `muChartShareScreeningLine`, `muChartShareIncludesRemainder`, `shareTarabalamOnWhatsApp`, `shareMuhurtaOnWhatsApp` |
| Public types | `TarabalamProfileActions`, `TarabalamProfilesController` |

No export may disappear during extraction. Temporary re-exports from
`tarabalam.ts` are required until callers migrate in a separate, reviewed step.

## State ownership

| State | Current owner | Required owner after extraction |
| --- | --- | --- |
| `TB_DAYS`, `TB_EVENTS` | Tarabalam calculation and rendering | Final panel composition only; pass immutable results to render/share adapters |
| `TB_PROFILE_CONTROLLER`, `TB_MANUAL_SEQUENCE`, `TB_LEGACY_ROWS` | Profile UI and legacy adapter | Profile module |
| `TB_SHOW_ALL`, `TB_MODE` | Tarabalam display preferences | Tarabalam render/controller module |
| `MU_SEARCH_SEQUENCE`, `MU_CHART_ABORT`, `MU_LAST` | Muhurtam async orchestration | Search coordinator only |
| Rule constants and generated activity contract | Muhurtam calculation | Decision/scoring modules; immutable imports |

The extracted pure modules must not read the DOM, browser storage, or these
module globals. State is supplied through typed inputs and returned as values.

## Browser and persistence contracts

| Kind | Complete contract |
| --- | --- |
| Fixed element IDs | `tb-profiles`, `tb-add-btn`, `tb-from`, `tb-to`, `tb-result`, `tb-summary`, `tb-show-all`, `tb-mode`, `mu-activity`, `mu-context`, `mu-result`, `mu-result-announcement`, `tp-city` |
| Fixed selectors | `.tb-section`, `.tb-reset`, `input[data-profile-selection]`, `[data-manual-participant][data-manual-field]`, `[data-muhurta-selection-summary]` |
| Dynamic legacy IDs | `tb-name-N`, `tb-nak-N`, `tb-pada-N`, `tb-lagna-N` |
| Listener types | `click`, `change`, `input` |
| Listener ownership | Profile module owns saved/manual participant, role, purpose, create/edit/manage, add/remove/clear, and activity listeners; panel composition owns date-range invalidation listeners |
| Storage | Guest-profile helpers own `GUEST_PROFILE_STORAGE_KEY`, `GUEST_BIRTH_PROFILE_STORAGE_KEY`, and `GUEST_PROFILE_COMMIT_STORAGE_KEY`; Tarabalam display owns literal key `tc-tb-mode`; manual participants remain session-only |
| Analytics | Share adapters retain `gcEvent('share-tarabalam')` and `gcEvent('share-slots')` |

The current profile controller also owns focus restoration and storage-failure
fallbacks. Those behaviors move with the controller, not with calculation code.

## Rendered-message contracts

Every user-visible output belongs to one of these sinks. Extraction must move a
whole sink with its templates so wording, escaping, ARIA behavior, and markup do
not split across modules.

| Sink | Messages and markup it owns | Characterization evidence |
| --- | --- | --- |
| Profile controller | Saved/manual participant labels, role and borrowing-purpose prompts, selection summary, storage warnings, four-person limit, clear/reset language | Profile selection, storage denial, hostile-name, focus, role, borrowing-purpose, fallback, and limit cases in `muhurta-profile-panel.test.ts` |
| `calcTarabalam` | Missing-star, invalid-range, calculating, and feed-error states | Executable literals in the baseline test; integrated browser smoke |
| `renderTarabalam` | Empty-date state, mode-specific summaries, rows, badges, and expand controls | Tarabalam group and Chandrabalam characterization tests; integrated browser smoke |
| Muhurtam coordinator | Searching, stale-input, chart-screening, partial-screening, and feed-error announcements | Extracted orchestration contract test and chart-state tests |
| `renderMuhurta` | Success count, no-slot result, day-drop context, score reasons, chart status, provenance, safety, personal checks, and review gates | Result-fragment, status-wording, boundary, daylight, personal, no-slot, and activity-rule tests |
| Share adapters | Tarabalam summary and slot shortlist, city/date context, privacy disclosure, chart scope/completion/count details, reasons, safety claim, method link, and product link | Share privacy and chart-share characterization tests |

The baseline test pins the highest-risk flow literals. Detailed helper outputs
remain pinned by the existing behavior tests. Existing assertions are the final
authority if this map and a test ever disagree.

## Share-output contracts

- Both shares open `https://wa.me/?text=` in `_blank` with a URI-encoded payload.
- Tarabalam shares keep their current title, date, person, Tara, Chandrabalam,
  summary, and product-link line ordering.
- Muhurtam shares keep their title, city/date, privacy disclosure, chart status,
  conditional completion details, up-to-five ranked slots, reasons, safety line,
  and product-link line ordering.
- Profile names and natal evidence remain absent from Muhurtam share payloads.
- The chart method URL remains
  `/docs/reference/54-muhurtam-election-chart-screening`.

## Extraction order and dependency direction

1. `tarabalam-profile-controller.ts` takes profile UI, legacy compatibility,
   persistence adapters, and profile-facing DOM listeners.
2. `muhurta-decision-primitives.ts` takes pure day drops, windows, participant
   scoring, slot scoring, doctrinal reasons, and ranking.
3. `muhurta-day-pipeline.ts` takes `processDay` and receives all dependencies as
   a context object; it returns candidates and day-context evidence.
4. `tarabalam-presentation.ts` and `muhurta-presentation.ts` take rendering,
   announcements, chart status, and WhatsApp payload assembly.
5. `tarabalam.ts` becomes composition only and preserves the public exports.

Allowed direction:

```text
tarabalam.ts (composition)
  -> profile controller
  -> Tarabalam presentation
  -> Muhurtam day pipeline -> decision primitives -> existing scorer/data modules
  -> Muhurtam presentation
```

Prohibited cycles:

- Presentation must not import panel composition or profile controller.
- Decision primitives must not import presentation, panel composition, DOM,
  storage, analytics, or loaders.
- The day pipeline must not import presentation, DOM, storage, or analytics.
- The profile controller must not import Muhurtam scoring or presentation.
- Extracted modules must not import from `tarabalam.ts`.

## Verification gates

Each extraction issue must pass its targeted Vitest files, `npm test`,
`npm run typecheck`, `npm run lint`, `npm run build`, the browser smoke suite,
`python -m pytest tests/`, and a CodeScene detailed review plus score check.
Before commit, run the CodeScene pre-commit safeguard. Before a pull request,
run the branch change-set analysis against `origin/master`.

Owner sign-off on this seam map is required before issue #550 moves production
code.
