# Eclipses & Special Yogas — Design Spec

**Date:** 2026-06-10
**Status:** approved

---

## Overview

Add two categories of Panchangam information that are currently missing entirely:

1. **Eclipses** (solar/lunar) — type, visibility from the location, eclipse window, and Sutak
   (ritual abstinence) window.
2. **Special Yogas** — auspicious/inauspicious weekday+nakshatra/tithi combinations:
   Sarvartha Siddhi Yoga, Amrita Siddhi Yoga, Visha Yoga, and Dagdha Yoga.

Both are surfaced in the existing per-day ICS event (no new feed files, no new calendar
subscriptions).

---

## Goals

- Compute and surface eclipse information (solar & lunar) for every day in the generated feeds,
  for all three calculation systems (`drik`, `surya_siddhanta`, `vakya`).
- Compute and surface four special yogas (Sarvartha Siddhi, Amrita Siddhi, Visha, Dagdha) derived
  from each day's existing `vaaram`/`tithi`/`nakshatra` values, for all three systems.
- Eclipse days get the existing `⚡` special-day marker in `SUMMARY` plus full eclipse details
  (type, window, Sutak) in `DESCRIPTION`.
- Special yogas are listed in `DESCRIPTION` only — no `SUMMARY` marker change.

## Non-Goals

- **Vishaghati** — deferred. It requires ghati-level (24-minute sub-division) timing computation
  that none of the three engines currently produce. Same category of "needs new infrastructure"
  as planetary transits below.
- **Planetary transits ("peyarchi") for all planets** — deferred to a future project. The
  `surya_siddhanta` and `vakya` engines currently model only Sun and Moon; supporting all 9 grahas
  would require building new mean-motion models for 7 more planets in those engines.
- **TTD "Poorva Paddhati" matching system** — separate future project, tracked independently.
- No changes to the landing page (`docs/index.html`) or feed file naming/structure.

---

## Data Model Changes (`telugu_panchangam/models/panchangam_day.py`)

New dataclass:

```python
@dataclass
class EclipseInfo:
    kind: str        # 'Solar' | 'Lunar'
    subtype: str     # 'Total' | 'Partial' | 'Annular' | 'Penumbral'
    visible: bool    # visible from this location
    start: datetime
    end: datetime
    sutak_start: datetime | None  # None if not visible (no Sutak observed)
    sutak_end: datetime | None
```

`PanchangamDay` gains two new fields, both defaulting to "nothing happened" so existing
construction sites and tests are unaffected:

```python
eclipse: EclipseInfo | None = None
special_yogas: list[str] = field(default_factory=list)
```

---

## Eclipses

### Computation (`telugu_panchangam/eclipses.py`, new shared module)

```python
def get_eclipse_for_date(d: date, location: Location) -> EclipseInfo | None:
```

- Eclipses are a physical event independent of calculation tradition, so this single
  implementation is shared by all three engines (each imports and calls it from `calculate()`).
  `swisseph` is already a project dependency (used by `drik`), so importing it from
  `surya_siddhanta`/`vakya` for this purpose only is acceptable.
