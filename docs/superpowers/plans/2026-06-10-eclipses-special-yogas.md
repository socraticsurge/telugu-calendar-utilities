# Eclipses & Special Yogas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add eclipse (solar/lunar, type/visibility/Sutak) and special-yoga (Sarvartha Siddhi,
Amrita Siddhi, Visha, Dagdha) information to every generated Panchangam day, surfaced in the ICS
feeds and MCP tools.

**Architecture:** Two new shared, engine-independent modules — `telugu_panchangam/eclipses.py`
(wraps `swisseph` eclipse functions) and `telugu_panchangam/special_yogas.py` (pure lookup tables
keyed on weekday/tithi/nakshatra). `PanchangamDay` gains `eclipse: EclipseInfo | None` and
`special_yogas: list[str]` fields, both defaulted so existing construction is unaffected. All
three engines call both modules and populate the new fields. `ICSGenerator` and the MCP tools
read the new fields to render output.

**Tech Stack:** Python 3.10+, `pyswisseph`, `pytest`.

---

### Task 1: Data model — `EclipseInfo` and new `PanchangamDay` fields

**Files:**
- Modify: `telugu_panchangam/models/panchangam_day.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
def test_eclipse_info_fields():
    from telugu_panchangam.models.panchangam_day import EclipseInfo
    start = datetime(2025, 9, 7, 16, 27, tzinfo=timezone.utc)
    end = datetime(2025, 9, 7, 19, 56, tzinfo=timezone.utc)
    eclipse = EclipseInfo(
        kind='Lunar', subtype='Total', visible=True,
        start=start, end=end,
        sutak_start=start, sutak_end=end,
    )
    assert eclipse.kind == 'Lunar'
    assert eclipse.subtype == 'Total'
    assert eclipse.visible is True
    assert eclipse.start == start
    assert eclipse.sutak_end == end
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_eclipse_info_fields -v`
Expected: FAIL with `ImportError: cannot import name 'EclipseInfo'`

- [ ] **Step 3: Add `EclipseInfo` and new `PanchangamDay` fields**

In `telugu_panchangam/models/panchangam_day.py`, add a new dataclass after `Window` (around
line 26):

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

Then add two new fields at the end of `PanchangamDay` (after `special_notes`, line 80):

```python
    special_notes: list[str] = field(default_factory=list)
    eclipse: EclipseInfo | None = None
    special_yogas: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_eclipse_info_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add telugu_panchangam/models/panchangam_day.py tests/test_models.py
git commit -m "feat: add EclipseInfo and special_yogas fields to PanchangamDay"
```

---

### Task 2: Special yogas lookup module

**Files:**
- Create: `telugu_panchangam/special_yogas.py`
- Test: `tests/test_special_yogas.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_special_yogas.py`:

```python
from telugu_panchangam.special_yogas import get_special_yogas


def test_sarvartha_siddhi_match():
    # Mangalavaram + Krittika is in the Sarvartha Siddhi table for Tuesday.
    # Tithi number 1 (Pratipat) doesn't trigger Visha or Dagdha on any weekday.
    result = get_special_yogas('Mangalavaram', 'Shukla Pratipat', 'Krittika')
    assert result == ['Sarvartha Siddhi Yoga']


def test_amrita_siddhi_match():
    # Shanivaram + Rohini triggers both Sarvartha Siddhi and Amrita Siddhi for Saturday.
    result = get_special_yogas('Shanivaram', 'Shukla Pratipat', 'Rohini')
    assert 'Amrita Siddhi Yoga' in result
    assert 'Sarvartha Siddhi Yoga' in result


def test_visha_yoga_match():
    # Budhavaram (Wednesday) + Ashtami (tithi number 8) triggers Visha Yoga.
    # Chitra is not in Wednesday's Sarvartha/Amrita tables, and 8 is not a
    # Wednesday Dagdha tithi (those are 2 and 3).
    result = get_special_yogas('Budhavaram', 'Shukla Ashtami', 'Chitra')
    assert result == ['Visha Yoga']


def test_dagdha_yoga_match():
    # Guruvaram (Thursday) Dagdha tithi is 6. Krishna Shashthi is tithi number 6
    # ((TITHI_NAMES index 20 % 15) + 1 == 6).
    result = get_special_yogas('Guruvaram', 'Krishna Shashthi', 'Chitra')
    assert result == ['Dagdha Yoga']


def test_dagdha_yoga_wednesday_two_tithis():
    # Wednesday has two Dagdha tithis: 2 and 3. Tritiya is tithi number 3.
    result = get_special_yogas('Budhavaram', 'Shukla Tritiya', 'Chitra')
    assert result == ['Dagdha Yoga']


def test_multiple_yogas_same_day():
    # Adivaram (Sunday) + Hasta is both Sarvartha Siddhi and Amrita Siddhi for Sunday.
    # Tithi number 5 (Panchami) is also Sunday's Visha Yoga tithi.
    result = get_special_yogas('Adivaram', 'Shukla Panchami', 'Hasta')
    assert result == ['Sarvartha Siddhi Yoga', 'Amrita Siddhi Yoga', 'Visha Yoga']


def test_no_yoga():
    # Mangalavaram + Chitra + tithi number 3 matches none of the four tables.
    result = get_special_yogas('Mangalavaram', 'Shukla Tritiya', 'Chitra')
    assert result == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_special_yogas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'telugu_panchangam.special_yogas'`

