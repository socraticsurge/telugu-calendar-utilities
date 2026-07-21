# 03 · Computational Features

Every jyotisha computation the project performs, beyond the five core angas.
These are standalone modules that **consume** engine output (or raw ephemeris)
and produce a derived result — a window, a flag, a verdict, a calendar. Grouped
by theme. Each row: what it computes · classical source · where it surfaces.

> Many of these populate the [`PanchangamDay` additive fields](02-engines-and-model.md#additive-timing-fields-190)
> and feed the [muhurta scorer](05-data-flow-and-muhurta.md). The five
> calendar-style ones (combustion, graha yuddha, ingress, eclipse, shuddhi) are
> exposed directly as [MCP tools](04-user-facing-features.md).

---

## Group 1 — Ghati-precision timing

The traditional day runs sunrise→next-sunrise, divided into 60 *ghatis*
(1 ghati ≈ 24 min, scaled by latitude/season); each ghati = 60 *vighatis*.
Several filters are only expressible on this scale.

| Module | Computes | Source | Surfaces as |
|---|---|---|---|
| `ghati.py` | `GhatiClock` / `GhatiWindow` — civil↔ghati conversion, sunrise-anchored | Surya Siddhanta | `PanchangamDay.ghati_clock`; foundation for the two below |
| `karana_windows.py` | **Vishaghati** ("poison ghatika") — 4-vighati window per nakshatra at a classical offset; **Bhadra Mukha/Puchha** — Vishti-karana split into Mukha (first 5/16, hard-avoid), body, Puchha (last 3/16, auspicious for contests/litigation) | Muhurta Chintamani; Dharma Sindhu | `vishaghati`, `bhadra_mukha`, `bhadra_puchha` |
| `sankramana.py` | Sun's rasi-ingress avoidance — ±16 ghatis around the exact crossing (~12h48m) | classical samskara rule | `sankramana_avoidance` |

---

## Group 2 — Nakshatra & yoga filters

| Module | Computes | Source | Surfaces as |
|---|---|---|---|
| `special_yogas.py` | **Anandadi 28 yogas** (vaaram×nakshatra → Ananda…Vardhamana, 16 auspicious / 12 not); **Sarvartha Siddhi**, **Amrita Siddhi**; **Siddha Yoga** (all five Tithi×Vara pairs: Nanda+Fri, Bhadra+Wed, Jaya+Tue, Rikta+Sat, Purna+Thu); **Visha** & **Dagdha** (avoid); **Dvipushkara/Tripushkara** | Muhurta Chintamani, B.V. Raman Muhurtha | `anandadi_yoga`, `special_yogas[]`; scorer ±1/±2 |
| `nakshatra_filters.py` | **5 Panchaka nakshatras** (Dhanishtha…Revati — cremation/roof/wood avoid); **Mukha direction** (Adho/Urdhva/Tiryan → foundations / coronation / travel) | classical samskara texts | `in_panchaka_nakshatra`, `nakshatra_mukha` |
| `panchaka.py` | **Panchaka Rahita** — mod-9 dosha on (tithi+vaaram+nakshatra+lagna): remainder → Rahita (good) / Mrityu / Agni / Raja / Chora / Roga, each with an `avoid_for` activity list | Muhurta Chintamani, Dharmasindhu | `panchaka_rahita` (needs sunrise lagna); recomputed per slot |
| `panchanga_shuddhi.py` | **Five-limb purity** — grades each of Tithi/Vaara/Nakshatra/Yoga/Karana shuddha/ashuddha/mixed → verdict Sarva Shuddha … Sarva Ashuddha (0–5 count) | Muhurta Chintamani, Dharma Sindhu | MCP `get_panchanga_shuddhi` |

---

## Group 3 — Solar/lunar maasa & special periods

| Module | Computes | Source | Surfaces as |
|---|---|---|---|
| `maasa_filters.py` | **Khar-Maasa** — Sun in Dhanu or Meena (samskaras, esp. marriage, avoided) | classical samskara texts | `is_khar_maasa`, `khar_maasa_name` |
| `pitru_paksha.py` | **Pitru Paksha** — Bhadrapada Krishna paksha (ancestral fortnight; samskaras forbidden) | Kalpa Sutras, Dharma Sindhu | `is_pitru_paksha` |
| `disha_shoola.py` | **Disha Shoola** — weekday → blocked travel direction | classical muhurta texts | `disha_shoola_direction`; gates `travel` muhurta |

---

## Group 4 — Graha-based (transit / combustion / war)

| Module | Computes | Source | Surfaces as |
|---|---|---|---|
| `gochara/positions.py` | Sidereal positions of all **9 grahas** at a JD — longitude, rasi, nakshatra, pada, retrograde, next ingress date; ayanamsa-configurable | Vedic astrology | MCP `get_graha_positions`; basis for gochara & phalalu |
| `gochara/rules.py` | **Gochara verdicts** from a janma rasi — favourable / blocked-by-vedha / adverse, plus named conditions (Sade Sati, Ashtama/Ardhastama Shani) | Brihat Samhita 104.4 for seven classical favourable-house sets; other layers retain explicit locator debt | MCP `get_gochara` |
| `gochara/combustion.py` | **Guru/Shukra Maudhya** — combustion thresholds (Jupiter 11°, Venus 10°) | Brihat Samhita, Muhurta Chintamani | `guru_maudhya`, `shukra_maudhya` (Drik) |
| `gochara/simha_stha.py` | **Simha-stha** — Jupiter or Venus in Simha (wedding restriction; Guru hard, Shukra penalty) | classical samskara tradition | `simha_stha_guru/shukra` (Drik) |
| `maudhya_calendar.py` | **All-planet Asta/Udaya** — heliacal setting & rising for Mercury/Venus/Mars/Jupiter/Saturn via swisseph `heliacal_ut()`, per-city | BPHS | MCP `get_combustion_calendar` |
| `graha_yuddha.py` | **Planetary war** — two tara grahas within 1° ecliptic longitude; victor by higher latitude; entry/exit by binary + ternary search | Surya Siddhanta, BPHS | MCP `get_graha_yuddha` |

---

## Group 5 — Calendars & events

| Module | Computes | Source | Surfaces as |
|---|---|---|---|
| `ingress.py` | **Rashi ingress calendar** — every sign change for 8 planets (Moon excluded) over a range, incl. retrograde re-entries; sidereal | Vedic astrology | MCP `get_rashi_ingresses` |
| `eclipses.py` | **Solar/lunar eclipses** with per-location visibility + **Sutak** (12h solar / 9h lunar before end, only if visible); precomputed once per generation run | classical computation; Dharma Sindhu (Sutak) | `PanchangamDay.eclipse`; MCP `get_eclipse_calendar` |
| `cities.py` | **City registry** — 22 pre-configured `Location`s (Telugu heartland, Indian metros, diaspora) | geographic data | location resolver; feed generation |

---

## How they combine

- **Hard filters** (return *no slots* for a day): eclipse, Disha Shoola match,
  Panchaka nakshatra for cremation/roof/wood, Khar-Maasa / Adhika / Pitru
  Paksha / Simha-stha Guru / Guru-Shukra combustion for samskaras, Visha/Dagdha
  & Vyatipata/Vaidhriti for samskaras.
- **Score modifiers** (±points): Anandadi, special yogas, Vishaghati & Bhadra
  Mukha cut slots, Bhadra Puchha & Nakshatra Mukha grant bonuses, Panchaka
  Rahita caps tier.

The full combination logic lives in the muhurta scorer —
[doc 05](05-data-flow-and-muhurta.md).
