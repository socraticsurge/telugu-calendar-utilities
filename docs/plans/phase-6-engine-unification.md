# Phase 6 — Engine Unification Migration Plan

> **STATUS — NARROWED SCOPE (decided 2026-06-16):** Owner declined the full `EngineCore` refactor on cost/benefit grounds. The architectural cleanup (originally PRs 2, 4–8 of this plan) is **parked** — revisit only if a new engine variant or a real bug forces it. The two PRs with visible value remain active. See **§7 Active scope** (replaced) and **§A Parked work** (appendix). The rest of this document is preserved as reference if/when the refactor case re-opens.
>
> **Ayanamsa confirmed (2026-06-16):** Drik engine uses Lahiri (`swe.SIDM_LAHIRI` at `engines/utils.py:32`) — Indian Astronomical Ephemeris standard, same default Drik Panchang uses. No change planned.
>
> **Active scope (~1 week of work):**
> - **PR 1** — Forward-year DP-verified festival pin (2027–2028, three cities, 18 cells). Pure-additive test fixture. Devotee-visible value (correct festival dates for future years; year-boundary regression guard).
> - **PR 2** — Table-driven festival rules: convert Karthika Somavaram / Varalakshmi Vratam / Sankashti Chaturthi from inline cases (`base.py:463-475`) to rule-table entries. Zero behaviour change. Squarely within CLAUDE.md's "append festival rows" exception.
>
> **Verification rule** (still applies): per `verify-against-drikpanchang.md`, every timing-affecting PR cites DP day-pages or scriptural reference in the PR body.

---

## 1. Executive summary

The three engines (`DrikGanitaEngine`, `SuryaSiddhantaEngine`, `VakyaEngine`) share roughly 90% of their structure but encode that overlap through three nearly-identical method bodies in each class. `_tithi_index_at`, `_tithi_span`, `_nakshatra_span`, `_yoga_span`, `_karana_spans`, `_special_flags`, `_maasam`, the eight day-part window helpers, and the top-level `calculate` body are all duplicated 3× with the only meaningful delta being **which longitude function is called** (`sun_longitude` vs `ss_sun_longitude`; `moon_longitude` vs `ss_moon_longitude` vs `vakya_moon_longitude`; corresponding elongations). One method — `facts_at` (base.py:325-391) — already lives on the abstract base, dispatches purely through the two virtual longitude hooks, and is consumed unchanged by all three engines. **`facts_at` is what every other helper should look like.** Phase 6 is the work of getting there.

The proposal is a sibling-composition refactor: a single concrete `EngineCore` owns all shared logic; each engine becomes a thin factory that injects an `Ephemeris` (sun + moon longitude functions) and an optional `MoonCorrection` overlay. Vakya stops being `VakyaEngine(SuryaSiddhantaEngine)` and becomes a sibling of SS that composes the same `SuryaSiddhantaEphem` and adds a `VakyaCorrection` additive moon offset. The eight Vakya overrides that exist today solely to swap `ss_*` for `vakya_*` go to zero.

Two behavioral asymmetries surface during the work and need explicit owner decisions, not silent code merges. **First**, `_special_flags is_sankranti` uses different sampling windows: Drik samples sunrise ± 24 h (symmetric); SS/Vakya sample yesterday-sunrise / today-sunrise / today-sunset (asymmetric). Both are 3-point — an earlier mapping note that said "3 vs 2" was wrong. **Second**, `_is_makara_day` (base.py:397-406) uses yet a third convention (sun-entry-after-sunset rolls to next day) and drives the Makara / Bhogi / Kanuma festival cluster regardless of engine. Unifying these requires either a `SankrantiPolicy` strategy or an explicit owner-approved choice of one convention; we recommend a `SankrantiPolicy` and refuse to merge a `if self.system == 'drik':` string switch into `EngineCore`.

`facts_at` itself needs a richer signature. Today it takes a single `datetime` and returns one slot's facts. Callers that want "the facts at madhyahna" or "the facts at moonrise" compute the JD externally, then call `facts_at` with a constructed datetime — losing engine-internal caches and forcing every caller to re-derive what `EngineCore` already knows. The new signature accepts either a `datetime` or a named deciding moment (`'sunrise' | 'madhyahna' | 'aparahna' | 'pradosha' | 'nishita' | 'moonrise' | 'sunset'`), with the day implied by a base date + location. Callers migrate in the same PR that lands the signature change.

The festival deciding-moment vocabulary is the natural follow-on. `base.py` defines five lists keyed to `sunrise / madhyahna / aparahna / pradosha / nishita`, plus two inline-cased festivals (Karthika Somavaram at base.py:463-464; Varalakshmi Vratam at base.py:465-469). Adding **`sandhya` (twilight)**, **`arunodaya` (pre-dawn ~96 min before sunrise)**, **`moonrise`**, and **`sunset`** as first-class deciding moments lets us pull both inline-cased festivals and Sankashti Chaturthi (base.py:472-475, currently inline) into table-driven form without touching engine math. This is appending to the rules table — the one routine change `CLAUDE.md` explicitly permits — and is the cheapest, lowest-risk PR in the sequence.

Forward-year DP verification is a non-negotiable gate. Today's pinned 33 DP-verified festival dates (per memory `festival-layer.md`) cover the current and prior year only. Phase 6 ships with a forward-year pin (Hyderabad / Bengaluru / Chennai 2027–2028) that exercises every deciding-moment branch including the new vocabulary — landed as PR #1 **before** any EngineCore code touches the repo, so the parity gate has somewhere to lock to. The matrix in §6 lists 18 specific (festival × year × city) cells with the exact field to verify against drikpanchang.com day pages.

## 2. Current state map — engine asymmetries

All findings are paraphrased from the `find:asymmetries` audit; the file:line citations have been re-confirmed.