- [ ] **Step 3: Implement the lookup module**

Create `telugu_panchangam/special_yogas.py`:

```python
from telugu_panchangam.engines.base import TITHI_NAMES

# Weekday -> set of nakshatras forming Sarvartha Siddhi Yoga.
_SARVARTHA_SIDDHI: dict[str, set[str]] = {
    'Adivaram':    {'Hasta', 'Mula', 'Pushya', 'Ashvini', 'Punarvasu', 'Anuradha', 'Shravana', 'Revati'},
    'Somavaram':   {'Shravana', 'Rohini', 'Mrigashira', 'Pushya', 'Anuradha'},
    'Mangalavaram': {'Ashvini', 'Krittika', 'Ashlesha', 'Uttara Ashadha', 'Uttara Phalguni', 'Uttara Bhadrapada'},
    'Budhavaram':  {'Krittika', 'Rohini', 'Hasta', 'Anuradha', 'Mrigashira'},
    'Guruvaram':   {'Ashvini', 'Punarvasu', 'Anuradha', 'Revati', 'Pushya', 'Swati'},
    'Shukravaram': {'Revati', 'Anuradha', 'Ashvini', 'Pushya', 'Shravana', 'Punarvasu'},
    'Shanivaram':  {'Swati', 'Rohini', 'Shravana'},
}

# Weekday -> single nakshatra forming Amrita Siddhi Yoga.
_AMRITA_SIDDHI: dict[str, str] = {
    'Adivaram':    'Hasta',
    'Somavaram':   'Mrigashira',
    'Mangalavaram': 'Ashvini',
    'Budhavaram':  'Anuradha',
    'Guruvaram':   'Pushya',
    'Shukravaram': 'Revati',
    'Shanivaram':  'Rohini',
}

# Weekday -> tithi number (1-15 within either paksha) forming Visha Yoga.
_VISHA_YOGA: dict[str, int] = {
    'Adivaram': 5, 'Somavaram': 6, 'Mangalavaram': 7, 'Budhavaram': 8,
    'Guruvaram': 9, 'Shukravaram': 10, 'Shanivaram': 11,
}

# Weekday -> tithi number(s) (1-15 within either paksha) forming Dagdha Yoga.
_DAGDHA_YOGA: dict[str, set[int]] = {
    'Adivaram': {12}, 'Somavaram': {11}, 'Mangalavaram': {5}, 'Budhavaram': {2, 3},
    'Guruvaram': {6}, 'Shukravaram': {8}, 'Shanivaram': {9},
}


def _tithi_number(tithi_name: str) -> int:
    """1-15 tithi number within either paksha (Pratipat=1 ... Pournami/Amavasya=15)."""
    return (TITHI_NAMES.index(tithi_name) % 15) + 1


def get_special_yogas(vaaram: str, tithi_name: str, nakshatra_name: str) -> list[str]:
    """Return the list of special yogas (possibly empty) for the given day."""
    yogas: list[str] = []

    if nakshatra_name in _SARVARTHA_SIDDHI.get(vaaram, set()):
        yogas.append('Sarvartha Siddhi Yoga')

    if nakshatra_name == _AMRITA_SIDDHI.get(vaaram):
        yogas.append('Amrita Siddhi Yoga')

    tithi_number = _tithi_number(tithi_name)

    if tithi_number == _VISHA_YOGA.get(vaaram):
        yogas.append('Visha Yoga')

    if tithi_number in _DAGDHA_YOGA.get(vaaram, set()):
        yogas.append('Dagdha Yoga')

    return yogas
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_special_yogas.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add telugu_panchangam/special_yogas.py tests/test_special_yogas.py
git commit -m "feat: add special yogas lookup module"
```

