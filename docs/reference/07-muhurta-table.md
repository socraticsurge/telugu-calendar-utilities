# The 30 Muhurtas — reference table (source of record)

This is the verified reference for the named-muhurta system the muhurta
finder is being rebuilt on. **Do not edit values without owner sign-off**
— every cell here is either owner-confirmed or web-sourced, tagged below.

## What a muhurta is

A **muhurta** is 1/30 of the ahorātra (day-and-night): **15 daytime**
muhurtas from sunrise to sunset, **15 night** muhurtas from sunset to the
next sunrise. Each is ≈48 minutes (2 ghati) at the equinox but is computed
**proportionally** — daytime÷15 and night÷15 — so it expands and contracts
with the season. Each muhurta has a name, most have a presiding deity, and
each has an intrinsic auspicious/inauspicious nature.

This is a **different system from choghadiya** (the 8-fold day/night
division). Both are kept, as scoring inputs — see "Scoring model" below.

## Computation

- **Daytime muhurta length** = (sunset − sunrise) / 15; the *i*-th daytime
  muhurta runs sunrise + (i−1)·len … sunrise + i·len.
- **Night muhurta length** = (next sunrise − sunset) / 15; analogous from
  sunset.
- The engine already computes this division (`_durmuhurtham`,
  `_abhijit_muhurta` in `engines/base.py`). The finder will reuse it rather
  than re-slice.
- **Abhijit** = the **8th daytime** muhurta (straddles solar noon); **none
  on Wednesday** (engine already encodes this).
- **Brahma** = the **14th night** muhurta (pre-dawn). Traditionally also
  given as a fixed 1/30-of-24h window; the engine's existing Brahma
  definition stands.

## Daytime muhurtas (from sunrise)

| # | Muhurta | Presiding deity | Nature |
|---|---------|-----------------|--------|
| 1  | Rudra          | Rudra (fierce Śiva)          | inauspicious |
| 2  | Ahi            | Sarpa / the Serpent (Nāga)   | inauspicious |
| 3  | Mitra          | Mitra (Āditya)               | auspicious |
| 4  | Pitri          | the Pitṛs (ancestors)        | inauspicious |
| 5  | Vasu           | the Vasus                    | auspicious |
| 6  | Vara           | Varāha (boar avatar of Viṣṇu)| auspicious |
| 7  | Vishvedeva     | the Viśvedevas               | auspicious |
| 8  | Vidhi (**Abhijit**) | Brahmā                  | auspicious (most; none on Wed) |
| 9  | Sathamukhi     | — (concept: "fair-faced")    | auspicious |
| 10 | Puruhuta       | Indra (Puruhūta)             | inauspicious |
| 11 | Vahini         | — (concept: "carrier/host")  | inauspicious |
| 12 | Naktanchara    | — (concept: "night-wanderer")| inauspicious |
| 13 | Varuna         | Varuṇa                       | auspicious |
| 14 | Aryama         | Aryaman (Āditya)             | auspicious |
| 15 | Bhaga          | Bhaga (Āditya)               | inauspicious |

## Night muhurtas (from sunset)

| # | Muhurta | Presiding deity | Nature |
|---|---------|-----------------|--------|
| 1  | Girisha        | Śiva (Girīśa)                | inauspicious |
| 2  | Ajapada        | Aja-Ekapāda (a Rudra)        | inauspicious |
| 3  | Ahirbudhnya    | Ahirbudhnya (a Rudra)        | auspicious |
| 4  | Pusha          | Pūṣan (Āditya)               | auspicious |
| 5  | Aswi           | the Aśvins                   | auspicious |
| 6  | Yama           | Yama                         | inauspicious |
| 7  | Agni           | Agni                         | inauspicious |
| 8  | Vidhatru       | Vidhātṛ (the ordainer)       | auspicious |
| 9  | Chanda         | Chandra (Moon)               | auspicious |
| 10 | Aditi          | Aditi                        | auspicious |
| 11 | Jeeva          | Bṛhaspati (Jupiter)          | auspicious (most) |
| 12 | Vishnu         | Viṣṇu                        | auspicious |
| 13 | Yumigadyuti    | — (concept: "brilliance of light") | auspicious |
| 14 | **Brahma**     | Brahmā                       | auspicious (most; Brahma Muhurta) |
| 15 | Samudra        | — (concept: "ocean")         | auspicious |

Intrinsically inauspicious set: **day** 1, 2, 4, 10, 11, 12, 15;
**night** 1, 2, 6, 7. (These are distinct from the weekday-specific
Durmuhurtam the engine already computes — see Scoring model.)

## Scoring model (owner-confirmed)

The finder is an **honest, additive scoring system** — it does not pick one
tradition over another; every applicable factor contributes and is
disclosed to the user. For a chosen activity, a muhurta's score layers:

1. **Intrinsic muhurta nature** (this table) — auspicious/inauspicious base.
2. **Weekday Durmuhurtam** (engine `DURMUHURTA_DAY_MUHURTAS`) — an
   *additional* penalty on the specific muhurta(s) inauspicious for that
   weekday. Additive, not an override.
3. **Choghadiya** (Amrit/Shubh/… — the 8-fold system) — kept as a scoring
   attribute of the muhurta it falls in.
4. **Tarabalam / Chandrabalam / lagna / tithi-class / special yogas** — as
   already implemented.

**"Good for [event]" is not a per-muhurta attribute** — it is answered by
the finder's source-profile activity catalogue (`ACTIVITY_RULES`): the user selects
the event (wedding, gruhapravesha, travel, surgery, …) and the finder scores
muhurtas for it. No per-muhurta activity list is invented.

## Provenance

- **Muhurta names (all 30) + Brahma at night-14** — owner-confirmed (B.V.
  Raman, *Muhurtha*).
- **Chanda deity (Moon) + nature (auspicious)** — owner-ruled.
- **Vara → Varāha; Yumigadyuti, Samudra natures** — web-sourced.
- **Day natures; night natures (except Chanda)** — web-sourced, consistent
  across sources; pending final owner read.
- **Deity-vs-concept distinction** — several names are abstractions, not
  deities (Taittirīya-brāhmaṇa, per wisdomlib); a blank deity cell is
  intentional, not missing data.

Sources: B.V. Raman *Muhurtha*; wisdomlib.org/definition/muhurta;
onlinejyotish.com; ganeshmitra.co.in/30-muhurta; instaastro.com/muhurat;
chamundaswamiji.com; anustubhblog.wordpress.com.