| Method | Drik | Surya Siddhanta | Vakya | Notes |
|---|---|---|---|---|
| `calculate` | drik.py:228-325 | surya_siddhanta.py:77-147 | vakya.py:47-117 | Three full copies. Only deltas: longitude functions called, `system='…'` literal, Drik writes flags as explicit kwargs vs `**special` in SS/Vakya. |
| `_tithi_index_at` | drik.py:36-38 | surya_siddhanta.py:152-153 | vakya.py:127-128 | Identical algebra `int(elong / 12.0) % 30`; only the elongation primitive differs. Base does NOT define it but `_festivals` calls it (base.py:434, 450, 453, 468, 476-481). |
| `_tithi_span` | drik.py:40-55 | surya_siddhanta.py:155-161 | vakya.py:130-136 | Identical root-find structure on engine-specific elongation. |
| `_nakshatra_span` | drik.py:57-75 | surya_siddhanta.py:163-171 | vakya.py:138-146 | Identical; differs only in moon-longitude function. |
| `_yoga_span` | drik.py:77-98 | surya_siddhanta.py:173-183 | vakya.py:148-158 | Inlines `(sun + moon) % 360`; only the two primitives differ. |
| `_karana_spans` | drik.py:194-226 | surya_siddhanta.py:185-199 | vakya.py:160-174 | Identical 3-offset loop; only elongation differs. Drik adds two local variables (`ht_start_deg`, `ht_end_deg` at drik.py:202-203) for clarity. |
| `_special_flags` | drik.py:170-192 | surya_siddhanta.py:207-223 | vakya.py:176-192 | Identical 7-key dict EXCEPT `is_sankranti` window (see §2.1 below). |
| `_maasam` | drik.py:166-168 | surya_siddhanta.py:204-205 | vakya.py:194-195 | All wrap shared `base.maasam_name`; only primitives differ. |
| `_samvatsara` | drik.py:162-164 | surya_siddhanta.py:201-202 | inherits SS | Drik / SS bodies are **textually identical**; trivially liftable to base. |
| `_moon_longitude_func` | drik.py:333-334 | surya_siddhanta.py:265-267 | vakya.py:121-122 | Cleanest virtual hook; works as designed. |
| `_sun_longitude_func` | drik.py:330-331 | surya_siddhanta.py:269-270 | vakya.py:124-125 | Vakya override is a no-op restatement of SS; deletable. |
| `_sun_sign_idx_at` | drik.py:327-328 | surya_siddhanta.py:149-150 | inherits SS | Could promote to base as `int(self._sun_longitude_func()(jd) / 30.0) % 12`. |
| Day-part windows (8 methods) | drik.py:100-160 | surya_siddhanta.py:225-263 | inherits SS | Drik / SS bodies behaviorally identical; stylistic delta only (`wd` vs `weekday` etc.). `_DAY_CHOGHADIYA` duplicated at drik.py:24-32 AND surya_siddhanta.py:31-39. |
| `facts_at` | inherits | inherits | inherits | **Reference example.** Base-only at base.py:325-391; dispatches through `_sun_longitude_func` / `_moon_longitude_func` / `_sun_sign_idx_at`. |
| `_is_makara_day` | inherits | inherits | inherits | base.py:397-406. Uses sun-entry-after-sunset → next day convention. |
| `_sankramanam_name` | inherits | inherits | inherits | base.py:408-419. Same after-sunset convention as `_is_makara_day`. |
| `_festivals` | inherits | inherits | inherits | base.py:421-484. Inline-cased festivals: Karthika Somavaram (base.py:463-464); Varalakshmi Vratam (base.py:465-469); Sankashti Chaturthi (base.py:472-475); Masa Shivaratri (base.py:479-482). |

### 2.1 The `is_sankranti` window divergence (verified from code)

**The earlier "3 vs 2" note in the map was wrong.** All three engines sample **three** points; the **windows** differ:

- **Drik** (drik.py:179-183): `jd_sr`, `jd_sr - 1.0`, `jd_sr + 1.0` — symmetric 48 h around sunrise.
- **SS** (surya_siddhanta.py:214-216): `jd_sr`, `jd_ss`, `jd_sr - 1.0` — asymmetric, covers yesterday-sunrise through today-sunset.
- **Vakya** (vakya.py:183-185): same three points as SS.

Real-world consequence: for sun ingresses that occur between today's sunset and tomorrow's sunrise, **Drik flags today** (via `+1d`); **SS/Vakya catch it tomorrow** (via their `-1d`). Meanwhile `_is_makara_day` (base.py:397-406) and the festival-cluster check at base.py:427-432 use a **third** convention (after-sunset rolls to next day) that drives Makara / Bhogi / Kanuma for **all three** engines. Today's code therefore uses two different sankranti conventions in the same engine output.

### 2.2 Test-only import surface (corrected from earlier draft)

`ss_elongation`, `vakya_elongation`, `ss_sun_longitude`, `ss_moon_longitude`, `vakya_moon_longitude` are imported only by `tests/test_surya_siddhanta_engine.py:2,57` and `tests/test_vakya_engine.py:2,3`. `personal/`, `gochara/`, `mcp/tools.py`, `scripts/` import only `Engine` classes plus `engines.base` name tables and `engines.utils` helpers. The compat shim layer in PR 6 below is therefore a test-only concern.

### 2.3 `_KALI_EPOCH_JD` ambiguity

Two distinct constants currently live in the engines tree:

- `engines/base.py:109` — `_KALI_EPOCH_JD = 588465.5` (no Ujjain correction; consumed by `samvatsara_name` at base.py:113-125).
- `engines/surya_siddhanta.py:24` — `_KALI_EPOCH_JD = 588465.5 - 75.7683 / 360.0` (Ujjain-corrected ≈ 588465.2898; consumed by SS `_mean_longitude` and by `engines/vakya.py:34` for the table cycle).

A new `engines/core.py` must not import one and silently get the other. The plan extracts both to `engines/constants.py` under distinct names (`SAMVATSARA_KALI_EPOCH_JD`, `SS_KALI_EPOCH_JD_UJJAIN`) with a pinned numerical test before any EngineCore code lands.

### 2.4 Eclipse computation inconsistency (load-bearing inheritance, NOT in scope for Phase 6)

`telugu_panchangam/eclipses.py:2,35,48` uses Swiss Ephemeris for **all** eclipse detection, called identically from all three engines (drik.py:275, surya_siddhanta.py:115, vakya.py:85). Architectural meaning: SS/Vakya engines today are not "pure SS" / "pure Vakya" — eclipse times are Swiss-derived. Phase 6 explicitly carries this inconsistency forward unchanged and documents it as a known non-goal. A future phase can decide whether to compute SS/Vakya eclipses from their own mean motions.

## 3. Proposed `EngineCore` design

### 3.1 Class skeleton (target shape)