---

### Task 3: Eclipse computation module

**Files:**
- Create: `telugu_panchangam/eclipses.py`
- Test: `tests/test_eclipses.py`

This module wraps `pyswisseph`'s eclipse search functions. The reference dates and exact field
indices below were verified by running the eclipse functions directly against this project's
`pyswisseph` installation:

- **2024-06-15**: no solar or lunar eclipse anywhere near this date — used as the "no eclipse"
  case.
- **2025-09-07**: Total Lunar Eclipse, maximum at 18:11:48 UTC (23:41 IST), fully visible from
  Hyderabad (apparent Moon altitude ~64.9°). Partial phase 16:27:04–19:56:33 UTC.
- **2026-02-17**: Annular Solar Eclipse, maximum at 12:11:53 UTC, **not** visible from
  Hyderabad (`sol_eclipse_how` returns `0`). First/last contact 09:56:47–14:27:40 UTC.

`swe.lun_eclipse_when` returns `tret` with: `tret[0]`=time of maximum, `tret[2]`/`tret[3]`=partial
phase begin/end (0 if the eclipse is penumbral-only), `tret[6]`/`tret[7]`=penumbral phase
begin/end. `swe.sol_eclipse_when_glob` returns `tret[0]`=time of maximum,
`tret[2]`/`tret[3]`=first/last global contact. `swe.lun_eclipse_how(tjd, geopos, flags)` returns
`attr` where `attr[6]` is the Moon's apparent altitude at the location (visible if `> 0`).
`swe.sol_eclipse_how(tjd, geopos, flags)` returns `0` as its retflag if the eclipse isn't visible
from that location at all.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_eclipses.py`:

```python
from datetime import date
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.cities import CITIES

HYD = next(c for c in CITIES if c.name == 'Hyderabad')


def test_no_eclipse_returns_none():
    result = get_eclipse_for_date(date(2024, 6, 15), HYD)
    assert result is None


def test_total_lunar_eclipse_visible():
    result = get_eclipse_for_date(date(2025, 9, 7), HYD)
    assert result is not None
    assert result.kind == 'Lunar'
    assert result.subtype == 'Total'
    assert result.visible is True
    assert result.start < result.end
    assert result.sutak_start is not None
    assert result.sutak_start < result.start
    assert result.sutak_end == result.end


def test_solar_eclipse_not_visible_from_hyderabad():
    result = get_eclipse_for_date(date(2026, 2, 17), HYD)
    assert result is not None
    assert result.kind == 'Solar'
    assert result.subtype == 'Annular'
    assert result.visible is False
    assert result.sutak_start is None
    assert result.sutak_end is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_eclipses.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'telugu_panchangam.eclipses'`

- [ ] **Step 3: Implement the eclipse module**

Create `telugu_panchangam/eclipses.py`:

```python
from datetime import date, timedelta
import swisseph as swe

from telugu_panchangam.engines.utils import jd_to_utc, local_midnight_jd
from telugu_panchangam.models.panchangam_day import EclipseInfo, Location

_SOLAR_SUBTYPE_BITS = [
    (swe.ECL_TOTAL, 'Total'),
    (swe.ECL_ANNULAR_TOTAL, 'Annular'),
    (swe.ECL_ANNULAR, 'Annular'),
    (swe.ECL_PARTIAL, 'Partial'),
]

_LUNAR_SUBTYPE_BITS = [
    (swe.ECL_TOTAL, 'Total'),
    (swe.ECL_PARTIAL, 'Partial'),
    (swe.ECL_PENUMBRAL, 'Penumbral'),
]

