# Browser smoke suite

`tests/test_browser_smoke.py` remains the only collection entrypoint.
CI still runs that path and Python-only CI still ignores it.
Its explicit exports preserve all 113 original node IDs and their order.
The build/server/browser fixtures retain module scope and cleanup behavior.

The parent test package registers assertion rewriting before support imports.
The support package never imports Playwright.
The entrypoint retains the optional Playwright/npm skip gates.
Keep journey filenames free of the `test_` prefix to avoid duplicate collection.
Add new cases to the appropriate journey module and explicitly export them from
the entrypoint in the desired order.

## Boundaries

- `calendar_fixtures`, `planet_fixtures`, `chart_gateway`: deterministic inputs,
  canonical Lagna projection, and intercepted gateway responses.
- `profile_support`, `muhurta_support`: browser setup and journey actions.
- `accessibility`, `muhurta_assertions`: existing result and accessibility checks.
- `*_cases`: product journeys, with long profile scenarios split into phases.
- `constants`: shared repository paths and fixture identifiers.

Screenshot tooling consumes five compatibility exports from the entrypoint.
`test_browser_smoke_imports.py` protects direct-script loading from another
directory and the missing-Playwright skip path.

## Refactor evidence (epic #556)

Baseline: `fb871d9511e50ebe221b39d05c50c6240ff9e003`.
Hosted baseline: CodeScene project 84645, job 7544262.

- Original entrypoint Code Health: 3.67; refactored entrypoint: 10.0.
- All 17 scored extracted modules: 9.05–10.0; constants-only module: unscored.
- 445 original assertion ASTs unchanged, including their messages.
- 23 ordered test functions, all decorators and signatures unchanged.
- 113 original parameterized cases retained under the original entrypoint.
- 3,007 differential fixture evaluations matched the baseline exactly, including
  success values and failures for all one-, two-, and three-Lagna Gold tuples,
  scenario/house combinations, and batched/empty/boundary chart payloads.
- Original full suite: 1,883 passed, one existing data-dependent skip.
- Refactored full suite plus import-contract guards: 1,885 passed, one skip.
- Frontend: 763 tests passed; both TypeScript projects typechecked.
- Ruff 0.16.6 lint and complexity gates: unchanged zero-debt baselines.

No production code, frozen engine, ICS generator, workflow, existing assertion,
or lint/complexity threshold was changed.

The CodeScene change-set gate reports inherited long methods, parameterized
test signatures, and fixture duplication as introduced in their new files.
That gate is not claimed as passed: the reviewed acceptance criterion is
removing red code without relocating it below the agreed score floor of 6.
All scored extracted modules exceed 9; unchanged test signatures deliberately
retain existing node IDs and fixtures rather than hiding these residual smells.