```python
# telugu_panchangam/engines/core.py  (NEW module; engines/ remains frozen until owner sign-off lands PR 2)

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Optional, Literal

from telugu_panchangam.engines.constants import SS_KALI_EPOCH_JD_UJJAIN
from telugu_panchangam.models.panchangam_day import (
    Location, PanchangamDay, Span, Window, SlotFacts,
)

# --- Plug points ----------------------------------------------------------

class Ephemeris(ABC):
    """Sidereal longitude model. Owns ayanamsa internally."""
    @abstractmethod
    def sun_longitude(self, jd: float) -> float: ...
    @abstractmethod
    def moon_longitude(self, jd: float) -> float: ...

class MoonCorrection(ABC):
    """Additive offset (degrees) applied to ephemeris moon longitude."""
    @abstractmethod
    def offset_deg(self, jd: float) -> float: ...
    @staticmethod
    def identity() -> 'MoonCorrection': return _ZeroCorrection()

class SankrantiPolicy(ABC):
    """Pluggable sampling pattern for is_sankranti flag."""
    @abstractmethod
    def is_sankranti(self, sun_sign_idx_at: Callable[[float], int],
                    jd_sr: float, jd_ss: float) -> bool: ...

class SymmetricSankrantiPolicy(SankrantiPolicy):
    """Drik's current behavior: sample sr-1d, sr, sr+1d."""
    def is_sankranti(self, idx, jd_sr, jd_ss):
        return idx(jd_sr) != idx(jd_sr + 1.0) or idx(jd_sr - 1.0) != idx(jd_sr)

class AsymmetricSunsetSankrantiPolicy(SankrantiPolicy):
    """SS/Vakya's current behavior: sample sr-1d, sr, ss."""
    def is_sankranti(self, idx, jd_sr, jd_ss):
        return idx(jd_sr) != idx(jd_ss) or idx(jd_sr) != idx(jd_sr - 1.0)

# --- Core ----------------------------------------------------------------

@dataclass(frozen=True)
class EngineCore:
    system: Literal['drik', 'surya_siddhanta', 'vakya']
    ephemeris: Ephemeris
    moon_correction: MoonCorrection = field(default_factory=MoonCorrection.identity)
    sankranti_policy: SankrantiPolicy = field(default_factory=SymmetricSankrantiPolicy)

    # --- Composed primitives (the three closures every helper uses) -----
    def sun_longitude(self, jd: float) -> float:
        return self.ephemeris.sun_longitude(jd)

    def moon_longitude(self, jd: float) -> float:
        return (self.ephemeris.moon_longitude(jd)
                + self.moon_correction.offset_deg(jd)) % 360.0

    def elongation(self, jd: float) -> float:
        return (self.moon_longitude(jd) - self.sun_longitude(jd)) % 360.0

    def sun_sign_idx_at(self, jd: float) -> int:
        return int(self.sun_longitude(jd) / 30.0) % 12

    # --- Top-level orchestration ----------------------------------------
    def calculate(self, d: date, location: Location,
                  include_eclipse: bool = True) -> PanchangamDay: ...
    def calculate_bulk(self, start_date: date, days: int, location: Location,
                       include_eclipse: bool = True) -> list[PanchangamDay]: ...

    # --- Span helpers (was duplicated 3x) -------------------------------
    def tithi_index_at(self, jd: float) -> int:
        return int(self.elongation(jd) / 12.0) % 30
    def tithi_span(self, jd_sunrise: float) -> Span: ...
    def nakshatra_span(self, jd_sunrise: float) -> Span: ...
    def yoga_span(self, jd_sunrise: float) -> Span: ...
    def karana_spans(self, jd_sr: float, jd_ss: float) -> list[Span]: ...

    # --- Solar / festival --------------------------------------------------
    def is_makara_day(self, jd_sr: float, jd_ss: float) -> bool: ...
    def sankramanam_name(self, jd_sr, jd_ss) -> Optional[str]: ...
    def maasam(self, jd_sunrise: float) -> str: ...
    def samvatsara(self, jd_sunrise: float, maasam: str) -> str: ...
    def special_flags(self, tithi_idx, weekday, jd_sr, jd_ss) -> dict: ...
    def festivals(self, maasam, weekday, jd_sr, jd_ss, jd_next_sr,
                  jd_moonrise) -> list[str]: ...

    # --- Per-instant facts (new richer signature; see §4) ---------------
    def facts_at(self, when: 'FactsAtMoment', location: Location,
                 vaaram: Optional[str] = None) -> SlotFacts: ...

    # --- Day-part windows (8 methods, lifted unchanged) -----------------
    def rahu_kalam(self, weekday, jd_sr, jd_ss) -> Window: ...
    def gulika_kalam(self, weekday, jd_sr, jd_ss) -> Window: ...
    def yamagandam(self, weekday, jd_sr, jd_ss) -> Window: ...
    def brahma_muhurta(self, jd_sunrise: float) -> Window: ...
    def abhijit_muhurta(self, jd_sr, jd_ss, weekday) -> Optional[Window]: ...
    def durmuhurtham(self, weekday, jd_sr, jd_ss, jd_next_sr) -> list[Window]: ...
    def choghadiya(self, weekday, jd_sr, jd_ss) -> list[Window]: ...
```

### 3.2 Plug points each concrete engine supplies

| Engine factory | `ephemeris` | `moon_correction` | `sankranti_policy` | `system` |
|---|---|---|---|---|
| `DrikGanitaEngine()` | `SwissEphem()` | `MoonCorrection.identity()` | `SymmetricSankrantiPolicy()` | `'drik'` |
| `SuryaSiddhantaEngine()` | `SuryaSiddhantaEphem()` | `MoonCorrection.identity()` | `AsymmetricSunsetSankrantiPolicy()` (preserves current behavior; see §8 risk R2) | `'surya_siddhanta'` |
| `VakyaEngine()` | `SuryaSiddhantaEphem()` | `VakyaCorrection(epoch=SS_KALI_EPOCH_JD_UJJAIN)` | `AsymmetricSunsetSankrantiPolicy()` | `'vakya'` |

**Each engine factory is a function returning an `EngineCore` instance, not a subclass.** This avoids the `frozen=True` + subclass-`__init__` footgun (`object.__setattr__` for inherited frozen fields). Callers that write `engine = DrikGanitaEngine()` keep working. No code in the repo does `isinstance(engine, DrikGanitaEngine)` or `type(engine).__name__` (verified by repo-wide grep).

### 3.3 Ayanamsa threading — kept inside `Ephemeris`, never on `EngineCore`