_SUTAK_HOURS = {'Solar': 12.0, 'Lunar': 9.0}


def _subtype(retflag: int, bits: list[tuple[int, str]]) -> str:
    for bit, name in bits:
        if retflag & bit:
            return name
    return 'Partial'


def _solar_eclipse(jd_midnight: float, geopos: list[float]) -> dict | None:
    try:
        retflag, tret = swe.sol_eclipse_when_glob(jd_midnight, swe.FLG_SWIEPH, 0, False)
    except Exception:
        return None
    if retflag == 0:
        return None
    how_flag, _attr = swe.sol_eclipse_how(tret[0], geopos, swe.FLG_SWIEPH)
    return {
        'kind': 'Solar',
        'subtype': _subtype(retflag, _SOLAR_SUBTYPE_BITS),
        'visible': how_flag != 0,
        'jd_max': tret[0],
        'jd_start': tret[2],
        'jd_end': tret[3],
    }


def _lunar_eclipse(jd_midnight: float, geopos: list[float]) -> dict | None:
    try:
        retflag, tret = swe.lun_eclipse_when(jd_midnight, swe.FLG_SWIEPH, 0, False)
    except Exception:
        return None
    if retflag == 0:
        return None
    _how_flag, attr = swe.lun_eclipse_how(tret[0], geopos, swe.FLG_SWIEPH)
    jd_start, jd_end = (tret[2], tret[3]) if tret[2] else (tret[6], tret[7])
    return {
        'kind': 'Lunar',
        'subtype': _subtype(retflag, _LUNAR_SUBTYPE_BITS),
        'visible': attr[6] > 0,
        'jd_max': tret[0],
        'jd_start': jd_start,
        'jd_end': jd_end,
    }


def get_eclipse_for_date(d: date, location: Location) -> EclipseInfo | None:
    """Return eclipse details for the local calendar day `d`, or None if no
    solar or lunar eclipse reaches its maximum during that day."""
    geopos = [location.lon, location.lat, 0.0]
    jd_midnight = local_midnight_jd(d, location.timezone)
    jd_next_midnight = local_midnight_jd(d + timedelta(days=1), location.timezone)

    for finder in (_solar_eclipse, _lunar_eclipse):
        result = finder(jd_midnight, geopos)
        if result is None:
            continue
        if not (jd_midnight <= result['jd_max'] < jd_next_midnight):
            continue

        if result['visible']:
            sutak_hours = _SUTAK_HOURS[result['kind']]
            sutak_start = jd_to_utc(result['jd_start'] - sutak_hours / 24.0)
            sutak_end = jd_to_utc(result['jd_end'])
        else:
            sutak_start = None
            sutak_end = None

        return EclipseInfo(
            kind=result['kind'],
            subtype=result['subtype'],
            visible=result['visible'],
            start=jd_to_utc(result['jd_start']),
            end=jd_to_utc(result['jd_end']),
            sutak_start=sutak_start,
            sutak_end=sutak_end,
        )
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_eclipses.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add telugu_panchangam/eclipses.py tests/test_eclipses.py
git commit -m "feat: add eclipse computation module"
```

---

### Task 4: Wire eclipse + special yogas into `DrikGanitaEngine`

**Files:**
- Modify: `telugu_panchangam/engines/drik.py`
- Test: `tests/test_drik_engine.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_drik_engine.py`:

```python
def test_eclipse_field_present_and_none_on_non_eclipse_day():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.eclipse is None

def test_eclipse_populated_on_known_eclipse_date():
    from datetime import date
    result = ENGINE.calculate(date(2025, 9, 7), HYD)
    assert result.eclipse is not None
    assert result.eclipse.kind == 'Lunar'

