# 02 · Engines & the `PanchangamDay` Model

The engine layer is the project's core. All three engines share one base class
and emit one object. The whole trick: **the base class derives every anga from
just two functions — a Sun-longitude function and a Moon-longitude function.**
Each engine differs *only* in how it computes those two longitudes.

- Code: `telugu_panchangam/engines/{base,drik,surya_siddhanta,vakya,utils}.py`
- Model: `telugu_panchangam/models/panchangam_day.py`

---

## The three engines at a glance

| | **Drik Ganita** | **Surya Siddhanta** | **Vakya** |
|---|---|---|---|
| Source of positions | Swiss Ephemeris (true positions, aberration + nutation) | Mean motion + *manda* (epicyclic) correction | SS Sun **+** tabulated Moon correction |
| Class | subclasses `PanchangamEngine` | subclasses `PanchangamEngine` | subclasses **`SuryaSiddhantaEngine`** |
| Reference frame | sidereal via ayanamsa | Kali epoch (3102 BCE) | Kali epoch |
| Ayanamsa param | **applied** (Lahiri / Raman / KP / true Chitrapaksha) | accepted, **no-op** | accepted, **no-op** |
| Outer planets (Guru/Shukra) | **yes** (Simha-stha, Maudhya) | no | no |
| Accuracy (modern) | highest (matches Drik Panchang) | classical, drifts over centuries | middle ground |
| Best for | modern apps, accurate sky events | classical siddhantic tradition | Telugu/Tamil printed panchangams |
| Overrides | every anga method | every anga method | **only Moon-touching methods** |

The Moon-touching methods Vakya overrides: `_moon_longitude_func`,
`_tithi_index_at`, `_tithi_span`, `_nakshatra_span`, `_yoga_span`,
`_karana_spans`, `_special_flags`, `_maasam`. Everything else (windows,
festivals, Sun) it inherits from Surya Siddhanta.

---

## How each engine computes longitude

**Drik** (`drik.py:47–70`) — Swiss Ephemeris. For Lahiri (default) it uses the
`@lru_cache`d `sun_longitude(jd)` / `moon_longitude(jd)` (`utils.py:70,75`); for
other ayanamsas it calls `sidereal_longitude_with_ayanamsa(jd, planet, ayanamsa)`
(`utils.py:23`), which sets the swisseph sid-mode and **restores Lahiri after
each call** so the hot-path cache stays consistent. It additionally computes
Jupiter & Venus longitudes after building the day, for Simha-stha and Maudhya
(`drik.py:404–426`), and derives the sunrise lagna (via
`personal/lagna_hora.get_lagna_transitions`) to populate Panchaka Rahita
(`drik.py:390–403`).

**Surya Siddhanta** (`surya_siddhanta.py:46–68`) — closed-form classical math:

```text
ka          = jd − KALI_EPOCH_JD
mean_long   = (ka · REVS / CIVIL_DAYS · 360) mod 360
anomaly     = (mean_long − apogee) mod 360
circumf     = base − 0.333·|sin(anomaly)|        # Sun base 14, Moon base 32
correction  = asin( (circumf / 360) · sin(anomaly) )   # manda correction
true_long   = (mean_long − correction) mod 360
```

Exposed as module functions `ss_sun_longitude`, `ss_moon_longitude`,
`ss_elongation`. Independent of swisseph ayanamsa.

**Vakya** (`vakya.py:32–37`) — SS Sun unchanged; Moon gets an additive,
table-driven correction that oscillates ±1° over a ~248-year cycle to mimic apse
drift:

```text
idx        = int(|jd − KALI_EPOCH_JD| / CYCLE_DAYS) mod len(CORRECTIONS)
moon_long  = (ss_moon_longitude(jd) + CORRECTIONS[idx]) mod 360
```

### From two longitudes to every anga

The base class (`base.py`) turns the Sun/Moon functions into angas by
**bisection on a monotonic longitude function** (`utils.find_crossing`,
`utils.py:92`):