Lahiri sidereal mode lives in `engines/utils.py:30-35` (`swe.set_sid_mode(swe.SIDM_LAHIRI)` inside `sidereal_longitude`). `SwissEphem` wraps that. `SuryaSiddhantaEphem` is sidereal by construction (mean motions anchored to the Ujjain-corrected Kali epoch). **`EngineCore` has no ayanamsa parameter.** If a future caller wants Drik-with-Krishnamurti, they construct `SwissEphem(ayanamsa='krishnamurti')` and inject it; `EngineCore` is untouched. The existing `ayanam_name` helper (Uttarayanam vs Dakshinayanam, base.py:90-91) is a label over the sidereal sun sign, not the ayanamsa itself, and stays on `EngineCore` as a derived helper.

### 3.4 Caching strategy

`engines/utils.py:38-60` `lru_cache`s `sun_longitude`, `moon_longitude`, AND the composite `moon_sun_elongation`. Under EngineCore, `self.elongation(jd)` becomes `(moon_longitude(jd) - sun_longitude(jd)) % 360`, decomposing to two cached lookups + subtract + mod. The composite cache becomes dead code. `_karana_spans` makes up to 6 `find_crossing` calls per day; the bulk feeds emit 365 days × 20 cities × 3 engines (~22 000 day-computations per nightly job). **Benchmark required before PR 2 lands**; if the dead composite cache costs more than ~5% on the bulk path, add a module-level `_cached_elongation(ephemeris_id, jd)` helper that `EngineCore.elongation` delegates to, keyed by `id(self.ephemeris) + id(self.moon_correction)`. Numbers go in the PR 2 description.

## 4. Proposed `facts_at` refactor

### 4.1 Current signature (base.py:325-391)

```python
def facts_at(self, dt: datetime, location: Location,
             vaaram: Optional[str] = None) -> SlotFacts:
```

Callers compute the JD for "moonrise on 2026-08-29 in Hyderabad" externally, build a `datetime`, hand it in. Loses any chance for `EngineCore` to cache "sunrise/sunset/moonrise for this date+location" across calls.

### 4.2 New signature

```python
NamedMoment = Literal[
    'sunrise', 'sunset', 'madhyahna', 'aparahna',
    'pradosha', 'nishita', 'moonrise',
    'sandhya', 'arunodaya',          # new — see §5
]

FactsAtMoment = datetime | tuple[date, NamedMoment]

def facts_at(self, when: FactsAtMoment, location: Location,
             vaaram: Optional[str] = None) -> SlotFacts:
    """When `when` is a datetime, behave exactly as today.
    When `when` is `(date, named_moment)`, resolve the JD internally
    using the engine's own sunrise/sunset/moonrise computation and
    return the slot facts at that instant."""
```

Backwards-compatible by Python's union dispatch: existing callers passing `datetime` are unchanged. New callers passing `(date, 'madhyahna')` get the engine to do the deciding-moment math internally, exactly as `_festivals` does today (base.py:443-475).

### 4.3 Caller migration table

| Caller | File:line | Current call | New call | Migration burden |
|---|---|---|---|---|
| Tarabalam slot lookup | `personal/tarabalam.py` (via engine output) | passes `datetime` from sunrise | unchanged (datetime branch) | None |
| Chandra Bala chart | `personal/chandrabalam.py` | passes `datetime` | unchanged | None |
| Lagna position | `personal/lagna_position.py` | passes `datetime` | unchanged | None |
| Lagna hora | `personal/lagna_hora.py` | passes `datetime` | unchanged | None |
| Muhurta windows | `personal/muhurta.py` | passes `datetime` | unchanged | None |
| Gochara positions | `gochara/positions.py` | passes `datetime` | unchanged | None |
| ICS generator | `generators/ics.py` | reads `PanchangamDay` only (no `facts_at` call) | unchanged | None |
| MCP tools | `mcp/tools.py` | no direct `facts_at` call | unchanged | None |
| `_festivals` internal | `engines/base.py:443-475` | computes named-moment JD inline | refactor to call `facts_at((date, 'madhyahna'), ...)` | **Inside PR 4** (`_festivals` → `EngineCore.festivals`); keeps the JD math co-located in `EngineCore`, removes duplication when `sandhya` / `arunodaya` are added in §5. |
| New deciding-moment festival rules (Karthika Somavaram, Varalakshmi, Sankashti) | new `_SANDHYA_FESTIVALS`, `_MOONRISE_FESTIVALS`, `_ARUNODAYA_FESTIVALS` tables (§5) | drive lookup off `facts_at((date, ...))` | **PR 3** (vocabulary expansion) | Net code reduction by removing inline cases at base.py:463-464, 465-469, 472-475. |

**Net effect:** Public callers see zero signature break. Only internal `_festivals` benefits from the new branch, and that benefit is what enables the table-driven festival rules in §5.

## 5. Expanded festival deciding-moment vocabulary

### 5.1 Existing vocabulary (verified at base.py:256-294, 443-475)

| Moment | Definition | Rule table | Festivals (count) |
|---|---|---|---|
| `sunrise` | `jd_sunrise` | `_SUNRISE_FESTIVALS` (base.py:256-274) | 17 |
| `madhyahna` | `jd_sr + 0.5 * (jd_ss - jd_sr)` (base.py:443-444) | `_MADHYAHNA_FESTIVALS` (base.py:276-281) | 4 |
| `aparahna` | `jd_sr + 0.7 * (jd_ss - jd_sr)` (base.py:445-446) | `_APARAHNA_FESTIVALS` (base.py:283-286) | 2 |
| `pradosha` | `jd_ss + 0.05` (~72 min after sunset; base.py:447-448) | `_PRADOSHA_FESTIVALS` (base.py:288-290) | 1 (Deepavali) |
| `nishita` | `(jd_ss + jd_next_sr) / 2` (base.py:435) | `_NISHITA_FESTIVALS` (base.py:292-294) | 1 (Maha Shivaratri) |

### 5.2 New vocabulary

