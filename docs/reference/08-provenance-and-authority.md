# Provenance & Authority

This is the trust contract for every astrological statement made by the
project. A computed fact, a textual rule, a regional convention, and a project
heuristic are different kinds of claim. None inherits the authority of another
merely because they appear in the same response.

The machine-readable companion is [`provenance.json`](provenance.json). Tests
validate its vocabulary, identifiers, source references, and evidence gaps.

## Evidence classes

| Class | Meaning | Suitable user-facing language |
|---|---|---|
| `astronomical` | Computed from an ephemeris or documented astronomical algorithm | "computed", with system and ayanamsa |
| `textual` | A rule attested in an identified textual edition at a precise locator | "according to [text/tradition]" |
| `published_panchangam` | Compared with a named external panchangam for a date and place | "externally verified" only for the recorded cells |
| `regional_convention` | A living or regional practice that is not universal | "in the configured Telugu/South Indian tradition" |
| `project_heuristic` | A product scoring or presentation choice | "project score/rank", never "scripturally ordained" |

## Verification states

| State | Meaning |
|---|---|
| `verified` | Evidence has been inspected and a precise locator or comparison record exists |
| `partially_verified` | Some representative cases or part of the claim have been checked |
| `engine_pinned` | A regression test preserves current output; it is not independent verification |
| `needs_locator` | A plausible authority is known, but chapter/verse/page is not yet recorded |
| `heuristic` | Intentionally a product judgment, not a textual claim |

## Source editions

The register identifies editions rather than citing titles alone. Page numbers
must always be interpreted against the named edition.

- **BS-IYER-1884** — Varahamihira, *The Brihat Samhita*, translated by
  N. Chidambaram Iyer, South Indian Press, 1884. Public scan:
  <https://archive.org/details/b29353130>.
- **BS-SASTRI-BHAT-1946** — Varahamihira, *Brihat Samhita*, Sanskrit text and
  English translation by V. Subrahmanya Sastri and M. Ramakrishna Bhat, 1946.
  Public scan: <https://archive.org/details/Brihatsamhita>.
- **BVR-MUHURTHA-1993** — B. V. Raman, *Muhurtha (Electional Astrology)*,
  UBS Publishers' Distributors, 1993, ISBN 9788185674681. This is a modern
  synthesis and secondary authority, not scripture. The Bhumi Puja / house-
  foundation profile uses Chapter XII, printed page 50 (PDF page 54), from
  the inspected public scan linked in the machine-readable register.
- **DP-DAY-PAGE** — Drik Panchang day/festival pages for a recorded city and
  date. This is an external published-panchangam comparison surface, not a
  textual authority for every project rule.
- **SWISSEPH** — Swiss Ephemeris/pyswisseph. This supports astronomical
  positions and event times, not interpretive judgments.

Muhurta Chintamani, Dharmasindhu, Surya Siddhanta, and BPHS remain in the
register as authorities requiring edition-level normalization. Until an
edition and locator are recorded, their claims remain `needs_locator`.

## Current ledger summary

- Drik astronomical positions are computed from Swiss Ephemeris and have
  representative external comparisons.
- The 2027–2028 forward-festival fixture contains **1 DP-verified cell and 29
  engine-pinned cells**. Engine-pinned means regression-protected, not
  independently verified.
- Gochara house/vedha tables, Muhurtam activity rules, Panchanga Shuddhi, and
  several dosha/yoga tables have named authorities but still need precise
  edition locators.
- Bhumi Puja / foundation laying is an activity-level exception: its profile
  has a page-level locator and criterion-by-criterion implementation crosswalk.
  Full election-chart and site-placement conditions remain visible manual checks.
- Well digging has the same activity-level treatment: the admitted Nakshatras
  and rising Rasis are automated from Chapter XII, while planetary Kendra and
  water-quality conditions remain explicit practitioner checks.
- The former generic “Property / Land purchase” option is now scoped narrowly
  to buying land for building, matching Raman's separate treatment of land and
  completed houses. Its weekday, Nakshatra and Rikta-Tithi rules have a precise
  Chapter XII locator.
- Namakarana now has a Chapter VIII rule-level profile: its Nakshatra,
  weekday and rejected-Tithi lists are automated, while birth-day timing and
  election-chart/name criteria remain visible manual checks.
- Annaprasana has a Chapter VIII profile cross-referenced to Chapter V's
  general Panchanga-Suddhi Tithis; age-month and election-chart requirements
  remain explicit manual prerequisites.
- Karnavedha now enforces Raman's daytime-only instruction across the Python
  and MCP night-slot path, plus exact weekday, Tithi and rising-Rasi gates;
  age, transition and election-house checks remain manual.
- Mundana/Chaula now enforces Shukla Paksha, non-combust Guru/Shukra, exact
  Tithi/Nakshatra/weekday/Lagna criteria and a cross-surface solar-noon cutoff;
  age, pregnancy, seasonal wording and chart placements remain manual.
- Absolute score thresholds and relative ordering are project heuristics.

Activity-level coverage is tracked separately in
[Muhurtam Activity Provenance Coverage](16-activity-provenance-coverage.md).
It is currently **7 of 30 profiles**; the remaining profiles retain
`needs_locator` status and do not inherit verified status from a general
title-level citation. `tools/check_activity_provenance.py` enforces every
activity-to-claim link against the ledger.

## Citation acceptance rule

A claim may move to `verified` only when its ledger entry contains:

1. a stable claim identifier;
2. an evidence class;
3. a named source edition;
4. a chapter, verse, table, or edition-specific page locator;
5. a short scope note stating what the citation does—and does not—support;
6. a maintainer review date.

For a published-panchangam comparison, replace items 3–4 with the page URL,
city, date, captured values, tolerance, and date inspected.

## Product-language rule

- Display facts as facts: "Moon enters Karka at 14:32."
- Attribute doctrine: "For Vivaha, this configuration is avoided in the
  configured Muhurta tradition."
- Disclose convention: "Some South Indian traditions observe this rule."
- Label heuristics: "Best available project score," not "Excellent Muhurtam,"
  unless it also clears the absolute quality threshold.
- Medical, legal, and financial timing is supplementary cultural guidance and
  never a substitute for qualified professional advice.