def test_special_yogas_field_is_list():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert isinstance(result.special_yogas, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_drik_engine.py::test_eclipse_field_present_and_none_on_non_eclipse_day tests/test_drik_engine.py::test_eclipse_populated_on_known_eclipse_date tests/test_drik_engine.py::test_special_yogas_field_is_list -v`
Expected: FAIL with `AttributeError: 'PanchangamDay' object has no attribute 'eclipse'`

- [ ] **Step 3: Wire the new modules into `DrikGanitaEngine.calculate`**

In `telugu_panchangam/engines/drik.py`, add the imports near the top (after the existing
`telugu_panchangam.models.panchangam_day` import on line 17):

```python
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.special_yogas import get_special_yogas
```

In `calculate()`, after the line `samvatsara = self._samvatsara(jd_sunrise)` and
`maasam = self._maasam(jd_sunrise)` (just before the `return PanchangamDay(...)` call), add:

```python
        eclipse = get_eclipse_for_date(d, location)
        special_yogas = get_special_yogas(vaaram, tithi_span.name, nakshatra_span.name)
```

Then in the `return PanchangamDay(...)` call, add two new keyword arguments after
`is_sankranti=special['is_sankranti'],`:

```python
            is_sankranti=special['is_sankranti'],
            eclipse=eclipse,
            special_yogas=special_yogas,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_drik_engine.py -v`
Expected: PASS (all tests, including the 3 new ones)

- [ ] **Step 5: Commit**

```bash
git add telugu_panchangam/engines/drik.py tests/test_drik_engine.py
git commit -m "feat: populate eclipse and special_yogas in DrikGanitaEngine"
```

---

### Task 5: Wire eclipse + special yogas into `SuryaSiddhantaEngine` and `VakyaEngine`

**Files:**
- Modify: `telugu_panchangam/engines/surya_siddhanta.py`
- Modify: `telugu_panchangam/engines/vakya.py`
- Test: `tests/test_surya_siddhanta_engine.py`
- Test: `tests/test_vakya_engine.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_surya_siddhanta_engine.py`:

```python
def test_eclipse_and_special_yogas_fields_present():
    result = ENGINE.calculate(REF_DATE, HYD)
    assert result.eclipse is None or hasattr(result.eclipse, 'kind')
    assert isinstance(result.special_yogas, list)
```

Add the same test to `tests/test_vakya_engine.py` (using that file's existing `ENGINE`,
`REF_DATE`, and `HYD` fixtures).

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_surya_siddhanta_engine.py::test_eclipse_and_special_yogas_fields_present tests/test_vakya_engine.py::test_eclipse_and_special_yogas_fields_present -v`
Expected: FAIL with `AttributeError: 'PanchangamDay' object has no attribute 'eclipse'`

- [ ] **Step 3: Wire the new modules into `SuryaSiddhantaEngine.calculate`**

In `telugu_panchangam/engines/surya_siddhanta.py`, add the imports after the existing
`telugu_panchangam.models.panchangam_day` import (line 17):

```python
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.special_yogas import get_special_yogas
```

In `calculate()`, after the line `special    = self._special_flags(tithi_idx, weekday, jd_sunrise, jd_sunset)`
(line 119), add:

```python
        eclipse    = get_eclipse_for_date(d, location)
        special_yogas = get_special_yogas(vaaram, tithi_span.name, nak_span.name)
```

Then in the `return PanchangamDay(...)` call, add the two new keyword arguments before
`**special,`:

```python
            choghadiya=self._choghadiya(weekday, jd_sunrise, jd_sunset),
            eclipse=eclipse,
            special_yogas=special_yogas,
            **special,
        )
```

- [ ] **Step 4: Wire the new modules into `VakyaEngine.calculate`**

`VakyaEngine` subclasses `SuryaSiddhantaEngine` but overrides `calculate()` with its own copy
(in `telugu_panchangam/engines/vakya.py`). Apply the same two changes there:

Add the imports after the existing `telugu_panchangam.models.panchangam_day` import (line 19):

```python
from telugu_panchangam.eclipses import get_eclipse_for_date
from telugu_panchangam.special_yogas import get_special_yogas
```

In `calculate()`, after the line `special    = self._special_flags(tithi_idx, weekday, jd_sunrise, jd_sunset)`
(line 80), add:

```python
        eclipse    = get_eclipse_for_date(d, location)
        special_yogas = get_special_yogas(vaaram, tithi_span.name, nak_span.name)
```

Then in the `return PanchangamDay(...)` call, add the two new keyword arguments before
`**special,`:

```python
            choghadiya=self._choghadiya(weekday, jd_sunrise, jd_sunset),
            eclipse=eclipse,
            special_yogas=special_yogas,
            **special,
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_surya_siddhanta_engine.py tests/test_vakya_engine.py -v`
Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add telugu_panchangam/engines/surya_siddhanta.py telugu_panchangam/engines/vakya.py \
        tests/test_surya_siddhanta_engine.py tests/test_vakya_engine.py
git commit -m "feat: populate eclipse and special_yogas in SuryaSiddhanta and Vakya engines"
```

---

### Task 6: ICS generator — eclipse marker, eclipse details, and yoga listing

**Files:**
- Modify: `telugu_panchangam/generators/ics.py`
- Test: `tests/test_ics_generator.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ics_generator.py`. First add the import at the top of the file:

```python
from telugu_panchangam.models.panchangam_day import EclipseInfo
from datetime import timedelta
```

Then add the tests:

```python
def test_eclipse_marker_and_description():
    days = _make_days(1)
    days[0].eclipse = EclipseInfo(
        kind='Lunar', subtype='Total', visible=True,
        start=datetime(2024, 3, 24, 16, 27, tzinfo=timezone.utc),
        end=datetime(2024, 3, 24, 19, 56, tzinfo=timezone.utc),
        sutak_start=datetime(2024, 3, 24, 7, 27, tzinfo=timezone.utc),
        sutak_end=datetime(2024, 3, 24, 19, 56, tzinfo=timezone.utc),
    )
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    summary = str(events[0].get('summary'))
    description = str(events[0].get('description'))
    assert '⚡' in summary
    assert 'Lunar Eclipse (Total)' in description
    assert 'Sutak' in description


def test_eclipse_not_visible_omits_sutak():
    days = _make_days(1)
    days[0].eclipse = EclipseInfo(
        kind='Solar', subtype='Annular', visible=False,
        start=datetime(2024, 3, 24, 9, 56, tzinfo=timezone.utc),
        end=datetime(2024, 3, 24, 14, 27, tzinfo=timezone.utc),
        sutak_start=None, sutak_end=None,
    )
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Solar Eclipse (Annular)' in description
    assert 'not visible' in description
    assert 'Sutak' not in description


def test_special_yogas_in_description():
    days = _make_days(1)
    days[0].special_yogas = ['Sarvartha Siddhi Yoga', 'Dagdha Yoga']
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Yogas: Sarvartha Siddhi Yoga, Dagdha Yoga' in description


def test_no_yogas_section_when_empty():
    days = _make_days(1)
    days[0].special_yogas = []
    gen = ICSGenerator()
    raw = gen.generate(days, 'drik')
    cal = Calendar.from_ical(raw)
    events = [c for c in cal.walk() if c.name == 'VEVENT']
    description = str(events[0].get('description'))
    assert 'Yogas:' not in description
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ics_generator.py -v -k "eclipse or yoga"`
Expected: FAIL — `'⚡' in summary` and `'Yogas:' not in description` assertions fail because
`_is_special` doesn't check `eclipse` and `_description` doesn't render eclipse/yoga sections.

- [ ] **Step 3: Update `ICSGenerator`**

In `telugu_panchangam/generators/ics.py`, update `_is_special` (line 50-52):

```python
    def _is_special(self, day: PanchangamDay) -> bool:
        return any([day.is_ekadashi, day.is_amavasya, day.is_pournami,
                    day.is_pradosham, day.is_sankranti, day.eclipse is not None])
```

Add a helper method after `_fmt_window` (after line 59):

```python
    def _fmt_eclipse_time(self, dt, tz, day_date) -> str:
        local = dt.astimezone(tz)
        prefix = 'Previous day ' if local.date() < day_date else ''
        return f'{prefix}{local.strftime("%H:%M")}'
```

In `_description`, the current code ends with the `specials` block (lines 102-111):

```python
        specials = []
        if day.is_ekadashi:        specials.append('Ekadashi — fasting day')
        if day.is_amavasya:        specials.append('Amavasya')
        if day.is_pournami:        specials.append('Pournami')
        if day.is_shani_pradosham: specials.append('Shani Pradosham')
        elif day.is_soma_pradosham: specials.append('Soma Pradosham')
        elif day.is_pradosham:     specials.append('Pradosham')
        if day.is_sankranti:       specials.append('Sankranti')
        if specials:
            lines += ['', '⚡ ' + ' | '.join(specials)]
        return '\n'.join(lines)
```

Replace it with (adding the eclipse and special-yogas sections, and the eclipse entry in
`specials`):

```python
        if day.eclipse:
            e = day.eclipse
            emoji = '🌒' if e.kind == 'Solar' else '🌕'
            visibility = 'visible from this location' if e.visible else 'not visible from this location (no Sutak)'
            lines += [
                '',
                f'{emoji} {e.kind} Eclipse ({e.subtype}) — {visibility}',
                f'  Eclipse:  {fmt(e.start, tz)} – {fmt(e.end, tz)}',
            ]
            if e.visible:
                lines.append(
                    f'  Sutak:    {self._fmt_eclipse_time(e.sutak_start, tz, day.date)} – {fmt(e.sutak_end, tz)}'
                )

        if day.special_yogas:
            lines += ['', 'Yogas: ' + ', '.join(day.special_yogas)]

        specials = []
        if day.is_ekadashi:        specials.append('Ekadashi — fasting day')
        if day.is_amavasya:        specials.append('Amavasya')
        if day.is_pournami:        specials.append('Pournami')
        if day.is_shani_pradosham: specials.append('Shani Pradosham')
        elif day.is_soma_pradosham: specials.append('Soma Pradosham')
        elif day.is_pradosham:     specials.append('Pradosham')
        if day.is_sankranti:       specials.append('Sankranti')
        if day.eclipse:
            specials.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
        if specials:
            lines += ['', '⚡ ' + ' | '.join(specials)]
        return '\n'.join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ics_generator.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add telugu_panchangam/generators/ics.py tests/test_ics_generator.py
git commit -m "feat: render eclipse and special yoga details in ICS output"
```

---

### Task 7: MCP tools — expose eclipse and special yogas

**Files:**
- Modify: `telugu_panchangam/mcp/tools.py`
- Test: `tests/test_mcp_tools.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mcp_tools.py`:

```python
def test_get_panchangam_has_eclipse_and_special_yogas_keys():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    assert 'eclipse' in result
    assert 'special_yogas' in result
    assert isinstance(result['special_yogas'], list)


def test_get_panchangam_eclipse_populated_on_eclipse_date():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2025-09-07', 'Hyderabad', 'drik'))
    assert result['eclipse'] is not None
    assert result['eclipse']['kind'] == 'Lunar'
    assert result['eclipse']['subtype'] == 'Total'
    assert result['eclipse']['visible'] is True
    assert result['eclipse']['sutak'] is not None
    assert 'start' in result['eclipse']['sutak']


def test_get_panchangam_eclipse_none_on_non_eclipse_date():
    from telugu_panchangam.mcp.tools import tool_get_panchangam
    result = json.loads(tool_get_panchangam('2026-06-10', 'Hyderabad', 'drik'))
    assert result['eclipse'] is None


def test_get_special_days_eclipse_event_listed():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2025, 9, 'Hyderabad', 'drik'))
    sep7 = next(d for d in result['special_days'] if d['date'] == '2025-09-07')
    assert any('Eclipse' in e for e in sep7['events'])