| Moment | Definition | New rule table | Festivals to convert from inline |
|---|---|---|---|
| `sandhya` (evening twilight) | `jd_ss - 0.025` (~36 min before sunset; deliberately earlier than `pradosha` to keep them distinguishable) | `_SANDHYA_FESTIVALS` | — (no inline cases today; reserved for future Pradosha Vrata expansion if owner wants it as separate from Deepavali pradosha) |
| `arunodaya` (pre-dawn) | `jd_sunrise - 0.067` (~96 min / 4 ghatis before sunrise; matches the classical 4-ghati arunodaya window) | `_ARUNODAYA_FESTIVALS` | — (reserved for Vaishakha-month Madhva-tradition festivals on future request) |
| `moonrise` | engine-computed `jd_moonrise` (already passed into `_festivals` at base.py:425) | `_MOONRISE_FESTIVALS` | **Sankashti Chaturthi** (base.py:472-475): currently inline-cased — "use moonrise if it falls between sunset and next sunrise else sunset+0.1". After conversion, sits as `('*', 18, 'Sankashti Chaturthi')` in `_MOONRISE_FESTIVALS` with a fallback "if moonrise > next_sunrise: use sunset+0.1" rule encoded once in `EngineCore.festivals`. |
| `sunset` (Friday-rule special) | `jd_sunset` | `_SUNSET_WEEKDAY_FESTIVALS` (new tuple shape: `(maasam, tithi_idx, weekday, name, lookahead_rule)`) | **Varalakshmi Vratam** (base.py:465-469): inline-cased — "Shravana Friday, tithi-at-sunrise ≤ 14, tithi at `jd_sr + 7.0` ≥ 15". |
| `weekday_in_maasam` (not a deciding moment per se but a rule type) | — | `_WEEKDAY_IN_MAASAM_FESTIVALS` (new) | **Karthika Somavaram** (base.py:463-464): inline-cased — "any Monday in Kartika maasam". |

### 5.3 Inline-case → table-driven conversion

The conversion is one PR (PR 3 below). The diff is approximately:

**Remove** (base.py:463-475, 9 lines):
```python
if base_m == 'Kartika' and weekday == 1:
    fests.append('Karthika Somavaram')

if (base_m == 'Shravana' and weekday == 5 and t_sr <= 14
        and self._tithi_index_at(jd_sr + 7.0) >= 15):
    fests.append('Varalakshmi Vratam')

# Sankashti Chaturthi (Krishna Chaturthi)
jd_sankashti = jd_moonrise if jd_ss < jd_moonrise < jd_next_sr else jd_ss + 0.1
if self._tithi_index_at(jd_sankashti) == 18 and t_sr != 18:
    fests.append('Sankashti Chaturthi')
```

**Add** (in `base.py` rule tables):
```python
_MOONRISE_FESTIVALS: tuple[tuple[str, int, str], ...] = (
    ('*', 18, 'Sankashti Chaturthi'),   # any maasam (incl. Adhika)
)

_SUNSET_WEEKDAY_FESTIVALS = (
    # (maasam, tithi_at_sunrise_max, weekday, lookahead_jd_offset,
    #  tithi_at_lookahead_min, name)
    ('Shravana', 14, 5, 7.0, 15, 'Varalakshmi Vratam'),
)

_WEEKDAY_IN_MAASAM_FESTIVALS = (
    # (maasam, weekday, name)
    ('Kartika', 1, 'Karthika Somavaram'),
)
```

**Add** (in `EngineCore.festivals`, single dispatch):
```python
# Moonrise-driven (with sunset+0.1 fallback when moonrise outside [sunset, next_sunrise])
jd_mr_eff = jd_moonrise if jd_ss < jd_moonrise < jd_next_sr else jd_ss + 0.1
for (m_rule, t_idx, name) in _MOONRISE_FESTIVALS:
    if (m_rule == '*' or m_rule == base_m) and self.tithi_index_at(jd_mr_eff) == t_idx \
            and t_sr != t_idx:
        fests.append(name)

# Sunset + lookahead (Varalakshmi pattern)
for (m, t_max, wd, look, t_min, name) in _SUNSET_WEEKDAY_FESTIVALS:
    if base_m == m and weekday == wd and t_sr <= t_max \
            and self.tithi_index_at(jd_sr + look) >= t_min:
        fests.append(name)

# Weekday in maasam
for (m, wd, name) in _WEEKDAY_IN_MAASAM_FESTIVALS:
    if base_m == m and weekday == wd:
        fests.append(name)
```

This conversion **does not change behavior** — the rules are line-equivalent. It is the same `CLAUDE.md`-permitted "appending a festival row" change applied retroactively to three festivals that were inline. The test for PR 3 is the same pinned 33 dates from `festival-layer.md`, plus the new forward-year matrix from §6.

## 6. Forward-year DP-verification matrix

Per `verify-against-drikpanchang.md`: timing changes need spot-checks on **multiple dates and more than one city**. The current pinned festival set (per memory `festival-layer.md`) covers ~33 dates and stops at the current year. Phase 6 ships with this forward matrix as PR 1, landing **before** any EngineCore code.

**Cities and DP geoname IDs** (resolved via drikpanchang.com search URL `?geoname-id=` parameter):

| City | DP geoname ID | TZ |
|---|---|---|
| Hyderabad, India | `1269843` | Asia/Kolkata |
| Bengaluru, India | `1277333` | Asia/Kolkata |
| Chennai, India | `1264527` | Asia/Kolkata |

### 6.1 Festival × year × city × field verification cells (18 cells)

Each cell is a single drikpanchang.com day-page lookup followed by a pinned assertion in `tests/test_festivals_forward_year.py`.

