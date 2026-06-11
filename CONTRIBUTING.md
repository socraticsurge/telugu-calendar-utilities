# Contributing

Thanks for your interest in improving this Telugu Panchangam project. Contributions of all kinds are welcome — bug reports, timing corrections, new cities, festival rules, and code.

## Reporting timing discrepancies

The most valuable reports are about **wrong panchangam values** (tithi/nakshatra boundaries, muhurta windows, festival dates). When filing one, please include:

- The date, city, and calculation system (Drik Ganita / Surya Siddhanta / Vakya)
- The value the feed shows and the value you expected
- Your reference source. For the Drik Ganita system, [drikpanchang.com](https://www.drikpanchang.com)'s day page for the same city is the project's reference; Surya Siddhanta and Vakya intentionally differ from modern positions (see the landing page notes), so cite a siddhantic almanac for those.

## Development setup

```bash
pip install -r requirements.txt
python -m pytest tests/
```

The full suite must pass before any change merges.

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
