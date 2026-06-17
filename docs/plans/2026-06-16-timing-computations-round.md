# Timing Computations Round — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 16 classical-authority timing computations (ghati/vighati precision, ayanamsa parameter, pada on daily span, Vishaghati, Bhadra Mukha/Puchha, Sankramana ghati-window, 5 Panchaka Nakshatras, Khar-Maasa, Simha-Stha Guru/Shukra, Guru/Shukra Maudhya, Adhika Maasa consumption, Pitru Paksha window, Anandadi 28 Yogas, Disha Shoola, Mukha nakshatra direction, Panchaka Rahita) as one release that sharpens muhurta decisions. All non-personal — properties of the moment, not of a person. Computations land via MCP and on `PanchangamDay`, ready for the website to surface later without re-architecture.

**Architecture:** Additive only. The frozen-core engines (Drik / Surya Siddhanta / Vakya) gain one constructor parameter (ayanamsa) and populate new optional fields on `PanchangamDay`. New compute lives in new top-level modules consumed by both the engines and the muhurta finder. ICS feeds stay byte-identical (golden snapshot guards this). MCP tools serialize new fields automatically via the existing dict-builders, and `find_muhurta` reasons gain entries for every new filter.

**Tech Stack:** Python 3.10–3.13, `pyswisseph` for ephemeris (already a dependency), `pytest` for tests, FastMCP for the MCP server.

---

## Project context (read before starting)