| # | Festival | Date (computed, IST) | City | Deciding moment | Field to pin | DP URL pattern |
|---|---|---|---|---|---|---|
| 1 | Ugadi | 2027-04-07 | Hyderabad | madhyahna | tithi end JD, festival name on day | `https://www.drikpanchang.com/panchang/day-panchang.html?date=07/04/2027&geoname-id=1269843` |
| 2 | Sri Rama Navami | 2027-04-15 | Hyderabad | madhyahna | tithi index at madhyahna | same pattern, date=15/04/2027 |
| 3 | Akshaya Tritiya | 2027-05-08 | Bengaluru | madhyahna | maasam=Vaishakha at sunrise | date=08/05/2027&geoname-id=1277333 |
| 4 | Vinayaka Chavithi | **2027-09-08** | Hyderabad | madhyahna (12:33 IST approx) | tithi end JD, madhyahna JD | date=08/09/2027&geoname-id=1269843 |
| 5 | Maharnavami | 2027-10-09 | Chennai | aparahna | tithi at aparahna | date=09/10/2027&geoname-id=1264527 |
| 6 | Vijayadashami | 2027-10-10 | Chennai | aparahna | maasam=Ashvina, tithi=9 at aparahna | date=10/10/2027&geoname-id=1264527 |
| 7 | Deepavali | 2027-11-07 | Hyderabad | pradosha | tithi index at sunset+0.05; maasam-rollover check (Amavasya at sunrise + Pratipada at pradosha) | date=07/11/2027&geoname-id=1269843 |
| 8 | Maha Shivaratri | 2028-02-23 | Bengaluru | nishita | tithi at (jd_ss + jd_next_sr)/2 | date=23/02/2028&geoname-id=1277333 |
| 9 | Karthika Somavaram | 2027-11-15 | Hyderabad | sunrise (weekday-in-maasam rule) | maasam=Kartika, weekday=Monday | date=15/11/2027&geoname-id=1269843 |
| 10 | Varalakshmi Vratam | 2027-08-13 | Chennai | sunset-weekday-lookahead | Shravana, Friday, tithi_at_sr ≤ 14, tithi_at_sr+7d ≥ 15 | date=13/08/2027&geoname-id=1264527 |
| 11 | Sankashti Chaturthi | 2027-07-23 | Bengaluru | moonrise | tithi=18 at moonrise (if between sunset and next sunrise) | date=23/07/2027&geoname-id=1277333 |
| 12 | Masa Shivaratri | 2027-11-26 | Hyderabad | sunset+pratah | tithi=28 at jd_ss+0.1; verify Maha Shivaratri did not also fire | date=26/11/2027&geoname-id=1269843 |
| 13 | Makara Sankranti | 2028-01-14 | Hyderabad | `_is_makara_day` (sun-entry-after-sunset rolls forward) | sun sign=Capricorn (idx 9) at sunrise | date=14/01/2028&geoname-id=1269843 |
| 14 | Bhogi | 2028-01-13 | Hyderabad | `_is_makara_day(next_sr, ss+1)` | day before Makara | date=13/01/2028&geoname-id=1269843 |
| 15 | Kanuma | 2028-01-15 | Hyderabad | `_is_makara_day(sr-1, ss-1)` | day after Makara | date=15/01/2028&geoname-id=1269843 |
| 16 | Krishna Janmashtami | 2027-09-04 | Chennai | sunrise (8th tithi Shravana Krishna) | tithi=22 at sunrise | date=04/09/2027&geoname-id=1264527 |
| 17 | Ratha Saptami | 2028-02-02 | Bengaluru | sunrise | tithi=6 Magha Shukla | date=02/02/2028&geoname-id=1277333 |
| 18 | Holi | 2028-03-11 | Hyderabad | sunrise (Phalguna Pournami next day) | tithi=14 at sunrise; weekday | date=11/03/2028&geoname-id=1269843 |

**Note on dates:** computed dates above are placeholders pending the actual engine run on the feature branch. PR 1 generates them, the human verifies them against drikpanchang.com day pages, **then** they get pinned. Any drift between computed and DP-published is a hard merge blocker and triggers an investigation, not a test-update.

### 6.2 Scrape commands

A small helper script `scripts/dp_verify_forward.py` (new in PR 1) prints the 18 URLs and the expected values it computed locally. Operator opens each URL, eyeballs the festival name + deciding-moment time, and signs off. Optionally:

```bash
# Print URLs + computed values for human review
python scripts/dp_verify_forward.py --year 2027 --year 2028 \
    --city hyderabad --city bengaluru --city chennai

# Once verified, freeze into the test fixture
python scripts/dp_verify_forward.py --pin > tests/fixtures/forward_year_festivals.json
```

The scraping method already documented in memory `verify-against-drikpanchang.md` is reused; this script does not introduce a new scrape mechanism.

## 7. Active scope — 2 PRs (narrowed 2026-06-16)

The two PRs with visible value. The full 8-PR breakdown is preserved verbatim in §A as parked reference.

| # | Title | Scope | Verification burden | Review burden |
|---|---|---|---|---|
| **1** | **Forward-year DP-verified festival pin** | Add `tests/test_festivals_forward_year.py` + `tests/fixtures/forward_year_festivals.json` covering the 18 cells in §6. Add `scripts/dp_verify_forward.py` helper. **No engine code changes.** | High — 18 manual DP day-page spot-checks. Owner reviews each URL alongside drikpanchang.com. Done collaboratively. | Low — pure additive test fixture. |
| **2** | **Table-driven festival rules (Karthika Somavaram / Varalakshmi / Sankashti)** | Add `_SANDHYA_FESTIVALS`, `_ARUNODAYA_FESTIVALS`, `_MOONRISE_FESTIVALS`, `_SUNSET_WEEKDAY_FESTIVALS`, `_WEEKDAY_IN_MAASAM_FESTIVALS` rule tables. Convert the three inline-cased festivals (`base.py:463-464`, `465-469`, `472-475`) into rule-table entries. **No engine math changes** — diff is line-equivalent. | Medium — the existing 33-date pinned festival suite (per `festival-layer.md` memory) and PR 1's new forward-year matrix must remain byte-equal. | Low — refactor inside the festival driver; reviewer compares old-vs-new behaviour table. |

**Dependencies:** PR 1 must land before PR 2 so the forward-year regression provides a stable parity gate.

**What's NOT in active scope:**
- `EngineCore` class refactor (was PR 2 in original plan)
- `facts_at` signature enrichment with NamedMoment union (was PR 4)
- `SankrantiPolicy` strategy + unifying the three sankranti conventions (was PR 5)
- Caller migrations to factory functions (was PR 6)
- Deletion of duplicated engine method bodies (was PR 7)
- `CLAUDE.md` frozen-core text revision (was PR 8)

All parked items are documented as "investigation only" — i.e., the *findings* in §2 stand as the canonical map of engine asymmetries, but no code lands. Future work may pull individual items back in scope when a concrete driver appears (e.g., a new ayanamsa variant request, or a user-reported `is_sankranti` bug on SS/Vakya feeds).

---

## 7-OLD. PR breakdown (original 8 PRs — PARKED, preserved as reference)

