# Engines and the `PanchangamDay` computation contract

This document describes what the repository computes today. It is not a claim
that every convention is textually authoritative or independently verified.
Evidence states come from [`provenance.json`](provenance.json); stable
computation IDs come from [`computations.json`](computations.json).

## Assurance key

- **Source-traced** means the implementation has an inspected technical or
  textual source with an exact locator.
- **Independently compared** means a value was checked against a separate
  published result for the same date and location.
- **Regression-pinned** means tests preserve current output. It does not prove
  that the output is correct outside those test cells.
- **Unresolved** means the implementation or convention still needs source or
  comparison work. The gap is named rather than hidden.

The current high-level evidence states are:

| Layer | State | Provenance claim |
|---|---|---|
| Drik sidereal positions | Partially verified | `drik.sidereal_positions` |
| Surya Siddhanta longitude model | Source-traced in part; output engine-pinned | `surya_siddhanta.mean_motion_manda`, `panchangam.non_drik_engine_outputs` |
| Vakya longitude model | Provisional and engine-pinned | `vakya.provisional_lunar_model` |
| Rise/set convention | Implementation traced; target convention unresolved | `panchangam.rise_set_convention` |
| Calendar naming and rollover semantics | Needs criterion-level locators | `panchangam.calendar_semantics` |
| Daily windows | Mixed, partially verified container | `panchangam.mixed_daily_windows` |

## End-to-end calculation

For `calculate(date, location, include_eclipse)` each engine follows this flow:

1. `local_midnight_jd` localizes civil midnight in `location.timezone`, converts
   it to UTC and then to a Universal-Time Julian day.
2. Shared Swiss Ephemeris helpers find the first sunrise and Moon rise/set after
   that local midnight, sunset after sunrise, and the next sunrise from the next
   local midnight.
3. The selected engine evaluates Sun and Moon longitudes at sunrise.
4. The engine derives the five angas, their applicable spans, signs, Paksham,
   Maasam, Samvatsara and special-day flags.
5. Shared helpers derive windows, festivals and additive classifications.
6. The result is returned as `PanchangamDay`. Datetimes are timezone-aware UTC;
   presentation layers convert them for display.

The three `calculate` methods are separate implementations, not a single shared
calculation method. The base class owns shared helpers and per-instant
`facts_at`, but it does not derive the complete day from two polymorphic
longitude functions. This distinction matters when comparing the engines.

## Time, units and boundary contract

| Concern | Current behavior |
|---|---|
| Input date | A civil `date` interpreted in the supplied IANA timezone. |
| Core time scale | Universal-Time Julian day as a floating-point number. One unit is one day. |
| Returned datetimes | UTC, timezone-aware, truncated to whole seconds by `jd_to_utc`; not rounded. |
| Panchangam day | Most day windows use `[sunrise, next sunrise)`. Daytime windows use `[sunrise, sunset]`. The stored `date` remains the input civil date. |
| Longitude | Degrees normalized to `[0, 360)`. |
| Span transitions | Located with `find_crossing`, at most 60 bisections and a default Julian-day tolerance of `1e-8` (about 0.864 ms), then exposed at whole-second precision. |
| Weekday | `int(jd_sunrise + 1.5) % 7`, where 0 is Sunday; it is fixed for the Panchangam day. |
| High-latitude failures | Swiss Ephemeris return codes are currently ignored. The configured city set avoids polar no-event cases, but the helper contract does not safely represent them. |

### Rise and set are shared, not engine-specific

`get_sunrise`, `get_sunset`, `get_moonrise` and `get_moonset` call Swiss
Ephemeris `rise_trans` for all three systems. The call currently uses:

- only `CALC_RISE` or `CALC_SET`;
- longitude and latitude, with altitude forced to `0.0` metres;
- pressure `1013.25` hPa and temperature `15.0` °C;
- the default astronomical upper-limb/refraction convention.