- **Tithi** — `int(elongation / 12°) mod 30`; span found by bisecting elongation.
- **Nakshatra** — `int(moon_long / 13°20′)`; span by bisecting moon longitude.
- **Yoga** — `int((sun+moon) / 13°20′)`; span by bisecting the sum.
- **Karana** — half-tithis (6° of elongation each); up to 2 between sunrise/sunset.
- **New-moon finders** — `previous_new_moon` / `next_new_moon` use iterative
  mean-elongation refinement (~12.19°/day) to dodge wrap-around near full moon.

Windows (Rahu Kalam, Gulika, Yamagandam, Brahma/Abhijit Muhurta, Choghadiya,
Durmuhurtham) are weekday-keyed divisions of the sunrise→sunset (or
sunset→next-sunrise) span — pure helpers shared by all three engines.

---

## Festival rules (the one place engines may grow)

`base.py` holds the festival dispatcher `_festivals(...)` (`base.py:496–575`) and
**nine named rule tables**. Per the working agreement, *appending a row here with
a DP-verified test is the only routine engine change allowed.*

| Table | Deciding moment | Pattern → example |
|-------|-----------------|-------------------|
| `_SUNRISE_FESTIVALS` | sunrise | (maasam, tithi) → Hanuman Jayanti, Guru Pournami |
| `_MADHYAHNA_FESTIVALS` | midday | (maasam, tithi) → Ugadi, Sri Rama Navami |
| `_APARAHNA_FESTIVALS` | afternoon (0.7·day) | (maasam, tithi) → Vijayadashami |
| `_PRADOSHA_FESTIVALS` | after sunset | (maasam, tithi) → Deepavali |
| `_NISHITA_FESTIVALS` | midnight | (maasam, tithi) → Maha Shivaratri |
| `_WEEKDAY_IN_MAASAM_FESTIVALS` | every matching weekday | (maasam, weekday) → Karthika Somavaram |
| `_LAST_WEEKDAY_IN_PAKSHAM_FESTIVALS` | last weekday in paksha | (maasam, weekday, paksham) → Varalakshmi Vratam |
| `_MOONRISE_MONTHLY_FESTIVALS` | tithi at moonrise | (tithi) → Sankashti Chaturthi |
| `_NISHITA_MONTHLY_FESTIVALS` | tithi at nishita | (tithi, suppress-if) → Masa Shivaratri |

---

## The `PanchangamDay` field reference

The canonical output object. Grouped logically; every consumer reads from here.

### Identity & configuration
| Field | Type | Meaning |
|---|---|---|
| `date` | `date` | Civil date |
| `location` | `Location` | name, lat, lon, timezone, altitude |
| `system` | `str` | `drik` / `surya_siddhanta` / `vakya` |

### Core metadata
| Field | Type | Meaning |
|---|---|---|
| `samvatsara` | `str` | 60-year-cycle name; flips at Ugadi |
| `ayanam` | `str` | Uttarayanam / Dakshinayanam |
| `rituvu` | `str` | Tropical season (uses **tropical** Sun) |
| `maasam` | `str` | Lunar month; `Adhika`/`Nija` prefix for intercalary |
| `paksham` | `str` | Shukla (waxing) / Krishna (waning) |

### The five angas
| Field | Type | Meaning |
|---|---|---|
| `tithi` | `Span` | Lunar day, with start/end |
| `vaaram` | `str` | Weekday (sunrise-anchored, constant across the day) |
| `nakshatra` | `Span` | Lunar mansion, with start/end |
| `yoga` | `Span` | Nitya yoga, with start/end |
| `karana` | `list[Span]` | Active half-tithis between sunrise & sunset |

### Sky & signs
`sunrise` · `sunset` · `moonrise` · `moonset` (all UTC `datetime`) ·
`solar_sign` · `lunar_sign` (sidereal rasi `str`).