- For the given local calendar day at `location`'s coordinates:
  - Search for the next solar eclipse via `swe.sol_eclipse_when_loc` and the next lunar eclipse
    via `swe.lun_eclipse_when_loc`, starting from local midnight of `d`.
  - If the eclipse's maximum-phase time falls within `[local midnight of d, local midnight of
    d+1)`, it belongs to this day; otherwise return `None` for that eclipse type.
  - If both a solar and lunar eclipse fall on the same day (astronomically essentially never in
    practice, but handle gracefully), prefer whichever one's maximum is earlier in the day.
- For the matched eclipse, call `swe.sol_eclipse_how` / `swe.lun_eclipse_how` at the location to
  determine `subtype` (Total/Partial/Annular for solar; Total/Partial/Penumbral for lunar) and
  `visible` (whether any phase of the eclipse is visible from the location).
- `start`/`end` = the eclipse's begin/end times (UTC `datetime`), from the `*_when_loc` result.
- Sutak window (only when `visible` is `True`; otherwise both `None`):
  - Solar eclipse: Sutak begins 12 hours before `start`.
  - Lunar eclipse: Sutak begins 9 hours before `start`.
  - Both end at `end`.
- If `swisseph` raises because no eclipse exists in the search window (common — most days have
  none), catch the exception and return `None`.

### Engine integration

Each of `drik.py`, `surya_siddhanta.py`, `vakya.py` calls `get_eclipse_for_date(d, location)` in
`calculate()` and assigns the result to `day.eclipse`.

### ICS Output (`generators/ics.py`)

- `_is_special()` extended: also returns `True` when `day.eclipse is not None`, so eclipse days
  get the `⚡` marker in `SUMMARY`.
- `_description()`:
  - If `day.eclipse` is set, append a section before the existing specials line:
    ```
    🌒 Solar Eclipse (Partial) — visible from this location
      Eclipse:  10:12 – 12:45
      Sutak:    Previous day 22:12 – 12:45
    ```
    or, when not visible:
    ```
    🌒 Solar Eclipse (Partial) — not visible from this location (no Sutak)
      Eclipse:  10:12 – 12:45
    ```
    Use `🌒` for solar eclipses and `🌕` for lunar eclipses. Times before midnight (i.e.
    `sutak_start` falls on the previous local day) are prefixed with "Previous day ".
  - The existing `specials` list (which produces the trailing `⚡ ...` summary line) gets an
    additional entry, e.g. `'Solar Eclipse (Partial)'` / `'Lunar Eclipse (Total)'`.

---

## Special Yogas

### Computation (`telugu_panchangam/special_yogas.py`, new shared module)

```python
def get_special_yogas(vaaram: str, tithi_name: str, nakshatra_name: str) -> list[str]:
```

Pure combinatorial lookup against `vaaram` (from `VAARAM_NAMES`), `tithi_name` (from
`TITHI_NAMES`), and `nakshatra_name` (from `NAKSHATRA_NAMES`) — all closed enums already produced
by every engine, so no error handling is needed (lookups are dict gets with safe defaults).

Internal lookup tables, built from standard panchangam references (filling in the Saturday
Sarvartha Siddhi combination and the full Amrita Siddhi table during implementation, beyond what
was found in initial research):

- **Sarvartha Siddhi Yoga** — table of `{weekday: set[nakshatra]}`. Returns `'Sarvartha Siddhi
  Yoga'` if `(vaaram, nakshatra_name)` matches.
- **Amrita Siddhi Yoga** — table of `{weekday: set[nakshatra]}`. Returns `'Amrita Siddhi Yoga'` if
  `(vaaram, nakshatra_name)` matches. (Note: Amrita Siddhi and Sarvartha Siddhi can occur on the
  same day for some combinations — both are returned if both match.)
- **Visha Yoga** — table of `{weekday: tithi_number}`:
  - Sunday+Panchami(5), Monday+Shashthi(6), Tuesday+Saptami(7), Wednesday+Ashtami(8),
    Thursday+Navami(9), Friday+Dashami(10), Saturday+Ekadashi(11).
  - Tithi number is derived from `tithi_name` (index into `TITHI_NAMES`, 1-indexed within each
    paksha — i.e. both Shukla and Krishna Panchami count as "5").
  - Returns `'Visha Yoga'` if `(vaaram, tithi_number)` matches.
- **Dagdha Yoga** — table of `{weekday: tithi_number}`:
  - Sunday→12, Monday→11, Tuesday→5, Wednesday→2 or 3, Thursday→6, Friday→8, Saturday→9.
  - Returns `'Dagdha Yoga'` if `(vaaram, tithi_number)` matches.

Returns a list of all matching yoga names (empty list if none apply), e.g.
`['Sarvartha Siddhi Yoga', 'Dagdha Yoga']`.

### Engine integration

Each engine calls `get_special_yogas(day.vaaram, day.tithi.name, day.nakshatra.name)` after those
fields are computed in `calculate()`, and assigns the result to `day.special_yogas`.