def test_get_special_days_special_yogas_key_present():
    from telugu_panchangam.mcp.tools import tool_get_special_days
    result = json.loads(tool_get_special_days(2026, 6, 'Hyderabad', 'drik'))
    assert len(result['special_days']) > 0
    for day in result['special_days']:
        assert 'special_yogas' in day
        assert isinstance(day['special_yogas'], list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_mcp_tools.py -v -k "eclipse or special_yogas"`
Expected: FAIL with `KeyError: 'eclipse'` / `KeyError: 'special_yogas'`

- [ ] **Step 3: Update `_special_events` and `tool_get_panchangam`**

In `telugu_panchangam/mcp/tools.py`, update `_special_events` (lines 77-86):

```python
def _special_events(day: PanchangamDay) -> list[str]:
    events = []
    if day.is_ekadashi:         events.append('Ekadashi — fasting day')
    if day.is_amavasya:         events.append('Amavasya')
    if day.is_pournami:         events.append('Pournami')
    if day.is_shani_pradosham:  events.append('Shani Pradosham')
    elif day.is_soma_pradosham: events.append('Soma Pradosham')
    elif day.is_pradosham:      events.append('Pradosham')
    if day.is_sankranti:        events.append('Sankranti')
    if day.eclipse:              events.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
    return events
```

Add a new helper after `_window_to_dict` (after line 74):

```python
def _eclipse_to_dict(eclipse, tz: str) -> Optional[dict]:
    if eclipse is None:
        return None
    return {
        'kind': eclipse.kind,
        'subtype': eclipse.subtype,
        'visible': eclipse.visible,
        'start': _fmt_time(eclipse.start, tz),
        'end': _fmt_time(eclipse.end, tz),
        'sutak': {
            'start': _fmt_time(eclipse.sutak_start, tz),
            'end': _fmt_time(eclipse.sutak_end, tz),
        } if eclipse.sutak_start is not None else None,
    }
```

In `tool_get_panchangam`, add `'eclipse'` and `'special_yogas'` top-level keys to the returned
dict — insert them right after the `'choghadiya'` entry (line 158) and before `'special_days'`:

```python
            'choghadiya': [
                {'name': w.name, 'start': _fmt_time(w.start, tz)}
                for w in day.choghadiya
            ],
            'eclipse': _eclipse_to_dict(day.eclipse, tz),
            'special_yogas': day.special_yogas,
            'special_days': specials,
            'is_special': bool(specials),
```

- [ ] **Step 4: Update `tool_get_special_days`**

In `tool_get_special_days`, update the loop body (lines 222-231):

```python
        for day_num in range(1, days_in_month + 1):
            d = date(year, month, day_num)
            day = engine.calculate(d, loc)
            is_notable = (
                day.is_ekadashi or day.is_amavasya or day.is_pournami
                or day.is_pradosham or day.is_sankranti or day.eclipse is not None
            )
            if is_notable:
                events = _special_events(day)
                special_days.append({
                    'date': d.isoformat(),
                    'tithi': day.tithi.name,
                    'events': events,
                    'special_yogas': day.special_yogas,
                })
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_mcp_tools.py -v`
Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add telugu_panchangam/mcp/tools.py tests/test_mcp_tools.py
git commit -m "feat: expose eclipse and special_yogas in MCP tools"
```

---

### Task 8: Full test suite and feed spot-check

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`
Expected: PASS (all tests, no regressions)

- [ ] **Step 2: Generate a short feed range covering the known eclipse date and inspect it**

```bash
python3 - << 'EOF'
from datetime import date
from telugu_panchangam.generate import generate_feeds

generate_feeds(
    output_dir='/tmp/eclipse-check',
    start=date(2025, 9, 5),
    end=date(2025, 9, 9),
    systems=['drik'],
    city_names=['Hyderabad'],
)
EOF
grep -A 6 "20250907" /tmp/eclipse-check/hyderabad-drik.ics
```

Expected output: an event for `20250907` whose `SUMMARY` starts with `⚡` and whose
`DESCRIPTION` contains `Lunar Eclipse (Total)` and a `Sutak` line.

- [ ] **Step 3: Clean up the temporary feed**

```bash
rm -rf /tmp/eclipse-check
```

---

## Self-Review Notes

- **Spec coverage:** `EclipseInfo`/new fields (Task 1), eclipse computation (Task 3), special
  yogas computation (Task 2), engine wiring for all three systems (Tasks 4-5), ICS marker +
  description sections for both eclipses and yogas (Task 6), MCP `tool_get_panchangam` /
  `tool_get_special_days` updates (Task 7), and an end-to-end feed check (Task 8) — all spec
  sections are covered. Vishaghati, planetary transits, and TTD Poorva Paddhati are explicitly
  out of scope per the spec's Non-Goals.
- **Type consistency:** `get_eclipse_for_date(d, location) -> EclipseInfo | None` (Task 3) is
  called identically in all three engines (Tasks 4-5) and consumed via `day.eclipse` in Task 6/7.
  `get_special_yogas(vaaram, tithi_name, nakshatra_name) -> list[str]` (Task 2) is called
  identically in all three engines and consumed via `day.special_yogas`.
- **No placeholders:** all code blocks are complete and runnable; eclipse reference dates/values
  were obtained by running the actual `pyswisseph` calls against this project's dependencies.