### Auspicious windows
`brahma_muhurta` (`Window`) · `abhijit_muhurta` (`Window | None`, omitted Wed) ·
`amrita_kalam` (`list[Window]`).

### Inauspicious windows
`rahu_kalam` · `gulika_kalam` · `yamagandam` (each `Window`) ·
`varjyam` · `durmuhurtham` (each `list[Window]`).

### Choghadiya
`choghadiya` (`list[Window]`) — 8 weekday-keyed day blocks, each auspicious or not.

### Special-day flags
`is_ekadashi` · `is_amavasya` · `is_pournami` · `is_pradosham` ·
`is_shani_pradosham` · `is_soma_pradosham` · `is_sankranti` (all `bool`).

### Festivals & events
`festivals` (`list[str]`) · `special_yogas` (`list[str]`) ·
`special_notes` (`list[str]`) · `eclipse` (`EclipseInfo | None`) ·
`sankramanam` (`str | None` — rasi the Sun enters today).

### Additive timing fields (1.9.0)
| Field | Type | Engine | Meaning |
|---|---|---|---|
| `ghati_clock` | `GhatiClock \| None` | all | sunrise-anchored 60-ghati scale |
| `nakshatra_pada` | `int \| None` | all | pada (1–4) of the sunrise nakshatra |
| `vishaghati` | `list[GhatiWindow]` | all | per-nakshatra "poison ghatika" windows |
| `bhadra_mukha` / `bhadra_puchha` | `GhatiWindow \| None` | all | Vishti-karana mouth / tail |
| `sankramana_avoidance` | `Window \| None` | all | ±16 ghatis around the Sun's ingress |
| `in_panchaka_nakshatra` | `bool` | all | sunrise nakshatra is one of the 5 Panchaka |
| `is_khar_maasa` / `khar_maasa_name` | `bool` / `str?` | all | Sun in Dhanu / Meena |
| `is_pitru_paksha` | `bool` | all | Bhadrapada Krishna paksha |
| `anandadi_yoga` | `str \| None` | all | one of 28 vaaram×nakshatra muhurta yogas |
| `disha_shoola_direction` | `str \| None` | all | weekday's blocked travel direction |
| `nakshatra_mukha` | `str \| None` | all | Adho / Urdhva / Tiryan facing |
| `panchaka_rahita` | `PanchakaInfo \| None` | all | mod-9 dosha (needs sunrise lagna) |
| `simha_stha_guru` / `simha_stha_shukra` | `bool` | **Drik only** | Jupiter / Venus in Simha |
| `guru_maudhya` / `shukra_maudhya` | `MaudhyaInfo \| None` | **Drik only** | Jupiter / Venus combustion |

> SS and Vakya don't model outer planets, so the four Drik-only fields stay
> `False`/`None` there — by design, not omission.

---

## `utils.py` — the shared toolbox

- **Ayanamsa** — `AYANAMSA_MODES` dict, `_validate_ayanamsa`,
  `sidereal_longitude_with_ayanamsa` (sets mode, computes, restores Lahiri).
- **JD** — `datetime_to_jd`, `jd_to_utc`, `local_midnight_jd`.
- **Cached longitudes** (`@lru_cache(maxsize=1024)`) — `sidereal_longitude`,
  `sun_longitude`, `moon_longitude`, `moon_sun_elongation`,
  `tropical_sun_longitude` (the last drives `rituvu`).
- **Rise/set** — `get_sunrise/sunset/moonrise/moonset` via swisseph `rise_trans`
  (1013.25 hPa, 15° visual horizon).
- **Crossing finder** — `find_crossing(func, target, jd_start, jd_end)` binary
  search (≤60 iters, 180° wrap for stability), the workhorse for anga boundaries.
- **New-moon finders** — `previous_new_moon`, `next_new_moon`.

See [doc 06](06-roadmap-and-backlog.md) for the parked `EngineCore` unification
that would collapse the three engines into one core consuming
`(sun_fn, moon_fn, ayanamsa_fn)`.