### ICS Output (`generators/ics.py`)

- `_description()`: if `day.special_yogas` is non-empty, append a line:
  ```
  Yogas: Sarvartha Siddhi Yoga, Dagdha Yoga
  ```
- No `SUMMARY`/`_is_special()` change for special yogas.

---

## MCP Server Changes (`telugu_panchangam/mcp/tools.py`)

The MCP tools wrap the same `PanchangamDay` objects, so they need to expose the new fields too:

- `_special_events(day)`: extend to also append an eclipse entry when `day.eclipse` is set, e.g.
  `'Solar Eclipse (Partial)'` / `'Lunar Eclipse (Total)'` — same strings used in the ICS
  `specials` list, keeping the two surfaces consistent.
- `tool_get_panchangam`: add a top-level `'eclipse'` key — `None` if `day.eclipse is None`,
  otherwise:
  ```python
  {
      'kind': day.eclipse.kind,
      'subtype': day.eclipse.subtype,
      'visible': day.eclipse.visible,
      'start': _fmt_time(day.eclipse.start, tz),
      'end': _fmt_time(day.eclipse.end, tz),
      'sutak': {
          'start': _fmt_time(day.eclipse.sutak_start, tz),
          'end': _fmt_time(day.eclipse.sutak_end, tz),
      } if day.eclipse.sutak_start else None,
  }
  ```
  Also add a top-level `'special_yogas': day.special_yogas` (list of strings, possibly empty).
  `'special_days'`/`'is_special'` continue to come from `_special_events`/`bool(specials)`, now
  including the eclipse entry per above.
- `tool_get_muhurta`: no changes — eclipses and special yogas aren't muhurta data.
- `tool_get_special_days`: extend the inclusion condition to also include days where
  `day.eclipse is not None`, and include `'special_yogas'` in each returned day's dict (so a day
  that's *only* notable for a special yoga, e.g. Sarvartha Siddhi with no other special flag, is
  *not* added to this list — `special_yogas` are informational annotations on existing entries,
  not a reason by themselves to appear in `special_days`. This matches the ICS decision that
  special yogas get no `SUMMARY`/specials-list marker of their own).

---

## Error Handling

- `eclipses.get_eclipse_for_date`: catch `swisseph` exceptions raised when no eclipse is found in
  the search window (the common case) and return `None`.
- `special_yogas.get_special_yogas`: no error handling needed — all inputs are closed-enum values
  already validated by the engines producing them.

---

## Testing / Verification

- `tests/test_eclipses.py`:
  - At least one known historical/upcoming solar eclipse date and one lunar eclipse date,
    verifying `kind`, `subtype`, `visible`, `start`/`end`, and Sutak window presence/absence.
  - A non-eclipse date returns `None`.
- `tests/test_special_yogas.py`: table-driven tests covering each of the four yoga types with at
  least one matching combination and one non-matching combination, including the
  multi-yoga-on-same-day case.
- Existing engine tests (`tests/test_drik.py`, `tests/test_surya_siddhanta.py`,
  `tests/test_vakya.py` or equivalent): extend a representative day's assertions to check
  `day.eclipse` (expected `None` for that test's date) and `day.special_yogas` (expected value for
  that date — `[]` or whichever yogas legitimately apply).
- ICS generation tests: add a synthetic `PanchangamDay` with `eclipse` set and `special_yogas`
  non-empty; assert the new `DESCRIPTION` sections render correctly and `⚡` appears in `SUMMARY`
  due to the eclipse.
- Run `python -m telugu_panchangam.generate` for a short date range covering a known eclipse date
  to manually spot-check the generated `.ics` output.
- `tests/test_mcp_tools.py` (or equivalent): extend `tool_get_panchangam` tests to assert the new
  `'eclipse'` and `'special_yogas'` keys (both the populated and `None`/`[]` cases), and extend
  `tool_get_special_days` tests to confirm an eclipse-only day is included while a
  special-yoga-only day is not.
