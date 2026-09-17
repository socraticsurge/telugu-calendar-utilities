# Profiles workflow boundaries

Task: [#586](https://github.com/socraticsurge/telugu-calendar-utilities/issues/586).
Baseline: `c7377284dbe59ae911a51d5063fd20df2c7a087c`.
Priority signal: CodeScene job `7587546`, Profiles health `5.32`.

## Responsibility map

```text
main.ts / Daily Horoscope / Muhurtam (unchanged callers)
  -> profiles.ts: public controller, active view and store subscription
       -> navigation: contextual return and focus recovery
       -> manual-form / birth-form: validation, request sequencing and save
            -> manual-form-view / birth-form-view: labelled controls
            -> birth-validation: existing wall-time input contract
            -> profile-save: existing store operations and failure messages
       -> list-view / detail-view: saved-profile presentation
            -> detail-sections / natal-view: readiness and saved chart display
       -> elements / form-view / notices: profile-local presentation helpers
       -> contracts: type-only internal dependencies
```

All computation remains in its existing runtime; this change adds no calculation,
storage migration, API endpoint, dependency, engine, ICS or deployment change.
The facade preserves its public exports, options and controller methods.
Forms keep independent request sequences; navigation owns the active view.
An external storage update still leaves unsaved form inputs and focus intact.
The original markup, strings, field order and accessibility attributes are retained.

## Compatibility evidence

- Add three response-ownership tests before changing production source.
- Confirm the new tests pass on the original implementation.
- Capture 24 SHA-256 fingerprints from the original `c7377284` module.
- Verify unchanged DOM, control values, focus and profile data after extraction.
- Cover active/inactive birth calculation, zero/one/four profiles, and all four views.
- Existing tests still cover birth API errors, DST, contextual saves, cross-tab
  reloads, persistence failures, keyboard focus, deletion and consumer selection.
- Move the new response tests into a focused file after the health gate identifies
  that appending them makes the existing test module exceed its size threshold.
- No existing behaviour assertion is changed.

The owner approved changing the inventory CLI golden count from 152 to 167.
The exact-output assertion remains; 15 new UI modules are explicitly classified.
There are still 69 computations and 216 implementations, with no new domain claim.

## Verification

- Local CodeScene: Profiles facade `5.32 -> 10.00`.
- All 14 scored production extractions: `10.00`; contracts are type-only/unscored.
- New response and view-parity test files: `10.00`.
- Whole-change CodeScene safeguard: passed, 20 files checked; only the original
  Profiles facade reports a changed health verdict (improved), with no regressions.
- Full frontend run: 1,713 passed, including 24 baseline fingerprints.
- Full Python and built-browser run: 2,030 passed after the approved count update.
- Type checking, lint and full site/docs build passed.
- Manual desktop/mobile checks: create, switch to manual, save, view and onward
  Daily Horoscope selection; profile pages had no console errors.
- The bare development preview lacks generated sky data; its horoscope data error
  is not treated as a successful live sky check; built-browser fixture tests pass.

The initial restricted run could not bind localhost for browser tests.
The unrestricted rerun exercised those tests; no checks were skipped or relaxed.
Local health is not a claim of hosted post-merge improvement.

## Release gate

The owner approved the desktop/mobile screenshots and publication.
PR [#587](https://github.com/socraticsurge/telugu-calendar-utilities/pull/587)
records the release checks and subsequent merge/hosted-analysis status.
Its first hosted CodeScene check passed; SonarCloud identified duplicated test
fixtures and name-field markup. Those now have shared helpers, with the distinct
help text preserved and every existing behavioural assertion unchanged.
No quality threshold, exclusion or snapshot was changed to resolve the finding.
Required hosted checks, merge and hosted analysis remain release gates.
No PyPI release or version change is required for this browser-only task.
The API clients, Today panel and other hotspots remain separate follow-ups.