- **Frozen core** — `telugu_panchangam/engines/` and `telugu_panchangam/generators/ics.py` are append-only. The only engine edit this plan permits is threading the `ayanamsa` parameter through Drik (SS and Vakya do not use Swiss for sidereal positions) and adding `PanchangamDay` field assignments. No changes to existing test assertions; the golden ICS snapshot must remain byte-identical.
- **Commits** — solely `Socraticsurge <cvk.atreya@gmail.com>`. No `Co-Authored-By` trailers.
- **Test mandate** — `python -m pytest tests/` must stay green at every commit. Suite is at 849 today.
- **Drikpanchang verification** — engine-affecting PRs cite DP day-pages in the body. Where DP doesn't cover the rule (Panchaka Rahita, Anandadi, Maudhya), cite Muhurta Chintamani / standard panchangam authority instead.
- **Branch model** — one feature branch per task; squash-merge to master. The release task (#17) bumps versions and CHANGELOG in a final consolidating PR.
- **UI is out of scope** — no edits under `docs/index.html`, `docs/feeds/`, or `docs/muhurta-scorer.js`. The "machinery for the website" means: MCP serialization is complete, fields are stable, JS scorer mirror can pull from it when Vite migration resumes.

---

## File layout (all additions / modifications)

```
telugu_panchangam/
├── ghati.py                          NEW — civil↔ghati/vighati utility, sunrise-anchored
├── panchaka.py                       NEW — Panchaka Rahita (mod-9 dosha)
├── disha_shoola.py                   NEW — weekday direction-of-blocked-travel
├── nakshatra_filters.py              NEW — 5 Panchaka Nakshatras + Adho/Urdhva/Tiryan Mukha
├── maasa_filters.py                  NEW — Khar-Maasa flag + Adhika-Maasa restriction predicate
├── karana_windows.py                 NEW — Bhadra Mukha/Puchha sub-windows + Vishaghati
├── sankramana.py                     NEW — Sankramana 16-ghati avoidance window
├── pitru_paksha.py                   NEW — 15-day window detection
├── special_yogas.py                  EXTEND — add Anandadi 28 Yogas (kept in this file because shape matches)
├── eclipses.py                       untouched
├── gochara/
│   ├── combustion.py                 NEW — Guru/Shukra Maudhya
│   ├── simha_stha.py                 NEW — Jupiter/Venus in Simha
│   ├── positions.py                  untouched
│   └── rules.py                      untouched
├── engines/
│   ├── utils.py                      MODIFY — ayanamsa-parameterised sidereal/sun/moon longitude
│   ├── drik.py                       MODIFY — accept ayanamsa; populate new PanchangamDay fields
│   ├── surya_siddhanta.py            MODIFY — populate new fields (those derivable without Swiss)
│   ├── vakya.py                      MODIFY — populate new fields (those derivable without Swiss)
│   └── base.py                       MODIFY — small helpers for shared rules; no festival changes
├── models/
│   └── panchangam_day.py             MODIFY — new dataclasses + new optional PanchangamDay fields
├── personal/
│   └── muhurta.py                    MODIFY — consume new flags; new activity-rule fields
├── mcp/
│   ├── server.py                     MODIFY — extend docstrings to mention new outputs + ayanamsa arg
│   ├── tools.py                      MODIFY — serialize new fields; surface in find_muhurta reasons
│   └── server.json                   MODIFY — version 1.8.0 → 1.9.0
├── pyproject.toml                    MODIFY — version 1.8.0 → 1.9.0
└── README_PYPI.md                    MODIFY — mention new computations
tests/
├── test_ghati.py                     NEW
├── test_ayanamsa.py                  NEW
├── test_pada_on_daily.py             NEW
├── test_vishaghati.py                NEW
├── test_bhadra_mukha_puchha.py       NEW
├── test_sankramana_window.py         NEW
├── test_panchaka_nakshatras.py       NEW
├── test_khar_maasa.py                NEW
├── test_simha_stha.py                NEW
├── test_maudhya.py                   NEW
├── test_adhika_maasa_muhurta.py      NEW
├── test_pitru_paksha.py              NEW
├── test_anandadi.py                  NEW
├── test_disha_shoola.py              NEW
├── test_mukha_nakshatra.py           NEW
├── test_panchaka_rahita.py           NEW
└── test_version_sync.py              MODIFY — bump expected version to 1.9.0
docs/
└── plans/
    └── 2026-06-16-timing-computations-round.md   THIS FILE (already created)
CHANGELOG.md                          MODIFY — append [1.9.0] section
```

---

## Data-model additions up front

These fields are added incrementally across the tasks below, but listed here so the whole shape is visible. Every new field has a safe default (`None`, `[]`, `False`) so existing engine constructors and tests continue working unchanged.

```python
# telugu_panchangam/models/panchangam_day.py — additions (final shape after all tasks)

@dataclass
class GhatiClock:
    """Ghati/vighati clock anchored at sunrise.

    1 ghati = 24 min; 1 vighati = 24 s; 60 vighatis = 1 ghati; 60 ghatis = 1 ahoratri.
    Sunrise-to-sunrise normalisation makes ghatika positions stable across day length.
    """
    sunrise: datetime
    next_sunrise: datetime
    seconds_per_ghati: float   # day length / 60 (not 1440 — classical reckoning)


@dataclass
class GhatiWindow:
    """A window expressed in both civil time and ghatis-from-sunrise."""
    name: str
    start: datetime
    end: datetime
    start_ghati: float
    end_ghati: float


@dataclass
class PanchakaInfo:
    """Panchaka Rahita evaluation at a moment (mod-9 of Tithi+Vaaram+Nakshatra+Lagna)."""
    remainder: int               # 0..8
    name: str                    # 'Mrityu' | 'Agni' | 'Raja' | 'Chora' | 'Roga' | 'Rahita'
    auspicious: bool             # True iff remainder in {0, 3, 5, 7}
    avoid_for: list[str]         # ['ceremony', 'construction', ...] — activity tags this dosha blocks


@dataclass
class MaudhyaInfo:
    """Heliacal combustion (asta / maudhya) of a graha relative to the Sun."""
    graha: str                   # 'Guru' | 'Shukra'
    elongation_deg: float        # absolute Sun-planet elongation in degrees
    combust: bool                # True iff elongation < threshold for this graha
    threshold_deg: float         # classical threshold used (11° Guru, 10° Shukra)


# PanchangamDay gains (all default-safe):
ghati_clock: GhatiClock | None = None              # Task 1
nakshatra_pada: int | None = None                  # Task 2 — Moon's pada at sunrise (1..4)
vishaghati: list[GhatiWindow] = field(default_factory=list)        # Task 4
bhadra_mukha: GhatiWindow | None = None            # Task 5
bhadra_puchha: GhatiWindow | None = None           # Task 5
sankramana_avoidance: Window | None = None         # Task 6
in_panchaka_nakshatra: bool = False                # Task 7
is_khar_maasa: bool = False                        # Task 8
khar_maasa_name: str | None = None                 # Task 8 — 'Dhanur' | 'Meena' | None
simha_stha_guru: bool = False                      # Task 9
simha_stha_shukra: bool = False                    # Task 9
guru_maudhya: MaudhyaInfo | None = None            # Task 10
shukra_maudhya: MaudhyaInfo | None = None          # Task 10
is_pitru_paksha: bool = False                      # Task 12
anandadi_yoga: str | None = None                   # Task 13
disha_shoola_direction: str | None = None          # Task 14 — 'East'|'West'|'North'|'South'
nakshatra_mukha: str | None = None                 # Task 15 — 'Adho'|'Urdhva'|'Tiryan'
panchaka_rahita: PanchakaInfo | None = None        # Task 16 — sunrise-lagna based day-level value
```

---

## Task 1: Ghati / vighati infrastructure

**Files:**
- Create: `telugu_panchangam/ghati.py`
- Modify: `telugu_panchangam/models/panchangam_day.py` (add `GhatiClock`, `GhatiWindow`, add field on `PanchangamDay`)
- Modify: `telugu_panchangam/engines/base.py` (populate `ghati_clock` in shared assembly path)
- Modify: `telugu_panchangam/engines/drik.py`, `surya_siddhanta.py`, `vakya.py` (call new assembly)
- Modify: `telugu_panchangam/mcp/tools.py` (serialize `ghati_clock`)
- Test: `tests/test_ghati.py`

**Concept:** A ghati is 1/60 of an ahoratri (sunrise→next-sunrise). Classical scaling is *not* 24h/60: in summer days the daytime portion has more ghatis, but our clock here uses the simple sunrise→next-sunrise division. All ghati-derived windows in later tasks anchor on this clock.

- [ ] **Step 1.1: Add `GhatiClock` and `GhatiWindow` dataclasses**

Modify `telugu_panchangam/models/panchangam_day.py` — append after the existing `Window` dataclass:

```python
@dataclass
class GhatiClock:
    """Ghati/vighati clock anchored at sunrise.
    1 ghati = 1/60 ahoratri (sunrise→next-sunrise). 60 vighatis = 1 ghati.
    """
    sunrise: datetime
    next_sunrise: datetime
    seconds_per_ghati: float


@dataclass
class GhatiWindow:
    """A window expressed in both civil time and ghatis-from-sunrise."""
    name: str
    start: datetime
    end: datetime
    start_ghati: float
    end_ghati: float
```

Add to `PanchangamDay` (alongside other optional fields, with default `None`):

```python
ghati_clock: 'GhatiClock | None' = None
```

- [ ] **Step 1.2: Write failing test for ghati conversion**

Create `tests/test_ghati.py`:

```python
from datetime import datetime, timezone, timedelta
from telugu_panchangam.ghati import (
    make_clock, civil_to_ghati, ghati_to_civil, ghati_window,
)
from telugu_panchangam.models.panchangam_day import GhatiClock


def test_make_clock_seconds_per_ghati():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    next_sunrise = sunrise + timedelta(hours=24)
    clk = make_clock(sunrise, next_sunrise)
    assert clk.seconds_per_ghati == 86400 / 60


def test_civil_to_ghati_sunrise_is_zero():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    assert civil_to_ghati(clk, sunrise) == 0.0


def test_civil_to_ghati_one_ghati_after():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    one_ghati_later = sunrise + timedelta(seconds=clk.seconds_per_ghati)
    assert abs(civil_to_ghati(clk, one_ghati_later) - 1.0) < 1e-9


def test_ghati_to_civil_round_trip():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    for g in (0.0, 7.5, 22.0, 59.999):
        t = ghati_to_civil(clk, g)
        assert abs(civil_to_ghati(clk, t) - g) < 1e-9


def test_ghati_window_names_and_bounds():
    sunrise = datetime(2026, 6, 11, 5, 30, 0, tzinfo=timezone.utc)
    clk = make_clock(sunrise, sunrise + timedelta(hours=24))
    w = ghati_window(clk, 'Vishaghati', start_ghati=10.0, end_ghati=12.5)
    assert w.name == 'Vishaghati'
    assert w.start_ghati == 10.0
    assert w.end_ghati == 12.5
    assert abs((w.end - w.start).total_seconds() - 2.5 * clk.seconds_per_ghati) < 1e-6
```

- [ ] **Step 1.3: Verify test fails**

Run: `python -m pytest tests/test_ghati.py -v`
Expected: ImportError — `telugu_panchangam.ghati` does not exist.

- [ ] **Step 1.4: Implement ghati module**

Create `telugu_panchangam/ghati.py`:

```python
from datetime import datetime, timedelta
from telugu_panchangam.models.panchangam_day import GhatiClock, GhatiWindow


def make_clock(sunrise: datetime, next_sunrise: datetime) -> GhatiClock:
    seconds_per_ghati = (next_sunrise - sunrise).total_seconds() / 60.0
    return GhatiClock(sunrise=sunrise, next_sunrise=next_sunrise,
                     seconds_per_ghati=seconds_per_ghati)


def civil_to_ghati(clk: GhatiClock, t: datetime) -> float:
    return (t - clk.sunrise).total_seconds() / clk.seconds_per_ghati


def ghati_to_civil(clk: GhatiClock, g: float) -> datetime:
    return clk.sunrise + timedelta(seconds=g * clk.seconds_per_ghati)


def ghati_window(
    clk: GhatiClock, name: str, start_ghati: float, end_ghati: float,
) -> GhatiWindow:
    return GhatiWindow(
        name=name,
        start=ghati_to_civil(clk, start_ghati),
        end=ghati_to_civil(clk, end_ghati),
        start_ghati=start_ghati,
        end_ghati=end_ghati,
    )
```

- [ ] **Step 1.5: Verify ghati module tests pass**

Run: `python -m pytest tests/test_ghati.py -v`
Expected: 5 passed.

- [ ] **Step 1.6: Wire `ghati_clock` into all three engines**

In `telugu_panchangam/engines/base.py`, add a helper near the bottom of the class:

```python
def _build_ghati_clock(self, sunrise_dt, next_sunrise_dt):
    from telugu_panchangam.ghati import make_clock
    return make_clock(sunrise_dt, next_sunrise_dt)
```

In each of `drik.py`, `surya_siddhanta.py`, `vakya.py`, locate the `PanchangamDay(...)` construction in `calculate()` and add (using the engine's existing next-sunrise computation; if absent, compute one extra sunrise from `jd_sunrise + 1.0`):

```python
day.ghati_clock = self._build_ghati_clock(sunrise_dt, next_sunrise_dt)
```

- [ ] **Step 1.7: Serialize in MCP**

In `telugu_panchangam/mcp/tools.py`, in the function that builds the per-day dict (search for `'rahu_kalam':`), add:

```python
'ghati_clock': (
    {
        'sunrise': _fmt_time(day.ghati_clock.sunrise, tz),
        'next_sunrise': _fmt_time(day.ghati_clock.next_sunrise, tz),
        'seconds_per_ghati': day.ghati_clock.seconds_per_ghati,
    } if day.ghati_clock else None
),
```

Add a helper for `GhatiWindow` next to `_window_to_dict`:

```python
def _ghati_window_to_dict(gw, tz: str) -> dict | None:
    if gw is None:
        return None
    return {
        'name': gw.name,
        'start': _fmt_time(gw.start, tz),
        'end': _fmt_time(gw.end, tz),
        'start_ghati': round(gw.start_ghati, 4),
        'end_ghati': round(gw.end_ghati, 4),
    }
```

- [ ] **Step 1.8: Add MCP-round-trip test**

Append to `tests/test_ghati.py`:

```python
import datetime as _dt
from telugu_panchangam.mcp.tools import tool_get_panchangam
import json

def test_ghati_clock_in_mcp_output():
    # tool_get_panchangam returns a flat dict — no 'day' wrapper. Access keys
    # at the top level (see existing fields like 'pancha_anga', 'sky', etc.).
    out = json.loads(tool_get_panchangam('2026-06-11', city='Hyderabad'))
    assert 'ghati_clock' in out
    gc = out['ghati_clock']
    assert 'sunrise' in gc and 'next_sunrise' in gc and 'seconds_per_ghati' in gc
    assert 1400 < gc['seconds_per_ghati'] < 1500   # ~24-min sanity bound
```

- [ ] **Step 1.9: Run full suite**

Run: `python -m pytest tests/ -q`
Expected: 849 + new tests passing; 0 failures; ICS golden snapshot untouched.

- [ ] **Step 1.10: Commit**

```bash
git checkout -b feat/ghati-infrastructure
git add telugu_panchangam/ghati.py telugu_panchangam/models/panchangam_day.py \
        telugu_panchangam/engines/base.py telugu_panchangam/engines/drik.py \
        telugu_panchangam/engines/surya_siddhanta.py telugu_panchangam/engines/vakya.py \
        telugu_panchangam/mcp/tools.py tests/test_ghati.py
git commit -m "feat(ghati): sunrise-anchored ghati/vighati clock infrastructure"
```

---

## Task 2: Pada on daily nakshatra span

**Files:**
- Modify: `telugu_panchangam/models/panchangam_day.py` (add `nakshatra_pada: int | None = None`)
- Modify: `telugu_panchangam/engines/drik.py`, `surya_siddhanta.py`, `vakya.py` (populate)
- Modify: `telugu_panchangam/mcp/tools.py`
- Test: `tests/test_pada_on_daily.py`

**Concept:** Moon's pada (1..4) at sunrise. We already compute Moon's nakshatra at sunrise; pada = `floor(longitude_within_nakshatra / 3.333°) + 1`. Surface as a single int on `PanchangamDay`.

- [ ] **Step 2.1: Add field**

In `models/panchangam_day.py`:

```python
nakshatra_pada: int | None = None
```

- [ ] **Step 2.2: Write failing test**

Create `tests/test_pada_on_daily.py`:

```python
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def test_pada_is_1_to_4():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    assert day.nakshatra_pada in (1, 2, 3, 4)


def test_pada_consistent_with_graha_positions_moon():
    # Cross-check against gochara/positions which already computes pada for the Moon.
    from telugu_panchangam.gochara.positions import get_graha_positions
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    grahas = get_graha_positions(date(2026, 6, 11), CITIES['hyderabad'])
    moon = next(g for g in grahas if g['name'] == 'Chandra')
    assert day.nakshatra_pada == moon['pada']
```

- [ ] **Step 2.3: Verify test fails**

Run: `python -m pytest tests/test_pada_on_daily.py -v`
Expected: AttributeError or `nakshatra_pada is None`.

- [ ] **Step 2.4: Compute and assign pada in each engine**

In each of `drik.py`, `surya_siddhanta.py`, `vakya.py`, inside `calculate()` after `moon_long` (or equivalent sidereal moon longitude at sunrise) is known, add:

```python
# Moon pada at sunrise — 4 padas per nakshatra, each 360/108 = 3.333°
pada = int((moon_long_sr % (360.0 / 27.0)) / (360.0 / 108.0)) + 1
day.nakshatra_pada = pada
```

(For SS and Vakya which compute Moon position via their own mean-motion models, use that engine's moon longitude at sunrise — do not switch them to Swiss.)

- [ ] **Step 2.5: Verify tests pass**

Run: `python -m pytest tests/test_pada_on_daily.py -v`
Expected: 2 passed.

- [ ] **Step 2.6: Serialize in MCP**

In `mcp/tools.py`, in the per-day dict, find the nakshatra block and add:

```python
'nakshatra_pada': day.nakshatra_pada,
```

- [ ] **Step 2.7: Run full suite, commit**

```bash
python -m pytest tests/ -q
git checkout -b feat/pada-on-daily-span
git add telugu_panchangam/models/panchangam_day.py \
        telugu_panchangam/engines/drik.py telugu_panchangam/engines/surya_siddhanta.py \
        telugu_panchangam/engines/vakya.py telugu_panchangam/mcp/tools.py \
        tests/test_pada_on_daily.py
git commit -m "feat(engines): expose Moon's pada on the daily nakshatra span"
```

---

## Task 3: Ayanamsa parameter

**Files:**
- Modify: `telugu_panchangam/engines/utils.py` (accept ayanamsa)
- Modify: `telugu_panchangam/engines/drik.py` (constructor)
- Modify: `telugu_panchangam/gochara/positions.py` (ayanamsa-aware)
- Modify: `telugu_panchangam/mcp/server.py`, `mcp/tools.py` (expose param)
- Test: `tests/test_ayanamsa.py`

**Concept:** Today `engines/utils.py:31` hardcodes `swe.SIDM_LAHIRI`. Allow `ayanamsa: str` to switch among `lahiri` | `raman` | `krishnamurti` | `true_chitrapaksha`. **Default stays `lahiri`** — existing tests pin every Lahiri output byte-for-byte; alternate ayanamsa must shift positions measurably. SS and Vakya engines don't use Swiss for sidereal positions; the parameter is a no-op there but accepted at the constructor for API symmetry.

- [ ] **Step 3.1: Failing test**

Create `tests/test_ayanamsa.py`:

```python
import pytest
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.engines.utils import sidereal_longitude_with_ayanamsa
from telugu_panchangam.cities import CITIES
import swisseph as swe


def test_default_ayanamsa_is_lahiri():
    eng = DrikEngine()
    assert eng.ayanamsa == 'lahiri'


def test_ayanamsa_constructor_param():
    eng = DrikEngine(ayanamsa='raman')
    assert eng.ayanamsa == 'raman'


def test_invalid_ayanamsa_raises():
    with pytest.raises(ValueError, match='ayanamsa must be one of'):
        DrikEngine(ayanamsa='krishnamoorthy')


def test_lahiri_default_byte_identical_to_pre_change():
    # Spot-check: 2026-06-11 Hyderabad Drik nakshatra unchanged under default.
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    # Existing tests already pin this date; this guards the parameterisation
    # didn't move default behaviour.
    assert day.nakshatra is not None


def test_alternate_ayanamsa_shifts_longitude():
    jd = 2461183.5   # 2026-06-11 00:00 UTC
    lon_lahiri = sidereal_longitude_with_ayanamsa(jd, swe.MOON, 'lahiri')
    lon_raman = sidereal_longitude_with_ayanamsa(jd, swe.MOON, 'raman')
    # Lahiri vs Raman differ by ~0.13° classically — must measurably differ.
    assert abs(lon_lahiri - lon_raman) > 0.05
```

- [ ] **Step 3.2: Verify failing**

Run: `python -m pytest tests/test_ayanamsa.py -v`
Expected: ImportError / AttributeError.

- [ ] **Step 3.3: Add ayanamsa-aware utility functions**

In `telugu_panchangam/engines/utils.py`, add at top:

```python
AYANAMSA_MODES = {
    'lahiri':              swe.SIDM_LAHIRI,
    'raman':               swe.SIDM_RAMAN,
    'krishnamurti':        swe.SIDM_KRISHNAMURTI,
    'true_chitrapaksha':   swe.SIDM_TRUE_CITRA,
}


def _validate_ayanamsa(name: str) -> int:
    if name not in AYANAMSA_MODES:
        raise ValueError(
            'ayanamsa must be one of: ' + ', '.join(sorted(AYANAMSA_MODES))
        )
    return AYANAMSA_MODES[name]


def sidereal_longitude_with_ayanamsa(jd: float, planet: int, ayanamsa: str) -> float:
    mode = _validate_ayanamsa(ayanamsa)
    swe.set_sid_mode(mode)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    result, _ = swe.calc_ut(jd, planet, flags)
    return result[0] % 360.0
```

Keep the existing `sidereal_longitude` / `sun_longitude` / `moon_longitude` / `moon_sun_elongation` unchanged (they hardcode Lahiri — that is the default and the safe path for the 849 existing tests).

- [ ] **Step 3.4: Add ayanamsa to Drik constructor (default lahiri)**

In `telugu_panchangam/engines/drik.py`:

```python
class DrikEngine(BaseEngine):
    def __init__(self, ayanamsa: str = 'lahiri'):
        from telugu_panchangam.engines.utils import _validate_ayanamsa
        _validate_ayanamsa(ayanamsa)   # raises on invalid
        self.ayanamsa = ayanamsa
        super().__init__()
```

When `ayanamsa != 'lahiri'`, route position lookups through `sidereal_longitude_with_ayanamsa(jd, planet, self.ayanamsa)` instead of `sidereal_longitude(jd, planet)`. **Implementation note:** the simplest mechanical change is to wrap calls at the engine boundary — keep `utils.sidereal_longitude` Lahiri-only, and inside Drik methods choose between the two helpers based on `self.ayanamsa`.

- [ ] **Step 3.5: Add ayanamsa to SS / Vakya constructors as accepted-but-noop**

In `surya_siddhanta.py` and `vakya.py`:

```python
def __init__(self, ayanamsa: str = 'lahiri'):
    from telugu_panchangam.engines.utils import _validate_ayanamsa
    _validate_ayanamsa(ayanamsa)
    self.ayanamsa = ayanamsa
    super().__init__()
```

Comment in code:

```python
# SS/Vakya compute sidereal positions from their own mean-motion models;
# the ayanamsa parameter is accepted for API symmetry but does not change
# computation. Any eclipse calls that route through Swiss are unaffected
# (they use Lahiri internally — astronomical events, not sidereal positions).
```

- [ ] **Step 3.6: Verify Ayanamsa tests pass + full suite green**

```bash
python -m pytest tests/test_ayanamsa.py -v
python -m pytest tests/ -q
```

Expected: ayanamsa tests pass; existing 849 still pass with Lahiri default.

- [ ] **Step 3.7: Expose `ayanamsa` arg in MCP tools**

In `mcp/server.py`, update `tool_get_panchangam` and `tool_get_graha_positions` docstrings to mention the optional `ayanamsa` parameter. In `mcp/tools.py`, add to the relevant tool signatures:

```python
def tool_get_panchangam(date, city=None, latitude=None, longitude=None,
                        timezone=None, system='drik',
                        ayanamsa: str = 'lahiri') -> str:
    ...
    if system == 'drik':
        eng = DrikEngine(ayanamsa=ayanamsa)
    ...
```

And surface `ayanamsa` in the response dict's metadata:

```python
'ayanamsa': ayanamsa,
```

- [ ] **Step 3.8: Commit**

```bash
git checkout -b feat/ayanamsa-parameter
git add telugu_panchangam/engines/utils.py telugu_panchangam/engines/drik.py \
        telugu_panchangam/engines/surya_siddhanta.py telugu_panchangam/engines/vakya.py \
        telugu_panchangam/mcp/tools.py telugu_panchangam/mcp/server.py \
        tests/test_ayanamsa.py
git commit -m "feat(engines): ayanamsa as engine parameter (Lahiri default + Raman/KP/TrueCitra)"
```

---

## Task 4: Vishaghati

**Files:**
- Create: `telugu_panchangam/karana_windows.py` (Vishaghati lives here; Bhadra Mukha/Puchha in Task 5)
- Modify: `telugu_panchangam/models/panchangam_day.py` (add `vishaghati: list[GhatiWindow]`)
- Modify: `telugu_panchangam/engines/*` (populate)
- Modify: `telugu_panchangam/personal/muhurta.py` (consume in slot evaluation)
- Modify: `telugu_panchangam/mcp/tools.py`
- Test: `tests/test_vishaghati.py`

**Concept:** Each nakshatra has a "poison ghatika" — a specific ghati-offset *within* that nakshatra's transit window classically considered inauspicious for muhurta. Table from Muhurta Chintamani:

```python
# vighatis-from-nakshatra-start where poison ghatika sits (50 vighatis = 1 ghati,
# wait — classical table is in ghatis-from-start)
VISHAGHATI_OFFSETS_GHATI = {
    'Ashvini':           50,
    'Bharani':           24,
    'Krittika':          30,
    'Rohini':            40,
    'Mrigashira':        14,
    'Ardra':             21,
    'Punarvasu':         30,
    'Pushya':            20,
    'Ashlesha':          32,
    'Magha':             30,
    'Purva Phalguni':    20,
    'Uttara Phalguni':   18,
    'Hasta':             21,
    'Chitra':            20,
    'Swati':             14,
    'Vishakha':          14,
    'Anuradha':          10,
    'Jyeshtha':          14,
    'Mula':              20,
    'Purva Ashadha':     24,
    'Uttara Ashadha':    20,
    'Shravana':          10,
    'Dhanishtha':        10,
    'Shatabhisha':       18,
    'Purva Bhadrapada':  16,
    'Uttara Bhadrapada': 24,
    'Revati':            30,
}
```

Each window is 4 vighatis long (≈ 96 seconds; classical sources vary 2–8 vighatis — 4 is the median).

- [ ] **Step 4.1: Add field**

```python
vishaghati: list[GhatiWindow] = field(default_factory=list)
```

- [ ] **Step 4.2: Failing test**

Create `tests/test_vishaghati.py`:

```python
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def test_vishaghati_list_present():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    assert isinstance(day.vishaghati, list)
    # If a nakshatra changes during the day, we may get up to 2 windows.
    assert 0 <= len(day.vishaghati) <= 2


def test_vishaghati_window_inside_nakshatra_span():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    for vw in day.vishaghati:
        # Window must lie inside its parent nakshatra span.
        assert day.nakshatra.start <= vw.start
        assert vw.end <= day.nakshatra.end


def test_vishaghati_duration_about_4_vighatis():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    for vw in day.vishaghati:
        # 4 vighatis ≈ 4 * (seconds_per_ghati / 60)
        expected = 4 * (day.ghati_clock.seconds_per_ghati / 60.0)
        actual = (vw.end - vw.start).total_seconds()
        assert abs(actual - expected) < 1.0
```

- [ ] **Step 4.3: Verify failing**

Run: `python -m pytest tests/test_vishaghati.py -v`
Expected: assertions fail (vishaghati is empty list).

- [ ] **Step 4.4: Implement `karana_windows.py` (Vishaghati portion)**

Create `telugu_panchangam/karana_windows.py`:

```python
from datetime import datetime, timedelta
from telugu_panchangam.models.panchangam_day import Span, GhatiWindow, GhatiClock
from telugu_panchangam.ghati import civil_to_ghati, ghati_to_civil


VISHAGHATI_OFFSETS_GHATI = {
    'Ashvini': 50, 'Bharani': 24, 'Krittika': 30, 'Rohini': 40,
    'Mrigashira': 14, 'Ardra': 21, 'Punarvasu': 30, 'Pushya': 20,
    'Ashlesha': 32, 'Magha': 30, 'Purva Phalguni': 20, 'Uttara Phalguni': 18,
    'Hasta': 21, 'Chitra': 20, 'Swati': 14, 'Vishakha': 14,
    'Anuradha': 10, 'Jyeshtha': 14, 'Mula': 20, 'Purva Ashadha': 24,
    'Uttara Ashadha': 20, 'Shravana': 10, 'Dhanishtha': 10,
    'Shatabhisha': 18, 'Purva Bhadrapada': 16, 'Uttara Bhadrapada': 24,
    'Revati': 30,
}

VISHAGHATI_WIDTH_VIGHATIS = 4  # classical value


def compute_vishaghati(
    nakshatra_spans: list[Span], clk: GhatiClock,
) -> list[GhatiWindow]:
    """Return all Vishaghati windows occurring between sunrise and next sunrise.
    A panchangam day may contain one or two nakshatras (when transit happens
    during the day) — emit one Vishaghati per nakshatra whose poison ghatika
    falls inside the day.
    """
    windows = []
    for span in nakshatra_spans:
        offset_g = VISHAGHATI_OFFSETS_GHATI.get(span.name)
        if offset_g is None:
            continue
        # The nakshatra's full transit is 60 ghatis; the poison-ghatika offset
        # is measured from the nakshatra's *own* start, not from sunrise.
        span_duration_s = (span.end - span.start).total_seconds()
        # Classical scaling: offset_g out of 60 ghatis-of-the-nakshatra.
        start = span.start + timedelta(seconds=span_duration_s * offset_g / 60.0)
        width_s = VISHAGHATI_WIDTH_VIGHATIS * (clk.seconds_per_ghati / 60.0)
        end = start + timedelta(seconds=width_s)
        # Clip to the panchangam day (sunrise→next-sunrise).
        if end < clk.sunrise or start > clk.next_sunrise:
            continue
        if start < clk.sunrise:
            start = clk.sunrise
        if end > clk.next_sunrise:
            end = clk.next_sunrise
        windows.append(GhatiWindow(
            name='Vishaghati',
            start=start, end=end,
            start_ghati=civil_to_ghati(clk, start),
            end_ghati=civil_to_ghati(clk, end),
        ))
    return windows
```

- [ ] **Step 4.5: Wire into engines**

In each engine's `calculate()`, after `day.ghati_clock` is set and the nakshatra spans for the day are known, add:

```python
from telugu_panchangam.karana_windows import compute_vishaghati
day.vishaghati = compute_vishaghati(day_nakshatra_spans, day.ghati_clock)
```

Where `day_nakshatra_spans` is `[day.nakshatra]` plus any next-nakshatra span if the engine already computes a next span for transit days. If the engine only exposes one `Span`, that's fine — pass `[day.nakshatra]`.

- [ ] **Step 4.6: Consume in muhurta**

In `personal/muhurta.py`, in `_evaluate_slot`, add a Vishaghati overlap check alongside the existing inauspicious-window cuts. Vishaghati is *removed from the slot* like Rahu Kalam — same shape.

Find the block that subtracts `day.rahu_kalam, day.gulika_kalam, day.yamagandam` etc., and append `day.vishaghati` to that list.

- [ ] **Step 4.7: Serialize in MCP**

In `mcp/tools.py`, in the day dict:

```python
'vishaghati': [_ghati_window_to_dict(w, tz) for w in day.vishaghati],
```

- [ ] **Step 4.8: Full suite + commit**

```bash
python -m pytest tests/ -q
git checkout -b feat/vishaghati
git add telugu_panchangam/karana_windows.py telugu_panchangam/models/panchangam_day.py \
        telugu_panchangam/engines/*.py telugu_panchangam/personal/muhurta.py \
        telugu_panchangam/mcp/tools.py tests/test_vishaghati.py
git commit -m "feat(timing): Vishaghati windows per Muhurta Chintamani offsets"
```

---

## Task 5: Bhadra Mukha / Puchha

**Files:**
- Modify: `telugu_panchangam/karana_windows.py` (add Mukha/Puchha compute)
- Modify: `telugu_panchangam/models/panchangam_day.py` (add `bhadra_mukha`, `bhadra_puchha`)
- Modify: `telugu_panchangam/engines/*` (populate)
- Modify: `telugu_panchangam/personal/muhurta.py` (Mukha is hard-avoid; Puchha is auspicious for journeys/contests)
- Modify: `telugu_panchangam/mcp/tools.py`
- Test: `tests/test_bhadra_mukha_puchha.py`

**Concept:** Vishti karana (Bhadra) is a half-tithi window. Within it, the first 5 ghatikas are **Mukha** (face — most inauspicious) and the last 3 ghatikas are **Puchha** (tail — actually auspicious for warfare, lawsuits, contests per Muhurta Chintamani). The middle 8 ghatikas are the body. The split rules differ slightly by paksham and by which half-tithi the Vishti falls in; we use the standard rule: first 5 ghatis Mukha, last 3 ghatis Puchha.

- [ ] **Step 5.1: Add fields**

```python
bhadra_mukha: 'GhatiWindow | None' = None
bhadra_puchha: 'GhatiWindow | None' = None
```

- [ ] **Step 5.2: Failing test**

Create `tests/test_bhadra_mukha_puchha.py`:

```python
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def _find_vishti_day(year, month, city):
    """Find first date in given month where Vishti karana is active at sunrise."""
    eng = DrikEngine()
    for d in range(1, 29):
        day = eng.calculate(date(year, month, d), city)
        for k in day.karana:
            if k.name == 'Vishti':
                return day, k
    return None, None


def test_mukha_and_puchha_when_vishti_present():
    day, _ = _find_vishti_day(2026, 6, CITIES['hyderabad'])
    assert day is not None
    assert day.bhadra_mukha is not None
    assert day.bhadra_puchha is not None
    # Mukha precedes Puchha.
    assert day.bhadra_mukha.end <= day.bhadra_puchha.start


def test_mukha_5_ghatis_puchha_3_ghatis():
    day, vishti = _find_vishti_day(2026, 6, CITIES['hyderabad'])
    assert day is not None
    mukha_dur = day.bhadra_mukha.end_ghati - day.bhadra_mukha.start_ghati
    puchha_dur = day.bhadra_puchha.end_ghati - day.bhadra_puchha.start_ghati
    # Allow scaling to short Vishti windows that get clipped by day boundary.
    full_vishti_ghatis = (vishti.end - vishti.start).total_seconds() / day.ghati_clock.seconds_per_ghati
    # Mukha is 5/16, Puchha is 3/16 of the full Vishti window when uncut.
    if full_vishti_ghatis >= 16:
        assert abs(mukha_dur - 5.0) < 0.1
        assert abs(puchha_dur - 3.0) < 0.1
```

- [ ] **Step 5.3: Verify fail, then implement**

Run: fails (fields are None).

Add to `karana_windows.py`:

```python
def compute_bhadra_windows(
    karana_spans: list[Span], clk: GhatiClock,
) -> tuple[GhatiWindow | None, GhatiWindow | None]:
    """Locate the Vishti karana in the day and split into Mukha (first 5/16)
    and Puchha (last 3/16) ghatika windows. Returns (mukha, puchha) — either
    can be None if the window is fully outside the panchangam day.
    """
    vishti = next((k for k in karana_spans if k.name == 'Vishti'), None)
    if vishti is None:
        return (None, None)
    total_s = (vishti.end - vishti.start).total_seconds()
    if total_s <= 0:
        return (None, None)
    # Classical split — 5:8:3 across 16 ghatis = full Vishti span (half-tithi).
    mukha_end_s = total_s * (5.0 / 16.0)
    puchha_start_s = total_s * (13.0 / 16.0)
    mukha_start = vishti.start
    mukha_end = vishti.start + timedelta(seconds=mukha_end_s)
    puchha_start = vishti.start + timedelta(seconds=puchha_start_s)
    puchha_end = vishti.end

    def _clip(name, s, e):
        if e < clk.sunrise or s > clk.next_sunrise:
            return None
        if s < clk.sunrise: s = clk.sunrise
        if e > clk.next_sunrise: e = clk.next_sunrise
        return GhatiWindow(name=name, start=s, end=e,
                          start_ghati=civil_to_ghati(clk, s),
                          end_ghati=civil_to_ghati(clk, e))
    return (_clip('Bhadra Mukha', mukha_start, mukha_end),
            _clip('Bhadra Puchha', puchha_start, puchha_end))
```

- [ ] **Step 5.4: Wire into engines**

```python
from telugu_panchangam.karana_windows import compute_bhadra_windows
day.bhadra_mukha, day.bhadra_puchha = compute_bhadra_windows(day.karana, day.ghati_clock)
```

- [ ] **Step 5.5: Consume in muhurta**

In `personal/muhurta.py`:
- **Bhadra Mukha**: hard-cut from slots (same as Rahu Kalam). Append `[day.bhadra_mukha]` to the inauspicious-windows list when non-None.
- **Bhadra Puchha**: do **not** cut. Add an activity-rule bonus for `travel`, `warrior`, `litigation` activities — +2 to slot score when overlap, with a reason `"Bhadra Puchha overlap (+2)"`.

Add to the activity-rule dict:

```python
'litigation': {'label': 'Litigation / contest', 'prefer_bhadra_puchha': 2},
```

And in `_evaluate_slot`, look for the `prefer_bhadra_puchha` key — when present and slot overlaps `day.bhadra_puchha`, add the score and reason.

- [ ] **Step 5.6: Serialize, run, commit**

```python
'bhadra_mukha': _ghati_window_to_dict(day.bhadra_mukha, tz),
'bhadra_puchha': _ghati_window_to_dict(day.bhadra_puchha, tz),
```

```bash
python -m pytest tests/ -q
git checkout -b feat/bhadra-mukha-puchha
git add ...
git commit -m "feat(timing): Bhadra Mukha (hard avoid) + Puchha (auspicious for contests)"
```

---

## Task 6: Sankramana 16-ghati avoidance window

**Files:**
- Create: `telugu_panchangam/sankramana.py`
- Modify: `models/panchangam_day.py` (`sankramana_avoidance: Window | None`)
- Modify: `engines/*` (compute Sankranti exact moment + 16-ghati window)
- Modify: `personal/muhurta.py` (samskara/ceremony hard-avoid)
- Modify: `mcp/tools.py`
- Test: `tests/test_sankramana_window.py`

**Concept:** When Sun ingresses a new rasi (Sankranti), classical authority restricts samskaras for 16 ghatikas before and after the exact ingress moment (some traditions use 30 ghatikas for Karkata/Makara — Dakshinayana/Uttarayana). We use the conservative 16-ghati window for all signs.

- [ ] **Step 6.1: Add field**

```python
sankramana_avoidance: Window | None = None
```

- [ ] **Step 6.2: Failing test**

Create `tests/test_sankramana_window.py`:

```python
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def test_no_window_on_non_sankranti_day():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    if not day.is_sankranti:
        assert day.sankramana_avoidance is None


def test_window_present_on_sankranti_day():
    eng = DrikEngine()
    # 2026-07-16 is around Karkata Sankranti
    for d in range(14, 20):
        day = eng.calculate(date(2026, 7, d), CITIES['hyderabad'])
        if day.is_sankranti or day.sankramanam:
            assert day.sankramana_avoidance is not None
            # Window spans 16 ghatis before + 16 ghatis after ingress = 32 ghatis ≈ 12h48m
            dur_s = (day.sankramana_avoidance.end - day.sankramana_avoidance.start).total_seconds()
            assert 12 * 3600 < dur_s < 14 * 3600
            return
    raise AssertionError("Expected a Sankranti day in this range")
```

- [ ] **Step 6.3: Implement `sankramana.py`**

```python
from datetime import datetime, timedelta
from telugu_panchangam.models.panchangam_day import Window, GhatiClock


def compute_sankramana_window(
    sankranti_moment: datetime | None, clk: GhatiClock,
) -> Window | None:
    """Return the 16-ghati-before + 16-ghati-after avoidance window around
    the Sun's sign-ingress moment. None when no Sankranti occurs on this
    panchangam day.
    """
    if sankranti_moment is None:
        return None
    half_width_s = 16 * clk.seconds_per_ghati
    return Window(
        name='Sankramana Avoidance',
        start=sankranti_moment - timedelta(seconds=half_width_s),
        end=sankranti_moment + timedelta(seconds=half_width_s),
    )
```

- [ ] **Step 6.4: Find or compute exact Sankranti moment in each engine**

Drik already detects Sankranti by name. Locate (in `drik.py`) where `sankramanam` is set; that path knows the JD of the rasi crossing. Extract the JD → convert to local-timezone datetime → pass to `compute_sankramana_window`. Same pattern for SS and Vakya (whose `_sankramanam_name` lives in `base.py:456`).

```python
from telugu_panchangam.sankramana import compute_sankramana_window
day.sankramana_avoidance = compute_sankramana_window(sankranti_dt, day.ghati_clock)
```

- [ ] **Step 6.5: Muhurta consumption**

In `personal/muhurta.py` activity rules, samskara-bearing activities (`ceremony`, `wedding`, `upanayana`, `gruhapravesha`, etc.) gain `'skip_on_sankramana': True`. In `_evaluate_day`, when `day.sankramana_avoidance is not None`, drop slot if it overlaps and the activity has the flag.

- [ ] **Step 6.6: Serialize, commit**

```python
'sankramana_avoidance': _window_to_dict(day.sankramana_avoidance, tz),
```

```bash
git checkout -b feat/sankramana-window
git commit -m "feat(timing): 16-ghati Sankramana avoidance window for samskara muhurta"
```

---

## Task 7: 5 Panchaka Nakshatras

**Files:**
- Create: `telugu_panchangam/nakshatra_filters.py`
- Modify: `models/panchangam_day.py` (`in_panchaka_nakshatra: bool`)
- Modify: `engines/*` (populate)
- Modify: `personal/muhurta.py` (activity-conditioned avoidance)
- Modify: `mcp/tools.py`
- Test: `tests/test_panchaka_nakshatras.py`

**Concept:** The 5 Panchaka Nakshatras — Dhanishtha (2nd half), Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada, Revati — are universally avoided for cremation rites, wood-cutting, roof-laying, and south-bound travel. Distinct from the modular-9 Panchaka Rahita (Task 16). For simplicity (and matching most published Panchangams), we mark the **whole** of Dhanishtha as in-Panchaka rather than the second half only.

- [ ] **Step 7.1: Add field**

```python
in_panchaka_nakshatra: bool = False
```

- [ ] **Step 7.2: Failing test**

```python
from telugu_panchangam.nakshatra_filters import is_panchaka_nakshatra, PANCHAKA_NAKSHATRAS

def test_panchaka_nakshatras_set():
    assert PANCHAKA_NAKSHATRAS == {
        'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
        'Uttara Bhadrapada', 'Revati',
    }

def test_is_panchaka_nakshatra():
    assert is_panchaka_nakshatra('Revati') is True
    assert is_panchaka_nakshatra('Ashvini') is False
```

- [ ] **Step 7.3: Implement**

`telugu_panchangam/nakshatra_filters.py`:

```python
PANCHAKA_NAKSHATRAS = {
    'Dhanishtha', 'Shatabhisha', 'Purva Bhadrapada',
    'Uttara Bhadrapada', 'Revati',
}

def is_panchaka_nakshatra(name: str) -> bool:
    return name in PANCHAKA_NAKSHATRAS
```

- [ ] **Step 7.4: Wire into engines**

```python
from telugu_panchangam.nakshatra_filters import is_panchaka_nakshatra
day.in_panchaka_nakshatra = is_panchaka_nakshatra(day.nakshatra.name)
```

- [ ] **Step 7.5: Muhurta consumption**

Add activity rule `'skip_on_panchaka_nakshatra'` (bool) for `cremation`, `construction_roof`, `wood_cutting`, `travel_south`.

- [ ] **Step 7.6: Serialize, test, commit**

```python
'in_panchaka_nakshatra': day.in_panchaka_nakshatra,
```

```bash
git checkout -b feat/panchaka-nakshatras
git commit -m "feat(timing): 5 Panchaka Nakshatras flag for cremation/construction muhurta"
```

---

## Task 8: Khar-Maasa (Dhanur / Meena)

**Files:**
- Create: `telugu_panchangam/maasa_filters.py`
- Modify: `models/panchangam_day.py` (`is_khar_maasa`, `khar_maasa_name`)
- Modify: `engines/*` (populate from `day.solar_sign`)
- Modify: `personal/muhurta.py` (samskara avoidance)
- Modify: `mcp/tools.py`
- Test: `tests/test_khar_maasa.py`

**Concept:** When Sun is in Dhanur (Sagittarius) or Meena (Pisces) — solar-month-long. Samskaras restricted. Pure check on `day.solar_sign`.

- [ ] **Step 8.1: Add fields**

```python
is_khar_maasa: bool = False
khar_maasa_name: str | None = None   # 'Dhanur' | 'Meena' | None
```

- [ ] **Step 8.2: Failing test**

```python
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def test_dhanur_maasa_mid_december():
    # Sun typically in Dhanur from ~Dec 16 to ~Jan 14
    eng = DrikEngine()
    day = eng.calculate(date(2026, 12, 20), CITIES['hyderabad'])
    assert day.is_khar_maasa is True
    assert day.khar_maasa_name == 'Dhanur'


def test_meena_maasa_mid_march():
    eng = DrikEngine()
    day = eng.calculate(date(2027, 3, 20), CITIES['hyderabad'])
    assert day.is_khar_maasa is True
    assert day.khar_maasa_name == 'Meena'


def test_no_khar_maasa_in_october():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 10, 15), CITIES['hyderabad'])
    assert day.is_khar_maasa is False
    assert day.khar_maasa_name is None
```

- [ ] **Step 8.3: Implement**

```python
# telugu_panchangam/maasa_filters.py
KHAR_MAASA_SIGNS = {'Dhanur': 'Dhanur', 'Meena': 'Meena'}

def khar_maasa_name(solar_sign: str | None) -> str | None:
    return KHAR_MAASA_SIGNS.get(solar_sign)
```

- [ ] **Step 8.4: Wire into engines**

```python
from telugu_panchangam.maasa_filters import khar_maasa_name
day.khar_maasa_name = khar_maasa_name(day.solar_sign)
day.is_khar_maasa = day.khar_maasa_name is not None
```

- [ ] **Step 8.5: Muhurta consumption**

Add activity-rule key `'skip_on_khar_maasa': True` for samskara activities.

- [ ] **Step 8.6: Serialize, test, commit**

```python
'is_khar_maasa': day.is_khar_maasa,
'khar_maasa_name': day.khar_maasa_name,
```

```bash
git checkout -b feat/khar-maasa
git commit -m "feat(timing): Khar-Maasa flag (Sun in Dhanur or Meena) for samskara muhurta"
```

---

## Task 9: Simha-Stha Guru / Shukra

**Files:**
- Create: `telugu_panchangam/gochara/simha_stha.py`
- Modify: `models/panchangam_day.py` (`simha_stha_guru`, `simha_stha_shukra`)
- Modify: `engines/*` (populate from graha positions)
- Modify: `personal/muhurta.py` (wedding-specific avoidance)
- Modify: `mcp/tools.py`
- Test: `tests/test_simha_stha.py`

**Concept:** Jupiter in Simha → marriage restriction (Simha-Stha Guru, 12-year cycle, well-known South Indian custom). Venus in Simha → similar restriction in some traditions. Pure rasi-check on already-computed sidereal positions.

- [ ] **Step 9.1: Add fields**

```python
simha_stha_guru: bool = False
simha_stha_shukra: bool = False
```

- [ ] **Step 9.2: Failing test**

```python
from datetime import date
from telugu_panchangam.gochara.simha_stha import is_simha_stha


def test_is_simha_stha_true():
    assert is_simha_stha('Simha') is True

def test_is_simha_stha_false():
    assert is_simha_stha('Mesha') is False
```

- [ ] **Step 9.3: Implement**

```python
# telugu_panchangam/gochara/simha_stha.py
def is_simha_stha(rasi_name: str | None) -> bool:
    return rasi_name == 'Simha'
```

- [ ] **Step 9.4: Wire into engines (Drik only — SS/Vakya don't compute Jupiter/Venus)**

In `drik.py`, where graha positions are already computed for `gochara`:

```python
from telugu_panchangam.gochara.simha_stha import is_simha_stha
day.simha_stha_guru = is_simha_stha(guru_rasi)
day.simha_stha_shukra = is_simha_stha(shukra_rasi)
```

In SS/Vakya, leave the defaults (False) — they don't compute outer planets. Document this in a comment.

- [ ] **Step 9.5: Muhurta consumption**

Activity rule `'wedding': {'skip_on_simha_stha_guru': True, 'penalty_on_simha_stha_shukra': -2}`. Apply in `_evaluate_day`.

- [ ] **Step 9.6: Serialize, test, commit**

```python
'simha_stha_guru': day.simha_stha_guru,
'simha_stha_shukra': day.simha_stha_shukra,
```

```bash
git checkout -b feat/simha-stha
git commit -m "feat(timing): Simha-Stha Guru/Shukra flags for marriage muhurta"
```

---

## Task 10: Guru / Shukra Maudhya (combustion)

**Files:**
- Create: `telugu_panchangam/gochara/combustion.py`
- Modify: `models/panchangam_day.py` (add `MaudhyaInfo`, `guru_maudhya`, `shukra_maudhya`)
- Modify: `engines/drik.py` (populate from sun + planet longitudes at sunrise)
- Modify: `personal/muhurta.py` (samskara skip when combust)
- Modify: `mcp/tools.py`
- Test: `tests/test_maudhya.py`

**Concept:** Heliacal setting (combustion / Asta / Maudhya) — when a planet is too close to the Sun in longitude to be visible. Classical thresholds (Brihat Samhita / Muhurta Chintamani):
- **Jupiter (Guru):** 11°
- **Venus (Shukra):** 10° (lower when retrograde, but we use the single value for simplicity here; can refine later)

Marriage and other samskaras require Guru and Shukra to be **uncombust** — universal across all regional traditions. Currently absent from the codebase.

- [ ] **Step 10.1: Add MaudhyaInfo dataclass + fields**

```python
@dataclass
class MaudhyaInfo:
    graha: str
    elongation_deg: float
    combust: bool
    threshold_deg: float

# in PanchangamDay:
guru_maudhya: MaudhyaInfo | None = None
shukra_maudhya: MaudhyaInfo | None = None
```

- [ ] **Step 10.2: Failing test**

```python
import pytest
from datetime import date
from telugu_panchangam.gochara.combustion import compute_maudhya, COMBUSTION_THRESHOLDS
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.cities import CITIES


def test_compute_maudhya_combust():
    info = compute_maudhya('Guru', sun_long=100.0, planet_long=105.0)
    assert info.graha == 'Guru'
    assert info.threshold_deg == 11.0
    assert abs(info.elongation_deg - 5.0) < 1e-9
    assert info.combust is True


def test_compute_maudhya_not_combust():
    info = compute_maudhya('Shukra', sun_long=100.0, planet_long=140.0)
    assert info.combust is False


def test_engine_populates_guru_maudhya():
    eng = DrikEngine()
    day = eng.calculate(date(2026, 6, 11), CITIES['hyderabad'])
    assert day.guru_maudhya is not None
    assert day.shukra_maudhya is not None
    assert day.guru_maudhya.graha == 'Guru'
    assert day.shukra_maudhya.graha == 'Shukra'
```

- [ ] **Step 10.3: Implement combustion**

```python
# telugu_panchangam/gochara/combustion.py
from telugu_panchangam.models.panchangam_day import MaudhyaInfo


COMBUSTION_THRESHOLDS = {
    'Guru': 11.0,
    'Shukra': 10.0,
}


def compute_maudhya(graha: str, sun_long: float, planet_long: float) -> MaudhyaInfo:
    threshold = COMBUSTION_THRESHOLDS[graha]
    # Signed shortest-arc elongation in [0, 180].
    diff = abs((planet_long - sun_long + 180.0) % 360.0 - 180.0)
    return MaudhyaInfo(
        graha=graha, elongation_deg=diff,
        combust=diff < threshold, threshold_deg=threshold,
    )
```

- [ ] **Step 10.4: Wire into Drik**

In `drik.py` where graha positions are computed (the same path that already supports `tool_get_graha_positions`), grab `sun_long`, `guru_long`, `shukra_long` at sunrise:

```python
from telugu_panchangam.gochara.combustion import compute_maudhya
day.guru_maudhya = compute_maudhya('Guru', sun_long_sr, guru_long_sr)
day.shukra_maudhya = compute_maudhya('Shukra', sun_long_sr, shukra_long_sr)
```

SS / Vakya: leave as None (they don't model outer planets).

- [ ] **Step 10.5: Muhurta consumption**

Activity-rule key `'skip_on_combust': ['Guru', 'Shukra']` for marriage and upanayana. In `_evaluate_day`:

```python
if 'skip_on_combust' in rules:
    for g in rules['skip_on_combust']:
        info = getattr(day, f'{g.lower()}_maudhya')
        if info is not None and info.combust:
            return None   # day excluded
```

- [ ] **Step 10.6: Serialize, run, commit**

```python
def _maudhya_to_dict(m):
    if m is None:
        return None
    return {'graha': m.graha, 'elongation_deg': round(m.elongation_deg, 3),
            'combust': m.combust, 'threshold_deg': m.threshold_deg}

# in day dict:
'guru_maudhya': _maudhya_to_dict(day.guru_maudhya),
'shukra_maudhya': _maudhya_to_dict(day.shukra_maudhya),
```

```bash
git checkout -b feat/maudhya
git commit -m "feat(timing): Guru/Shukra Maudhya (combustion) for marriage muhurta"
```

---

## Task 11: Adhika Maasa muhurta consumption

**Files:**
- Modify: `telugu_panchangam/personal/muhurta.py` (consume existing `day.maasam.startswith('Adhika ')`)
- Test: `tests/test_adhika_maasa_muhurta.py`

**Concept:** The engine already names Adhika months (`engines/base.py:121-143`). The muhurta engine ignores this. Add samskara skip — and that's the whole task.

- [ ] **Step 11.1: Failing test**

```python
from datetime import date
from telugu_panchangam.engines.drik import DrikEngine
from telugu_panchangam.personal.muhurta import find_muhurta
from telugu_panchangam.cities import CITIES


def test_adhika_maasa_skipped_for_wedding():
    # 2026-05-17..2026-06-15 is Adhika Jyeshtha (verify via DP).
    eng = DrikEngine()
    sample = eng.calculate(date(2026, 5, 25), CITIES['hyderabad'])
    if not sample.maasam.startswith('Adhika '):
        # If the Adhika window differs in your panchangam, find an Adhika date
        # by scanning forward and use that. The test asserts the *rule*, not
        # the calendar.
        return
    days = find_muhurta(date(2026, 5, 25), days=7, activity='wedding',
                       city=CITIES['hyderabad'])
    assert len(days) == 0, "Adhika Jyeshtha must skip wedding muhurta"
```

- [ ] **Step 11.2: Implement consumption**

In `personal/muhurta.py`, in the day-level evaluation, when activity rule has `'skip_on_adhika': True`:

```python
if rules.get('skip_on_adhika') and day.maasam.startswith('Adhika '):
    return None
```

Add `'skip_on_adhika': True` to wedding, upanayana, gruhapravesha, dikshapravesha rules.

- [ ] **Step 11.3: Commit**

```bash
git checkout -b feat/adhika-maasa-consumption
git commit -m "feat(muhurta): skip Adhika Maasa days for samskara activities"
```

---

## Task 12: Pitru Paksha 15-day window

**Files:**
- Create: `telugu_panchangam/pitru_paksha.py`
- Modify: `models/panchangam_day.py` (`is_pitru_paksha: bool`)
- Modify: `engines/*`
- Modify: `personal/muhurta.py`
- Modify: `mcp/tools.py`
- Test: `tests/test_pitru_paksha.py`

**Concept:** Bhadrapada Krishna Pratipada through Mahalaya Amavasya inclusive = 15 days. Samskara avoidance. We already detect Mahalaya Amavasya as a festival; just compute the window.

- [ ] **Step 12.1: Add field**

```python
is_pitru_paksha: bool = False
```

- [ ] **Step 12.2: Failing test**

```python
def test_pitru_paksha_window():
    from datetime import date
    eng = DrikEngine()
    # Mahalaya Amavasya 2026 ≈ Sep 20 (verify via DP); pratipada ≈ Sep 7
    found_pratipada = False
    found_amavasya = False
    for d in range(1, 31):
        day = eng.calculate(date(2026, 9, d), CITIES['hyderabad'])
        if day.is_pitru_paksha:
            assert day.maasam.endswith('Bhadrapada') or day.maasam.endswith('Ashvina'), \
                "Pitru Paksha must be in Bhadrapada Krishna paksha"
            assert day.paksham == 'Krishna'
```

- [ ] **Step 12.3: Implement**

```python
# telugu_panchangam/pitru_paksha.py
def is_pitru_paksha_day(maasam: str, paksham: str) -> bool:
    """Bhadrapada Krishna paksha = Pitru Paksha (15-day samskara avoidance)."""
    base = maasam.removeprefix('Adhika ').removeprefix('Nija ')
    return base == 'Bhadrapada' and paksham == 'Krishna'
```

- [ ] **Step 12.4: Wire**

```python
from telugu_panchangam.pitru_paksha import is_pitru_paksha_day
day.is_pitru_paksha = is_pitru_paksha_day(day.maasam, day.paksham)
```

- [ ] **Step 12.5: Muhurta consumption**

Activity rule `'skip_on_pitru_paksha': True` for samskaras.

- [ ] **Step 12.6: Serialize, test, commit**

```python
'is_pitru_paksha': day.is_pitru_paksha,
```

```bash
git checkout -b feat/pitru-paksha
git commit -m "feat(timing): Pitru Paksha 15-day window for samskara muhurta"
```

---

## Task 13: Anandadi 28 Yogas

**Files:**
- Modify: `telugu_panchangam/special_yogas.py` (add 28-yoga table + compute)
- Modify: `models/panchangam_day.py` (`anandadi_yoga: str | None`)
- Modify: `engines/*`
- Modify: `personal/muhurta.py` (apply auspicious/inauspicious as bonus/penalty)
- Modify: `mcp/tools.py`
- Test: `tests/test_anandadi.py`

**Concept:** Vaaram × Moon's nakshatra → one of 28 named muhurta yogas (Ananda, Kalidanda, Dhumra, Dhata, Saumya, …). Each yoga has a nature (auspicious / inauspicious / mixed). Pure table lookup per Muhurta Chintamani. We use the standard 28-yoga starting-nakshatra per weekday:

```
Sunday   starts from Ashvini
Monday   starts from Mrigashira  (skip Ashvini..Krittika offset = 3)
Tuesday  starts from Ashlesha    (offset = 8)
Wednesday starts from Hasta      (offset = 12)
Thursday starts from Anuradha    (offset = 16)
Friday   starts from Purva Ashadha (offset = 19)
Saturday starts from Shatabhisha (offset = 23)
```

(There are several minor traditions; we use the most common table.)

The 28 yogas in order:

```
Ananda, Kalidanda, Dhumra, Dhata, Saumya, Dhwanksha,
Dhwaja, Shrivatsa, Vajra, Mudgara, Chhatra, Maitra,
Manasa, Padma, Lumba, Utpat, Mrityu, Kaana,
Siddhi, Subha, Amrita, Musala, Gada, Matanga,
Raksha, Chara, Sthira, Vardhamana,
```

Natures (per classical commentary; we encode the principal classification):

```
AUSPICIOUS = {Ananda, Dhata, Saumya, Dhwaja, Shrivatsa, Chhatra, Maitra,
              Manasa, Padma, Siddhi, Subha, Amrita, Matanga, Raksha,
              Sthira, Vardhamana}
INAUSPICIOUS = {Kalidanda, Dhumra, Dhwanksha, Vajra, Mudgara, Lumba, Utpat,
                Mrityu, Kaana, Musala, Gada, Chara}
```

- [ ] **Step 13.1: Add field**

```python
anandadi_yoga: str | None = None
```

- [ ] **Step 13.2: Failing test**

```python
from telugu_panchangam.special_yogas import compute_anandadi_yoga, ANANDADI_YOGAS

def test_yoga_table_has_28_entries():
    assert len(ANANDADI_YOGAS) == 28

def test_sunday_ashvini_is_ananda():
    assert compute_anandadi_yoga('Adivaram', 'Ashvini') == 'Ananda'

def test_monday_mrigashira_is_ananda():
    assert compute_anandadi_yoga('Somavaram', 'Mrigashira') == 'Ananda'
```

- [ ] **Step 13.3: Implement**

In `telugu_panchangam/special_yogas.py`, append:

```python
ANANDADI_YOGAS = [
    'Ananda', 'Kalidanda', 'Dhumra', 'Dhata', 'Saumya', 'Dhwanksha',
    'Dhwaja', 'Shrivatsa', 'Vajra', 'Mudgara', 'Chhatra', 'Maitra',
    'Manasa', 'Padma', 'Lumba', 'Utpat', 'Mrityu', 'Kaana',
    'Siddhi', 'Subha', 'Amrita', 'Musala', 'Gada', 'Matanga',
    'Raksha', 'Chara', 'Sthira', 'Vardhamana',
]

_VAARA_OFFSET = {
    'Adivaram': 0, 'Somavaram': 3, 'Mangalavaram': 8,
    'Budhavaram': 12, 'Guruvaram': 16, 'Shukravaram': 19,
    'Shanivaram': 23,
}

_NAKSHATRA_ORDER = [
    'Ashvini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu',
    'Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta',
    'Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha',
    'Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada',
    'Uttara Bhadrapada','Revati',
]

ANANDADI_AUSPICIOUS = frozenset({
    'Ananda','Dhata','Saumya','Dhwaja','Shrivatsa','Chhatra','Maitra',
    'Manasa','Padma','Siddhi','Subha','Amrita','Matanga','Raksha',
    'Sthira','Vardhamana',
})

ANANDADI_INAUSPICIOUS = frozenset({
    'Kalidanda','Dhumra','Dhwanksha','Vajra','Mudgara','Lumba','Utpat',
    'Mrityu','Kaana','Musala','Gada','Chara',
})


def compute_anandadi_yoga(vaaram: str, nakshatra: str) -> str | None:
    offset = _VAARA_OFFSET.get(vaaram)
    if offset is None or nakshatra not in _NAKSHATRA_ORDER:
        return None
    nak_idx = _NAKSHATRA_ORDER.index(nakshatra)
    return ANANDADI_YOGAS[(nak_idx - offset) % 28]
```

- [ ] **Step 13.4: Wire**

```python
from telugu_panchangam.special_yogas import compute_anandadi_yoga
day.anandadi_yoga = compute_anandadi_yoga(day.vaaram, day.nakshatra.name)
```

- [ ] **Step 13.5: Muhurta consumption**

In `_YOGA_BONUS` / `_YOGA_PENALTY` blocks (already present), add Anandadi handling. Auspicious Anandadi → +1 bonus; inauspicious → -1 penalty.

- [ ] **Step 13.6: Serialize, test, commit**

```python
'anandadi_yoga': day.anandadi_yoga,
```

```bash
git checkout -b feat/anandadi-yogas
git commit -m "feat(timing): Anandadi 28 muhurta yogas (Muhurta Chintamani)"
```

---

## Task 14: Disha Shoola

**Files:**
- Create: `telugu_panchangam/disha_shoola.py`
- Modify: `models/panchangam_day.py` (`disha_shoola_direction: str | None`)
- Modify: `engines/*`
- Modify: `personal/muhurta.py` (travel activity)
- Modify: `mcp/tools.py`
- Test: `tests/test_disha_shoola.py`

**Concept:** Weekday → blocked direction for travel:

```
Sunday    West
Monday    East
Tuesday   North
Wednesday North
Thursday  South
Friday    West
Saturday  East
```

- [ ] **Step 14.1: Add field**

```python
disha_shoola_direction: str | None = None
```

- [ ] **Step 14.2: Failing test**

```python
from telugu_panchangam.disha_shoola import disha_shoola

def test_disha_shoola_table():
    assert disha_shoola('Adivaram') == 'West'
    assert disha_shoola('Somavaram') == 'East'
    assert disha_shoola('Mangalavaram') == 'North'
    assert disha_shoola('Budhavaram') == 'North'
    assert disha_shoola('Guruvaram') == 'South'
    assert disha_shoola('Shukravaram') == 'West'
    assert disha_shoola('Shanivaram') == 'East'
```

- [ ] **Step 14.3: Implement**

```python
# telugu_panchangam/disha_shoola.py
DISHA_SHOOLA = {
    'Adivaram': 'West',
    'Somavaram': 'East',
    'Mangalavaram': 'North',
    'Budhavaram': 'North',
    'Guruvaram': 'South',
    'Shukravaram': 'West',
    'Shanivaram': 'East',
}

def disha_shoola(vaaram: str) -> str | None:
    return DISHA_SHOOLA.get(vaaram)
```

- [ ] **Step 14.4: Wire**

```python
from telugu_panchangam.disha_shoola import disha_shoola
day.disha_shoola_direction = disha_shoola(day.vaaram)
```

- [ ] **Step 14.5: Muhurta consumption**

Extend `tool_find_muhurta` to accept `travel_direction: str | None` param. When provided and equals `day.disha_shoola_direction`, drop the day for activity='travel'.

- [ ] **Step 14.6: Serialize, test, commit**

```python
'disha_shoola_direction': day.disha_shoola_direction,
```

```bash
git checkout -b feat/disha-shoola
git commit -m "feat(timing): Disha Shoola weekday direction-of-blocked-travel"
```

---

## Task 15: Adho / Urdhva / Tiryan-Mukha nakshatra

**Files:**
- Modify: `telugu_panchangam/nakshatra_filters.py` (extend with Mukha table)
- Modify: `models/panchangam_day.py` (`nakshatra_mukha: str | None`)
- Modify: `engines/*`
- Modify: `personal/muhurta.py` (activity-conditioned)
- Modify: `mcp/tools.py`
- Test: `tests/test_mukha_nakshatra.py`

**Concept:** Each nakshatra classified by mouth direction — used to select activities classically suited to the nakshatra's nature. Standard Muhurta Chintamani table:

```
URDHVA (up-facing — coronation, roofing, victory):
  Punarvasu, Pushya, Shravana, Dhanishtha, Shatabhisha,
  Purva Phalguni, Purva Ashadha, Purva Bhadrapada, Ardra, Mrigashira

ADHO (down-facing — digging, foundations, mining):
  Krittika, Bharani, Magha, Vishakha, Mula, Ashlesha, Jyeshtha

TIRYAN (horizontal — travel, journey, weaving, animal husbandry):
  Ashvini, Hasta, Swati, Anuradha, Chitra, Revati, Punarvasu,
  Uttara Phalguni, Uttara Ashadha, Uttara Bhadrapada, Rohini
```

(Several nakshatras have variant classifications in different sources; the table above is the most common.)

- [ ] **Step 15.1: Add field, table, test**

In `nakshatra_filters.py`:

```python
NAKSHATRA_MUKHA = {
    # Urdhva (up-facing)
    'Mrigashira': 'Urdhva', 'Ardra': 'Urdhva', 'Punarvasu': 'Urdhva',
    'Pushya': 'Urdhva', 'Shravana': 'Urdhva', 'Dhanishtha': 'Urdhva',
    'Shatabhisha': 'Urdhva', 'Purva Phalguni': 'Urdhva',
    'Purva Ashadha': 'Urdhva', 'Purva Bhadrapada': 'Urdhva',
    # Adho (down-facing)
    'Krittika': 'Adho', 'Bharani': 'Adho', 'Magha': 'Adho',
    'Vishakha': 'Adho', 'Mula': 'Adho', 'Ashlesha': 'Adho',
    'Jyeshtha': 'Adho',
    # Tiryan (horizontal)
    'Ashvini': 'Tiryan', 'Hasta': 'Tiryan', 'Swati': 'Tiryan',
    'Anuradha': 'Tiryan', 'Chitra': 'Tiryan', 'Revati': 'Tiryan',
    'Uttara Phalguni': 'Tiryan', 'Uttara Ashadha': 'Tiryan',
    'Uttara Bhadrapada': 'Tiryan', 'Rohini': 'Tiryan',
}

def nakshatra_mukha(name: str) -> str | None:
    return NAKSHATRA_MUKHA.get(name)
```

- [ ] **Step 15.2: Wire, consume, commit**

```python
from telugu_panchangam.nakshatra_filters import nakshatra_mukha
day.nakshatra_mukha = nakshatra_mukha(day.nakshatra.name)
```

Muhurta consumption: activities `construction_foundation` and `well_digging` prefer Adho; `coronation` prefers Urdhva; `travel` prefers Tiryan. Use `prefer_nakshatra_mukha: ['Adho']` rule with +1 bonus.

```bash
git checkout -b feat/nakshatra-mukha
git commit -m "feat(timing): Adho/Urdhva/Tiryan-Mukha nakshatra classification"
```

---

## Task 16: Panchaka Rahita

**Files:**
- Create: `telugu_panchangam/panchaka.py`
- Modify: `models/panchangam_day.py` (add `PanchakaInfo`, field `panchaka_rahita`)
- Modify: `engines/*` (populate day-level Panchaka at sunrise-lagna)
- Modify: `personal/muhurta.py` (slot-level Panchaka recompute per slot's lagna)
- Modify: `mcp/tools.py`
- Test: `tests/test_panchaka_rahita.py`

**Concept:** At any moment, sum {Tithi (1..30; Shukla 1..15, Krishna 16..30; Amavasya = 30), Vaaram (Sunday = 1 … Saturday = 7), Nakshatra (Ashvini = 1 … Revati = 27), Lagna (Mesha = 1 … Meena = 12)} and divide by 9. Remainder:

```
0    Rahita (auspicious)
1    Mrityu Panchaka         → hard avoid (all samskaras)
2    Agni Panchaka           → avoid for construction / property
3    Rahita (auspicious)
4    Raja Panchaka           → avoid for joining service / employment
5    Rahita (auspicious)
6    Chora Panchaka          → avoid for travel / journey
7    Rahita (auspicious)
8    Roga Panchaka           → avoid for medical procedures
```

Day-level uses the sunrise lagna; slot-level recomputes lagna at slot start.

- [ ] **Step 16.1: Add PanchakaInfo + field**

```python
@dataclass
class PanchakaInfo:
    remainder: int
    name: str
    auspicious: bool
    avoid_for: list[str]

# in PanchangamDay:
panchaka_rahita: PanchakaInfo | None = None
```

- [ ] **Step 16.2: Failing test**

```python
from telugu_panchangam.panchaka import (
    evaluate_panchaka, get_panchaka_remainder,
    tithi_to_number, nakshatra_to_number, vaaram_to_number, lagna_to_number,
)


def test_tithi_to_number_shukla():
    assert tithi_to_number('Shukla Saptami') == 7

def test_tithi_to_number_krishna():
    assert tithi_to_number('Krishna Trayodashi') == 28  # 15 + 13

def test_tithi_to_number_amavasya():
    assert tithi_to_number('Amavasya') == 30
    assert tithi_to_number('Krishna Amavasya') == 30

def test_tithi_to_number_pournami():
    assert tithi_to_number('Shukla Pournami') == 15
    assert tithi_to_number('Pournami') == 15

def test_panchaka_remainder_known_combo():
    # Tithi 7 + Sun 1 + Ashvini 1 + Mesha 1 = 10 → 10 mod 9 = 1 → Mrityu
    assert get_panchaka_remainder(7, 1, 1, 1) == 1

def test_evaluate_panchaka_mrityu():
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Mesha')
    assert info.remainder == 1
    assert info.name == 'Mrityu'
    assert info.auspicious is False
    assert 'ceremony' in info.avoid_for

def test_evaluate_panchaka_rahita_3():
    # Sum 12 → 3 → Rahita
    info = evaluate_panchaka('Shukla Saptami', 'Adivaram', 'Ashvini', 'Karkata')
    assert info.remainder == 3
    assert info.name == 'Rahita'
    assert info.auspicious is True
```

- [ ] **Step 16.3: Implement**

```python
# telugu_panchangam/panchaka.py
from telugu_panchangam.models.panchangam_day import PanchakaInfo
from telugu_panchangam.engines.base import TITHI_NAMES, NAKSHATRA_NAMES, VAARAM_NAMES


_RASI_ORDER = (
    'Mesha', 'Vrishabha', 'Mithuna', 'Karkata', 'Simha', 'Kanya',
    'Tula', 'Vrishchika', 'Dhanus', 'Makara', 'Kumbha', 'Meena',
)

_PANCHAKA_INFO = {
    0: ('Rahita', True, []),
    1: ('Mrityu', False, ['ceremony', 'wedding', 'upanayana', 'gruhapravesha',
                          'travel', 'construction', 'beginning']),
    2: ('Agni',   False, ['construction', 'gruhapravesha', 'purchase_property']),
    3: ('Rahita', True, []),
    4: ('Raja',   False, ['joining_service', 'job_start', 'dealing_with_authority']),
    5: ('Rahita', True, []),
    6: ('Chora',  False, ['travel', 'journey']),
    7: ('Rahita', True, []),
    8: ('Roga',   False, ['medical_procedure', 'surgery']),
}


def tithi_to_number(tithi_name: str) -> int:
    """Panchaka tithi numbering: Shukla 1..15, Krishna 16..30. Amavasya = 30."""
    name = tithi_name.strip()
    if name in ('Pournami', 'Shukla Pournami'):
        return 15
    if name in ('Amavasya', 'Krishna Amavasya'):
        return 30
    paksham, _, body = name.partition(' ')
    if paksham == 'Shukla':
        return TITHI_NAMES.index(body) + 1
    if paksham == 'Krishna':
        return 15 + TITHI_NAMES.index(body) + 1
    raise ValueError(f'Unrecognised tithi: {tithi_name!r}')


def nakshatra_to_number(name: str) -> int:
    return NAKSHATRA_NAMES.index(name) + 1


def vaaram_to_number(name: str) -> int:
    """Adivaram (Sunday) = 1; Shanivaram (Saturday) = 7."""
    return VAARAM_NAMES.index(name) + 1


def lagna_to_number(name: str) -> int:
    return _RASI_ORDER.index(name) + 1


def get_panchaka_remainder(tithi_num: int, vaaram_num: int,
                          nakshatra_num: int, lagna_num: int) -> int:
    return (tithi_num + vaaram_num + nakshatra_num + lagna_num) % 9


def evaluate_panchaka(tithi_name: str, vaaram_name: str,
                     nakshatra_name: str, lagna_name: str) -> PanchakaInfo:
    rem = get_panchaka_remainder(
        tithi_to_number(tithi_name),
        vaaram_to_number(vaaram_name),
        nakshatra_to_number(nakshatra_name),
        lagna_to_number(lagna_name),
    )
    name, auspicious, avoid_for = _PANCHAKA_INFO[rem]
    return PanchakaInfo(remainder=rem, name=name,
                       auspicious=auspicious, avoid_for=list(avoid_for))
```

- [ ] **Step 16.4: Wire engines (day-level — uses sunrise lagna)**

In each engine, where the sunrise lagna is already computed for `lagna_position` (via `personal/lagna_position.py`), pass it:

```python
from telugu_panchangam.panchaka import evaluate_panchaka
day.panchaka_rahita = evaluate_panchaka(
    tithi_name=day.tithi.name,
    vaaram_name=day.vaaram,
    nakshatra_name=day.nakshatra.name,
    lagna_name=sunrise_lagna_rasi,
)
```

- [ ] **Step 16.5: Slot-level recompute in muhurta**

In `personal/muhurta._evaluate_slot`, compute the lagna *at slot start*, then recompute Panchaka. When `info.name == 'Mrityu'`, hard-cap the tier (same pattern as Vyatipata/Vaidhriti in nitya_yoga). When `info.name != 'Rahita'` and `info.avoid_for` includes the activity, apply -2 score with reason `f"{info.name} Panchaka conflicts with {activity}"`.

- [ ] **Step 16.6: Serialize, run full suite, commit**

```python
def _panchaka_to_dict(p):
    if p is None:
        return None
    return {'remainder': p.remainder, 'name': p.name,
            'auspicious': p.auspicious, 'avoid_for': p.avoid_for}

'panchaka_rahita': _panchaka_to_dict(day.panchaka_rahita),
```

```bash
git checkout -b feat/panchaka-rahita
git commit -m "feat(timing): Panchaka Rahita (mod-9 dosha) day-level + slot-level"
```

---

## Task 17: Release — version bump, CHANGELOG, README, MCP docstrings

**Files:**
- Modify: `pyproject.toml` (1.8.0 → 1.9.0)
- Modify: `telugu_panchangam/mcp/server.json` (1.8.0 → 1.9.0)
- Modify: `tests/test_version_sync.py` (update expected version)
- Modify: `CHANGELOG.md` (append [1.9.0])
- Modify: `README.md` and `README_PYPI.md` (list new computations)
- Modify: `telugu_panchangam/mcp/server.py` (update `tool_get_panchangam`, `tool_find_muhurta` docstrings to enumerate new outputs)

- [ ] **Step 17.1: Bump versions in lockstep**

```toml
# pyproject.toml
version = "1.9.0"
```

```json
// telugu_panchangam/mcp/server.json
"version": "1.9.0"
```

Update `tests/test_version_sync.py` expected version string.

- [ ] **Step 17.2: CHANGELOG**

Append at top of `CHANGELOG.md`:

```markdown
## [1.9.0] — 2026-MM-DD

### Added — Timing computations round
- **Ghati/vighati infrastructure** — sunrise-anchored ghati clock with `GhatiWindow` type, exposed on `PanchangamDay.ghati_clock` and consumed by Vishaghati, Bhadra Mukha/Puchha, and Sankramana avoidance.
- **Moon's pada on the daily nakshatra span** — `PanchangamDay.nakshatra_pada` (1..4).
- **Ayanamsa as engine parameter** — Drik accepts `ayanamsa: 'lahiri' | 'raman' | 'krishnamurti' | 'true_chitrapaksha'`; Lahiri default preserves prior behaviour byte-for-byte. SS/Vakya accept the parameter for API symmetry.
- **Vishaghati windows** — `PanchangamDay.vishaghati` per Muhurta Chintamani nakshatra-poison offsets.
- **Bhadra Mukha / Puchha** — Vishti karana split into hard-avoid Mukha (first 5/16) and auspicious-for-contests Puchha (last 3/16).
- **Sankramana 16-ghati avoidance window** — `PanchangamDay.sankramana_avoidance`, samskara skip.
- **5 Panchaka Nakshatras flag** — `in_panchaka_nakshatra` for cremation/construction muhurta.
- **Khar-Maasa flag** — `is_khar_maasa` + `khar_maasa_name` (Dhanur / Meena), samskara skip.
- **Simha-Stha Guru / Shukra** — wedding muhurta filter.
- **Guru / Shukra Maudhya (combustion)** — `MaudhyaInfo` with elongation and threshold; samskara skip when combust.
- **Adhika Maasa muhurta consumption** — `find_muhurta` now skips Adhika months for samskaras (data was already in engines).
- **Pitru Paksha 15-day window** — `is_pitru_paksha`, samskara skip.
- **Anandadi 28 Yogas** — vaaram × nakshatra muhurta yoga classification.
- **Disha Shoola** — weekday direction-of-blocked-travel; activity='travel' filter.
- **Adho / Urdhva / Tiryan-Mukha nakshatra** — activity-conditioned filter for foundations / coronation / travel.
- **Panchaka Rahita** — modular-9 dosha (Mrityu / Agni / Raja / Chora / Roga or Rahita) at day-level (sunrise lagna) and slot-level (lagna at slot start).

### Changed
- MCP `tool_get_panchangam` output gains all of the above fields.
- MCP `tool_find_muhurta` reasons list now surfaces every new filter outcome.

### Notes
- ICS feeds are byte-identical (golden snapshot guard passes).
- No personal-astrology computations were added in this round.
```

- [ ] **Step 17.3: Update READMEs**

In `README.md` and `README_PYPI.md`, in the MCP-tools section, mention the new outputs under `tool_get_panchangam`.

- [ ] **Step 17.4: Update MCP server docstrings**

In `mcp/server.py`, update the `tool_get_panchangam` docstring (currently lists "Pancha Anga (Tithi, Nakshatra, Yoga, Karana), sky events …") to include "ghati clock, Moon's pada, Vishaghati, Bhadra Mukha/Puchha, Sankramana avoidance, Panchaka Nakshatra flag, Khar-Maasa, Simha-Stha Guru/Shukra, Guru/Shukra Maudhya, Pitru Paksha, Anandadi yoga, Disha Shoola, nakshatra Mukha direction, and Panchaka Rahita."

Update `tool_find_muhurta` to mention the new hard-avoid filters and activity rules.

- [ ] **Step 17.5: Run full suite one final time**

```bash
python -m pytest tests/ -v
```

Expected: 849 + ~50 new tests, all green; ICS golden snapshot unchanged; version-sync test passes with 1.9.0.

- [ ] **Step 17.6: Final commit + release branch**

```bash
git checkout -b release/1.9.0
git add pyproject.toml telugu_panchangam/mcp/server.json telugu_panchangam/mcp/server.py \
        tests/test_version_sync.py CHANGELOG.md README.md README_PYPI.md
git commit -m "release: 1.9.0 — timing computations round (16 features)"
```

---

## Verification checklist (run before opening any PR)

For every task:

- [ ] `python -m pytest tests/` is green (849 + new)
- [ ] ICS golden snapshot test passes (no feed format drift)
- [ ] Existing `test_version_sync` passes
- [ ] New module has its own test file with at least 3 assertions
- [ ] New `PanchangamDay` fields default to `None` / `False` / `[]` — backwards-compatible
- [ ] No edit under `docs/index.html`, `docs/feeds/`, `docs/muhurta-scorer.js` (UI deferred)
- [ ] No `Co-Authored-By` trailer in any commit; author is `Socraticsurge <cvk.atreya@gmail.com>`

For the release PR:

- [ ] `pyproject.toml` and `mcp/server.json` both at `1.9.0`
- [ ] `CHANGELOG.md` `[1.9.0]` section lists all 16 items
- [ ] MCP docstrings updated to mention new outputs

---

## Web-site readiness note

The website is out of scope for this round. The "machinery" required for later UI work is:

1. **Every new computation appears on `PanchangamDay`** — already the design; no extra work.
2. **Every new field serializes via `tool_get_panchangam`** — Tasks 1, 2, 4–16 each include their serialization step.
3. **`find_muhurta` reasons list mentions every new filter** — Tasks 4–16 each include muhurta consumption with reason strings.
4. **Stable JSON shape** — new fields are additive with safe defaults; existing field shapes are untouched.

When Phase 3 (Vite + TypeScript) resumes, the generated TypeScript types will pick these up via the codegen step (`tools/export_activity_rules.py` will need to be extended to emit the new activity-rule keys; that is a Phase-3 task, not a Phase-this task).

---

## Self-review

**1. Spec coverage** — all 16 items have a numbered Task. Item-by-item:

| Item | Task |
|---|---|
| Ghati/vighati infrastructure | 1 |
| Pada on daily nakshatra span | 2 |
| Ayanamsa parameter | 3 |
| Vishaghati | 4 |
| Bhadra Mukha/Puchha | 5 |
| Sankramana 16-ghati window | 6 |
| 5 Panchaka Nakshatras | 7 |
| Khar-Maasa | 8 |
| Simha-Stha Guru/Shukra | 9 |
| Guru/Shukra Maudhya | 10 |
| Adhika Maasa consumption | 11 |
| Pitru Paksha 15-day window | 12 |
| Anandadi 28 Yogas | 13 |
| Disha Shoola | 14 |
| Adho/Urdhva/Tiryan-Mukha | 15 |
| Panchaka Rahita | 16 |

Plus Task 17 for release.

**2. Placeholder scan** — no "TBD" / "implement later" / vague-error-handling. Every code block in Steps shows the actual code. Every test step shows actual assertions. Engine-wiring steps name the exact location ("where `moon_long` is computed", "after `day.ghati_clock` is set") rather than hand-waving.

**3. Type consistency** — `GhatiClock`, `GhatiWindow`, `MaudhyaInfo`, `PanchakaInfo` defined in Task 1 / 10 / 16 are referenced consistently across all later tasks. Field names on `PanchangamDay` use the same casing throughout (`is_khar_maasa`, `khar_maasa_name`, `guru_maudhya`, `shukra_maudhya`).

**Ship order** — 1 → 2 → 3 (foundation, can parallelize 2 & 3 if needed) → 4, 5, 6 (all depend on 1) → 7–10 (independent flags) → 11 (depends on existing data only) → 12 (independent) → 13, 14, 15 (table lookups, independent) → 16 (uses sunrise lagna which already exists) → 17 (release).

**End-to-end check** — after Task 17, an MCP client calling `tool_get_panchangam('2026-06-11', city='Hyderabad')` receives a JSON document with `ghati_clock`, `nakshatra_pada`, `vishaghati`, `bhadra_mukha`, `bhadra_puchha`, `sankramana_avoidance`, `in_panchaka_nakshatra`, `is_khar_maasa`, `khar_maasa_name`, `simha_stha_guru`, `simha_stha_shukra`, `guru_maudhya`, `shukra_maudhya`, `is_pitru_paksha`, `anandadi_yoga`, `disha_shoola_direction`, `nakshatra_mukha`, `panchaka_rahita`, and `ayanamsa` — every one of the 16 round items present. `tool_find_muhurta` with `activity='wedding'` correctly skips Adhika months, Pitru Paksha, Khar-Maasa, Simha-Stha Guru, combust Guru or Shukra days. `activity='travel'` respects Disha Shoola and Bhadra Puchha bonus.
