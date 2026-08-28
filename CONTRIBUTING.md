# Contributing

Thanks for your interest in improving this Telugu Panchangam project. Contributions of all kinds are welcome — bug reports, timing corrections, new cities, festival rules, and code.

## Finding current work

The **[Telugu Calendar Utilities GitHub Project](https://github.com/users/socraticsurge/projects/2)**
is the maintenance source of truth. It shows priority and status for current
work. Use **[repository Issues](https://github.com/socraticsurge/telugu-calendar-utilities/issues)**
for the acceptance criteria and discussion attached to each change.

Files under `docs/tracking/` preserve the completed 2026 project and its
decisions. Do not add new work to `STORIES.csv` or `TASKS.csv`.

## Reporting timing discrepancies

The most valuable reports are about **wrong panchangam values** (tithi/nakshatra boundaries, muhurta windows, festival dates). When filing one, please include:

- The date, city, and calculation system (Drik Ganita / Surya Siddhanta / Vakya)
- The value the feed shows and the value you expected
- Your reference source. For the Drik Ganita system, [drikpanchang.com](https://www.drikpanchang.com)'s day page for the same city is the project's reference; Surya Siddhanta and Vakya intentionally differ from modern positions (see the landing page notes), so cite a siddhantic almanac for those.

## Development setup

```bash
pip install -r requirements.txt
npm install
python tools/verify_project.py
```

The verifier checks the provenance ledger links, generated browser activity
data, the Ruff debt baseline, the full Python suite, frontend tests, typecheck,
and production build. Every gate must pass before any change merges.

Documentation is maintained with the code. Read
[`docs/README.md`](docs/README.md) before adding or reorganising documentation;
it defines the canonical directories, authoring contract, archival boundary,
and publication approval gate.

Ruff currently uses a reviewed per-file, per-rule baseline in
`tools/ruff_baseline.json`. New lint debt fails CI. If a change reduces existing
debt, regenerate the baseline with
`python tools/check_ruff_baseline.py --update` and review that reduction in the
same pull request. The optional local hooks use the same check:

```bash
pip install pre-commit
pre-commit install
```

## Ground rules for changes

- **Tests first.** Every behavior change lands with a test that fails before the fix and passes after. Engine changes pin reference values in `tests/`.
- **Verify timing logic against an independent reference.** Any change to tithi, nakshatra, muhurta, or festival calculations must be spot-checked against drikpanchang.com day pages (several dates, more than one city) and the verified dates recorded in the tests.
- **Festival rules carry their deciding moment.** New festivals are one row in the rules tables in `telugu_panchangam/engines/base.py` (sunrise / madhyahna / aparahna / pradosha / nishita) plus a reference-verified test in `tests/test_festivals.py`.
- **English only in user-facing text.** The audience is global; transliterated Telugu terms (Tithi, Varjyam, Rituvu) are used as-is without script.
- **Adding a city** means adding it to `telugu_panchangam/cities.py` with exact coordinates and IANA timezone, plus a sunrise sanity test.

## Pull requests

Keep PRs focused on one change. Fill in the PR template — in particular the verification section: what reference you checked against and which dates. CI runs the test suite and regenerates feeds only from `master`, so PRs don't affect published feeds until merged.

## Questions

Open a discussion or issue — happy to help you find your way around the engines.