| # | Title | Scope | Verification burden | Review burden | Deps |
|---|---|---|---|---|---|
| **1** | **Forward-year DP-verified festival pin** | Add `tests/test_festivals_forward_year.py` + `tests/fixtures/forward_year_festivals.json` covering the 18 cells in §6. Add `scripts/dp_verify_forward.py`. No engine code changes. | **Highest** — 18 manual DP day-page spot-checks. Owner reviews each URL. | Low — pure additive test fixture. | None. **Must land first** to give later PRs a parity gate forward in time. |
| **2** | Extract `engines/constants.py` and add `engines/core.py` (parallel, no callers) | New `engines/constants.py` with `SAMVATSARA_KALI_EPOCH_JD = 588465.5` and `SS_KALI_EPOCH_JD_UJJAIN = 588465.5 - 75.7683/360.0`. New `engines/core.py` with `EngineCore`, `Ephemeris`, `MoonCorrection`, `SankrantiPolicy` (per §3). Old engines untouched. Parametrised parity test `tests/test_engine_core_parity.py` runs every existing test fixture through both the old engine and a new `EngineCore.from_drik() / from_ss() / from_vakya()` factory and asserts byte-equal `PanchangamDay`. **Includes bulk benchmark** (365d × 20 cities × 3 engines) in the PR description. | High — must demonstrate byte-equal output on all existing fixtures AND the new forward-year fixture. Also: numerical pinning of both Kali epochs in a dedicated test. | High — large new module; reviewer reads the whole `EngineCore` body. | PR 1 (uses forward-year fixture as parity gate). |
| **3** | Expand festival deciding-moment vocabulary (table-driven Karthika Somavaram / Varalakshmi / Sankashti) | Add `_SANDHYA_FESTIVALS`, `_ARUNODAYA_FESTIVALS`, `_MOONRISE_FESTIVALS`, `_SUNSET_WEEKDAY_FESTIVALS`, `_WEEKDAY_IN_MAASAM_FESTIVALS` rule tables. Convert the three inline-cased festivals (base.py:463-464, 465-469, 472-475) into rule-table entries. **No engine math changes** — diff is line-equivalent. | Medium — re-run the 33-date pinned festival suite from `festival-layer.md` AND the new forward-year matrix; both must remain byte-equal. | Low — purely a refactor inside the festival driver; reviewer compares old-vs-new behavior table. | PR 1 (forward-year tests must already exist). Independent of PR 2 — can land in either order, but landing **after** PR 2 lets PR 3 use `EngineCore.festivals` directly, removing the duplicated rule-driver code path. |
| **4** | Migrate `_festivals` driver into `EngineCore.festivals`, with `facts_at((date, NamedMoment))` enrichment | Move `_festivals` body (base.py:421-484) into `EngineCore.festivals`. Extend `facts_at` signature per §4.2. Internal callers in `EngineCore.festivals` switch from inline JD math to `self.facts_at((date, 'madhyahna'), ...)` etc. Old ABC `_festivals` stays as a thin delegator until PR 7. | Medium — full pinned-festival suite + forward-year + a new `facts_at`-named-moment unit test for each NamedMoment value. | Medium — `facts_at` signature change is a public-API touch; reviewer checks the union-dispatch logic. | PR 2 (`EngineCore` exists) AND PR 3 (rule tables are in their final shape). |
| **5** | Unify `is_sankranti` behind `SankrantiPolicy` and converge on the symmetric window | Replace per-engine `_special_flags is_sankranti` (drik.py:179-183, surya_siddhanta.py:214-216, vakya.py:183-185) with `self.sankranti_policy.is_sankranti(...)`. **Initially keeps current per-engine policies** (Drik=symmetric, SS/Vakya=asymmetric) — pure refactor. **Conditional second commit, behind owner sign-off only**: flip SS and Vakya to `SymmetricSankrantiPolicy` too, unifying with the `_is_makara_day` after-sunset convention used by the festival cluster at base.py:427-432. | **High** — second commit changes a visible chip flag on the deployed SS and Vakya ICS feeds (`feeds/hyderabad-surya-siddhanta.ics`, `feeds/hyderabad-vakya.ics`, …). Owner reviews the diff list of (date, city) cells where `is_sankranti` flips. DP only publishes Drik panchang in practice, so SS/Vakya parity has to be argued on internal consistency grounds, not DP-matched. | High — touches a load-bearing flag consumed by `mcp/tools.py:444` `special_days`. | PR 2 (`SankrantiPolicy` plug point exists) AND PR 4 (festivals driver already unified). |
| **6** | Flip all callers to `EngineCore` factories; keep test-only compat shims | `generators/ics.py`, `mcp/tools.py`, `personal/*`, `gochara/*`, `scripts/*` switch their `DrikGanitaEngine() / SuryaSiddhantaEngine() / VakyaEngine()` calls to the new factory functions (call syntax identical). Keep `ss_elongation`, `vakya_elongation`, `ss_sun_longitude`, `ss_moon_longitude`, `vakya_moon_longitude` as 3-line re-export shims in the original `engines/surya_siddhanta.py` and `engines/vakya.py` files for `tests/test_surya_siddhanta_engine.py:2,57` and `tests/test_vakya_engine.py:2,3`. | Medium — full test suite must pass; bulk-feed regeneration produces byte-equal `.ics` files (modulo PR 5's `is_sankranti` if it landed). | Medium — many small touch sites; reviewer scans for any caller that broke. | PRs 2-5. |
| **7** | Delete old engine method bodies and the `_festivals` delegator | Remove all `_tithi_index_at`, `_tithi_span`, `_nakshatra_span`, `_yoga_span`, `_karana_spans`, `_special_flags`, `_maasam`, `_samvatsara`, `_sun_sign_idx_at`, day-part window methods from `engines/drik.py`, `engines/surya_siddhanta.py`, `engines/vakya.py`. Remove the ABC `_festivals` delegator from `engines/base.py`. Old `PanchangamEngine` ABC stays for `tests/test_base.py:19-22` (`test_engine_is_abstract`) — see §8 risk R1. | Low — all tests already passing post-PR 6; this is pure deletion. | Low — large red diff with no behavioral change. | PR 6. |
| **8** | Convert `is_sankranti` second commit (if not already in PR 5) + final docs | Documentation update: `docs/architecture/engines.md` describes the new shape. `CHANGELOG.md` entry. Reframe `CLAUDE.md` frozen-core text to reflect that the **new** frozen surface is `EngineCore` + its plug-point ABCs, not the three engine classes. | Low — docs-only if PR 5 already flipped. | Medium — `CLAUDE.md` change requires explicit owner sign-off per project rules. | PRs 1-7. |

## 8. Risk register

| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | `tests/test_base.py:19-22` (`test_engine_is_abstract`) asserts `PanchangamEngine()` raises `TypeError`. If we delete the ABC or replace it with concrete `EngineCore`, this test breaks. | High | Certain if not mitigated | **Keep `PanchangamEngine` as the ABC.** `EngineCore` is the implementation that the engine factories return; `PanchangamEngine` becomes a `Protocol`-style structural marker that the test continues to assert against, OR the test is rewritten in PR 7 to assert `EngineCore` requires `ephemeris` to instantiate. Decide before PR 2 lands. |
| R2 | Unifying `is_sankranti` to the symmetric window flips visible chip behavior on deployed SS/Vakya ICS feeds. DP only publishes Drik panchang, so we cannot DP-verify the SS/Vakya direction — the argument is internal-consistency-with-`_is_makara_day` only. | High | Medium (real semantic shift, but on a flag few users notice) | Land PR 5 as **two commits**, gated by separate owner sign-off. First commit: pure refactor (per-engine policies preserved). Second commit: convergence. Diff the full set of cities × 2 years of `is_sankranti`-bearing days against the current shipped feeds; surface the (date, city) list to owner before merge. |
| R3 | Caching regression: the `lru_cache` on composite `moon_sun_elongation` (engines/utils.py:38-60) becomes dead code under `EngineCore.elongation`. Bulk feed generation runs 365 days × 20 cities × 3 engines ≈ 22 000 day-computations. | Medium | Medium | Benchmark required in PR 2 description. If degradation >5%, add a module-level `_cached_elongation(eph_id, corr_id, jd)` keyed by `id(ephemeris) + id(moon_correction)` that `EngineCore.elongation` delegates to. |
| R4 | `_KALI_EPOCH_JD` ambiguity. Two different constants in two files. New `engines/core.py` could import the wrong one. | Medium | Medium | PR 2 explicitly extracts both to `engines/constants.py` under distinct names AND adds a numerical pinning test. |
| R5 | Eclipse-via-Swiss inconsistency made more visible by `Ephemeris` abstraction. Reviewer asks "why doesn't SS eclipse use SS mean motions?" mid-PR. | Low | High (will come up) | PR 2 description explicitly carves it out: "EngineCore + Ephemeris does NOT own eclipse computation. SS and Vakya continue to emit Swiss-derived eclipse times, matching today's behavior. Out of scope for Phase 6." |
| R6 | Frozen-core gate (`CLAUDE.md`). Owner may reject the whole refactor as "rework for its own sake" given the project is `project-done-baseline.md` (2026-06-11). | High | Medium | The justification rests on PRs 3 and 5: PR 3 is the `CLAUDE.md`-permitted "append-festival-rule" pattern applied to fix three inline-cased festivals (a code-quality cleanup the owner can take or leave); PR 5 is a genuine behavioral inconsistency (two sankranti conventions in one engine output). Phase 6 is **not** "rework for the sake of architecture"; it is "fix R5's inconsistency AND ship the table-driven festival rule the docs already promise". If the owner says no, the only PR that ships is PR 1 (the forward-year pin), which is valuable regardless. |
| R7 | `dataclass(frozen=True)` + subclassing footgun. If we ever extend `EngineCore` rather than compose, `object.__setattr__` is required in every subclass `__init__`. | Low | Low | Plan commits to factory functions returning `EngineCore` instances. Subclassing is explicitly disallowed in the docstring. |
| R8 | Forward-year DP dates drift (DP updates its own algorithm between now and 2028 ingestion). | Low | Low | Forward-year fixture pinned to a specific DP scrape date; failure surfaces as a clear test diff that the operator investigates. Not a code defect. |
| R9 | `mcp/tools.py:444` `special_days` consumer relies on the exact `is_sankranti` dict key. PR 5 second commit doesn't rename it, but adjacent diff noise could confuse reviewers. | Low | Low | PR 5 explicitly does not touch any dict keys, only the boolean value computation. Reviewer-aimed comment in the PR. |

## 9. Open decisions — RESOLVED 2026-06-16

All five decisions from the original plan, with the owner's verdicts:

| # | Question | Verdict | Notes |
|---|---|---|---|
| 1 | Does CLAUDE.md frozen-core rule permit Phase 6? | **Narrow scope** | Owner: "YES IN GENERAL" — but only the two visible-value PRs proceed. The architectural refactor (PRs 2, 4–8 of original) is parked; CLAUDE.md stays as-is until/unless a real driver appears. |
| 2 | Should SS/Vakya `is_sankranti` converge to Drik's symmetric window? | **No — leave alone** | Owner: "I am not sure what can be a good baseline for us to decide on this." Resolution: no clean baseline exists (DP only publishes Drik panchang; classical SS/Vakya sources disagree on civil-day convention; Telugu/Tamil traditions differ). Documenting the three-convention reality in `ARCHITECTURE.md` is sufficient. Revisit only if a devotee reports a real issue. |
| 3 | Should `facts_at` accept named deciding moments? | **Dropped** | Owner: "What does this mean?" — once explained as an internal convenience for the rule-table iterator (PR 4 of original), and given PR 4 is now parked, this signature change has no driver. Drop entirely. |
| 4 | Should `Ephemeris` abstraction own eclipse computation? | **Non-goal, documented** | Owner: "SS and Vakya systems tend to differ with Drik. I am not sure if you are trying to baseline everything to modern astronomy, Drik basis." Clarified: the project intentionally exposes three engines so traditionalists can choose; the refactor would NOT have made SS/Vakya output the same as Drik (longitude functions stay distinct). Eclipses today silently use Swiss-derived times in SS/Vakya — this inconsistency is a one-line acknowledgement in `ARCHITECTURE.md`, not a fix. |
| 5 | Factory functions vs subclasses for engine names? | **Moot** | With the refactor parked, the existing class structure stays. Question disappears. |

**Ayanamsa (new, raised by owner 2026-06-16):** Confirmed Drik uses Lahiri (`engines/utils.py:32 — swe.set_sid_mode(swe.SIDM_LAHIRI)`). This is the Indian Astronomical Ephemeris standard and the same default Drik Panchang uses. No change planned.

---

## A. Parked work (full `EngineCore` refactor)

Everything in §3 (`EngineCore` design), §4 (`facts_at` refactor), §5.2 / §5.3 (vocabulary expansion beyond what PR 2 needs), and §7-OLD (the 8-PR breakdown) is preserved as analysis for a future re-opening — for example:

- A user requests an additional ayanamsa engine (Krishnamurti, Raman, true Chitrapaksha)
- A devotee reports an `is_sankranti` bug on SS or Vakya feeds that traces to the three-convention disagreement
- A new contributor is willing to take on the refactor for its own sake and the maintainer is willing to absorb the review burden

If any of these happens, this doc is the starting point — §2 (current state map) and §3 (proposed shape) remain accurate as long as the engine code itself hasn't drifted materially. Re-verify file:line refs before acting.