Swiss Ephemeris Programmer's Documentation sections 8.12 and 8.12.1 distinguish
that default from its Hindu-calendar disc-centre/no-refraction mode. The project
has not yet recorded a multi-city comparison that decides which convention its
public Panchangam should promise. That work is tracked in
[#177](https://github.com/socraticsurge/telugu-calendar-utilities/issues/177).
Until it is resolved, do not describe these four fields as a verified Hindu
sunrise convention.

Technical source: [Swiss Ephemeris Programmer's Documentation](https://www.astro.com/swisseph/swephprg.htm),
sections 3, 5.8, 8.12, 8.12.1 and 12.2.

## The three longitude models

### Drik Ganita

Owner: `DrikGanitaEngine` in `telugu_panchangam/engines/drik.py`.

`_sun_lon` and `_moon_lon` call Swiss Ephemeris `calc_ut` with
`FLG_SWIEPH | FLG_SIDEREAL`, returning geocentric ecliptic longitude under the
selected sidereal mode. Lahiri is the default and uses cached helpers. Raman,
Krishnamurti and True Chitrapaksha bypass that cache, set the requested global
Swiss sidereal mode, calculate the longitude and restore Lahiri afterward.

The selected ayanamsa changes Drik Sun/Moon longitudes and downstream angas,
signs, Maasam and ingress times. It also changes the Drik-only Jupiter and Venus
positions used for Simha-stha and Maudhya. The Swiss documentation supports the
API and flag semantics; representative repository tests and published day cells
support only partial output verification.

### Surya Siddhanta

Owner: `SuryaSiddhantaEngine` in
`telugu_panchangam/engines/surya_siddhanta.py`.

The implementation is a bounded modern transcription of mean motion plus one
manda correction, not a complete implementation of every Sūrya Siddhānta
procedure:

```text
ahargana       = jd - 588465.5
mean_longitude = (ahargana * revolutions / 1,577,917,828 * 360) mod 360
anomaly        = (mean_longitude - apogee) mod 360
circumference  = even - (even - odd) * abs(sin(anomaly))
manda          = asin((circumference / 360) * sin(anomaly))
true_longitude = (mean_longitude - manda) mod 360
```

The Sun uses 4,320,000 revolutions, a fixed apogee of 77.333° and epicycle
circumferences 14°/13°40′. The Moon uses 57,753,336 revolutions, a moving apogee
of 488,219 revolutions plus 90° at the code epoch, and circumferences
32°/31°40′.

The source crosswalk is Ebenezer Burgess and William Dwight Whitney,
*Translation of the Sûrya-Siddhânta*, Journal of the American Oriental Society
6 (1860): chapter I verses 29–34 and 53 for revolution counts and mean place;
chapter II verses 29–39 for anomaly, epicycle dimensions and manda equation.
The code uses direct floating-point trigonometry and fixed/simplified constants,
so this locator supports the algorithm family, not a claim of complete textual
fidelity or modern astronomical accuracy.

Tests bound the 2026 sample Sun difference from the Drik model below 1° and the
Moon difference below 5.5°. That is a cross-model regression check, not an
independent published Surya Siddhanta Panchangam comparison.

The constructor accepts an ayanamsa name for API symmetry and validation, but
the selected name does not change any Surya Siddhanta output.

### Vakya

Owner: `VakyaEngine` in `telugu_panchangam/engines/vakya.py`.

The current implementation keeps the Surya Siddhanta Sun and adds one of nine
offsets (`0`, `+0.5`, `+1`, `+0.5`, `0`, `-0.5`, `-1`, `-0.5`, `0` degrees) to
the Surya Siddhanta Moon. The phase index is
`int(abs(jd - 588465.5) / 3031) % 9`.

This is a provisional project model. It is not a registered transcription of a
248-entry lunar-vākya table, and 3,031 days must not be described as a 248-year
cycle. Source reconstruction and a possible frozen-core correction are tracked
in [#176](https://github.com/socraticsurge/telugu-calendar-utilities/issues/176).
Current tests prove range, shape and regression behavior only.

Like Surya Siddhanta, Vakya accepts but does not apply the ayanamsa parameter.

## Pancha anga formulas and transition spans

Let `S` be the engine's Sun longitude, `M` its Moon longitude and
`E = (M - S) mod 360` at a Universal-Time Julian day.

| Anga | Sunrise value | Stored transition semantics | Owners |
|---|---|---|---|
| Tithi | `floor(E / 12°) mod 30` | `tithi` is the Tithi active at sunrise. Start is bisected in `[sunrise-2d, sunrise]`; end in `[sunrise, sunrise+2d]`. | Engine `_tithi_index_at`, `_tithi_span` |
| Vaaram | Sunrise Julian weekday | `vaaram` is one name for the entire Panchangam day; it does not flip at civil midnight. | each engine `calculate` |
| Nakshatra | `floor(M / (360°/27)) mod 27` | `nakshatra` is active at sunrise. Start/end use the engine's Moon model and ±2-day search windows. | engine `_nakshatra_span` |
| Nitya Yoga | `floor(((S+M) mod 360) / (360°/27)) mod 27` | `yoga` is active at sunrise with the same ±2-day crossing windows. | engine `_yoga_span` |
| Karana | `floor(E / 6°) mod 60` | Up to two spans intersecting sunrise–sunset are returned in `karana`. Spans are not clipped to the daylight interval. Fixed and sevenfold repeating names come from `panchangam_names.py`. | engine `_karana_spans` |

`facts_at` derives the same five instant-level names from an engine's exposed
Sun/Moon functions. Callers must pass the day's `vaaram`; its UTC-weekday
fallback is explicitly approximate around the sunrise/civil-day boundary.

## Calendar metadata

| Fields | Algorithm | Implementation | Evidence state |
|---|---|---|---|
| `solar_sign`, `lunar_sign` | Sunrise longitude divided into twelve 30° Rasis. | each engine `calculate` | Follows the engine position state. |
| `paksham` | Tithi indices 0–14 are Shukla; 15–29 are Krishna. | each engine `calculate` | `panchangam.calendar_semantics`; locator debt remains. |
| `maasam` | Find bounding new moons from the engine elongation; name by the Sun sign at the starting new moon. Same Sun sign at start/end gives `Adhika`; same sign at previous/start gives `Nija`. | `maasam_name`, engine `_maasam` | Needs regional criterion-level verification. |
| `samvatsara` | Count 365.25636-day years from JD 588465.5, shift by the lunar-month number so the label flips at Chaitra, then apply offset 12 modulo 60. | `samvatsara_name` | Project convention; needs exact locator. |
| `ayanam` | Sidereal Sun signs Makara through Mithuna map to Uttarayanam; Karkataka through Dhanu to Dakshinayanam. | `ayanam_name` | Needs exact criterion locator. |
| `rituvu` | Tropical Swiss Ephemeris Sun sign selects the six-season name. | `rituvu_name` | Hybrid: all three engines use the same Drik/tropical helper. |

New-moon search uses a 12.19°/day iterative estimate for ten iterations and a
fixed 29.530589-day fallback. Its result is an implementation technique, not a
separately verified astronomical event series.

## Core windows

| Fields | Current calculation | Boundary notes |
|---|---|---|
| `rahu_kalam`, `gulika_kalam`, `yamagandam` | Weekday-selected one-eighth of sunrise–sunset. | Equal temporal eighths; tables use Sunday index 0. |
| `brahma_muhurta` | 96 to 48 clock minutes before sunrise. | Uses fixed fractions of a 24-hour Julian day. |
| `abhijit_muhurta` | Local daylight midpoint ± one-thirtieth of daylight. | Omitted on Wednesday; total length is one-fifteenth of daylight. |
| `choghadiya` | Eight equal daytime blocks with weekday names. | Night Choghadiya is not returned. |
| `durmuhurtham` | Weekday-selected parts of fifteen equal daylight divisions; Tuesday also uses the seventh of fifteen night divisions. | Night is sunset–next sunrise. |
| `varjyam`, `amrita_kalam` | Four-sixtieths of the actual Nakshatra span, starting at its configured ghati. | Consider the sunrise Nakshatra and its successor; return a window only when its start falls in `[sunrise, next sunrise)`. |

These fields form a mixed-evidence container. The exact Raman locators in
`panchangam.mixed_daily_windows` cover Nakshatra Tyajyakala and a Durmuhurta
scheme, while other tables and regional differences remain partially verified
or regression-pinned.

## Festival deciding moments

`PanchangamEngine._festivals` applies shared rule tables using the selected
engine's Tithi and Maasam. Its moment semantics are exact implementation
contracts:

| Rule family | Deciding instant |
|---|---|
| Sunrise | sunrise |
| Madhyahna | `sunrise + 0.5 * daylight` |
| Aparahna | `sunrise + 0.7 * daylight` |
| Pradosha | `sunset + 0.05` Julian day (72 clock minutes) |
| Nishita | midpoint of sunset and next sunrise |
| Monthly Moonrise | Moonrise when it falls between sunset and next sunrise; otherwise `sunset + 0.1` Julian day |
| Weekday in Maasam | sunrise Maasam plus sunrise weekday |
| Last weekday in Paksha | current sunrise Paksha differs from the same weekday seven days later |
| Solar ingress | between sunrise and sunset belongs to that day; after the previous sunset belongs to the next day |

Moment-based rules compare the same instant one Julian day earlier to avoid
double assignment when a Tithi spans two deciding instants. Adhika months skip
the annual lunar festival tables but still admit the monthly vrata tables.

The forward-year fixture contains a mixture of independently checked and
engine-pinned cells. Consult each fixture cell's label; never describe the whole
festival series as independently verified.

## Engine asymmetries and hybrids

| Concern | Drik | Surya Siddhanta | Vakya |
|---|---|---|---|
| Sun/Moon longitude | Swiss sidereal mode | Project SS mean-motion/manda model | SS Sun plus provisional Moon offset |
| Ayanamsa parameter | Applied | Validated, no effect | Validated, no effect |
| Pancha anga spans | Drik-specific methods | SS-specific methods | Vakya overrides every Moon-dependent method |
| Rise/set | Shared Swiss default | Shared Swiss default | Shared Swiss default |
| Rituvu | Shared tropical Swiss Sun | Shared tropical Swiss Sun | Shared tropical Swiss Sun |
| Eclipse | Shared Swiss eclipse calculation | Shared Swiss eclipse calculation | Shared Swiss eclipse calculation |
| Jupiter/Venus flags | Populated | Default `False`/`None` | Default `False`/`None` |
| Festivals and windows | Shared rules fed by Drik facts | Shared rules fed by SS facts | Shared rules fed by Vakya facts |

Consequently, “Surya Siddhanta day” and “Vakya day” do not mean that every
field comes from that astronomical system. Rise/set, Rituvu and eclipse fields
are deliberately shared Swiss-derived hybrids.

## `PanchangamDay` field-to-owner map

Every current model field appears below. “Default” means the dataclass supplies
the initial value until an engine or finalizer replaces it.

| Field group | Fields | Immediate owner |
|---|---|---|
| Request identity | `date`, `location`, `system` | engine `calculate` |
| Calendar metadata | `samvatsara`, `ayanam`, `rituvu`, `maasam`, `paksham` | engine `calculate`; shared naming helpers |
| Five angas | `tithi`, `vaaram`, `nakshatra`, `yoga`, `karana` | engine-specific span methods and `calculate` |
| Sky and signs | `sunrise`, `sunset`, `moonrise`, `moonset`, `solar_sign`, `lunar_sign` | shared rise/set helpers plus engine sunrise longitudes |
| Auspicious windows | `brahma_muhurta`, `abhijit_muhurta`, `amrita_kalam` | base window helpers |
| Inauspicious windows | `rahu_kalam`, `gulika_kalam`, `yamagandam`, `varjyam`, `durmuhurtham` | base window helpers |
| Choghadiya | `choghadiya` | `_choghadiya` |
| Tithi/day flags | `is_ekadashi`, `is_amavasya`, `is_pournami`, `is_pradosham`, `is_shani_pradosham`, `is_soma_pradosham`, `is_sankranti` | engine `_special_flags` |
| Events | `special_notes`, `eclipse`, `special_yogas`, `festivals`, `sankramanam` | default; eclipse/special-yoga modules; base festival/ingress helpers |
| Ghati and Karana additions | `ghati_clock`, `nakshatra_pada`, `vishaghati`, `bhadra_mukha`, `bhadra_puchha` | `_finalize_day`, `ghati.py`, `karana_windows.py` |
| Sankramana and month filters | `sankramana_avoidance`, `in_panchaka_nakshatra`, `is_khar_maasa`, `khar_maasa_name`, `is_pitru_paksha` | `_finalize_day` and dedicated derived modules |
| Drik-only outer-planet fields | `simha_stha_guru`, `simha_stha_shukra`, `guru_maudhya`, `shukra_maudhya` | Drik `calculate`; dataclass defaults for SS/Vakya |
| Other derived classifications | `anandadi_yoga`, `disha_shoola_direction`, `nakshatra_mukha`, `panchaka_rahita` | `_finalize_day` and dedicated derived modules |

The derived rules in the last four rows are documented in
[Computational features](03-computational-features.md) and will receive their
own criterion-level evidence audit under story #167. This document records
their ownership so no model field is orphaned.

## Representative test map

| Contract | Tests |
|---|---|
| Drik day, angas, signs, metadata and ingress | `tests/test_drik_engine.py`, `tests/test_integration.py` |
| Ayanamsa application and no-op boundaries | `tests/test_ayanamsa.py` |
| Surya Siddhanta day and cross-model longitude bounds | `tests/test_surya_siddhanta_engine.py` |
| Vakya day and provisional-offset regression | `tests/test_vakya_engine.py` |
| Shared windows and Maasam helpers | `tests/test_base.py`, `tests/test_muhurta_windows.py` |
| Festival rules and deciding moments | `tests/test_festivals.py`, `tests/test_festivals_forward_year.py` |
| Per-instant facts | `tests/test_engine_facts_at.py` |
| Model shape | `tests/test_models.py` |
| This documentation's links, symbols, fields and claims | `tests/test_engine_documentation.py` |

## Review checklist

When an engine-facing computation changes:

1. Update the stable computation record and this contract in the same PR.
2. State whether the result is regression-pinned, source-traced or independently
   compared; do not promote one state into another.
3. Add exact date, location, system, timezone, input convention and expected
   value to comparison fixtures.
4. Preserve UTC internally and make any display-time conversion explicit.
5. Treat changes under `telugu_panchangam/engines/` as frozen-core changes that
   require owner approval, focused tests, the full project gate and a PyPI
   version bump.
