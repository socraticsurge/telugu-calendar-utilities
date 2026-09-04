# Raman work and inspected-artifact identity audit

Story: [#366](https://github.com/socraticsurge/telugu-calendar-utilities/issues/366)

Parent event: [#265](https://github.com/socraticsurge/telugu-calendar-utilities/issues/265)

Audience: maintainers, computation reviewers, and readers checking Muhurtam sources

Revalidated: 2026-09-04

## Direct answer

The repository had represented one catalogue record and one hosted PDF as
though they were the same edition. They are not the same inspected object. This
release candidate separates them in canonical provenance:

1. BVR-MUHURTHA-1993 is the bibliographic record for B. V. Raman,
   *Muhurtha (Electional Astrology)*, UBS Publishers' Distributors, 1993,
   ISBN 9788185674681, 181 catalogued pages.
2. BVR-MUHURTHA-CHISTABO-2020 is the artifact actually inspected: a
   78-physical-page PDF whose own notice identifies it as a 2020 Simon/Chistabo
   re-edit with bracketed additions, typo corrections, and the appendix
   omitted.

No scan of the 181-page 1993 edition was inspected. The Chistabo notice says
its text was checked against an unspecified original scanned PDF; it does not
identify that input as the 1993 UBS edition. The canonical record therefore
links the objects while explicitly leaving an exact edition match unverified.

## Scope and method

The audit covers every provenance claim linked to BVR-MUHURTHA-1993 at the
release base, plus human-readable pages and generated source disclosures that
project those claims. It does not reassess the meaning, admission set, score,
or ranking effect of any rule.

The hosted artifact was downloaded again on 2026-09-04. Its checksum, byte
size, page count, metadata, editorial notice, internal folios, chapter
transitions, and each claimed passage were checked directly. Google Books and
Open Library were independently read for the 1993 catalogue identity.

## Inspected artifact

| Field | Verified value |
|---|---|
| URL | <https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf> |
| Accessed | 2026-09-04 |
| SHA-256 | b8b878a444a487c83810329fdf8f057c40e92221a867db480d864da8be21a133 |
| Bytes | 2,172,882 |
| Physical PDF pages | 78 |
| PDF title | Muhurta-Raman Eng |
| PDF creation/modification metadata | 2020-06-17 16:29:55 IST |
| Producer | Mac OS X 10.13.6 Quartz PDFContext |
| Editorial disclosure | physical PDF p. 3 / internal folio II |

The title page says that the document is “as per” B. V. Raman. Physical PDF
p. 3 identifies Simon, also called Chistabo, as editor and describes re-editing,
corrections, bracketed additions, and appendix omission. These visible
statements rule out treating the file as an inspected copy of the catalogued
1993 edition.

## Page-number model

The derivative has two offsets:

- physical PDF pp. 1–3 are derivative front matter;
- physical PDF pp. 4–36 map to internal printed pp. 1–33
  (internal = physical - 3);
- physical PDF p. 37 is an unnumbered continuation/table page;
- physical PDF pp. 38–78 map to internal printed pp. 34–74
  (internal = physical - 4).

A global “printed page + 4” rewrite is therefore unsafe. All canonical Raman
locators now say both **internal printed page** and **physical PDF page** and
name the Chistabo derivative.

## Claim-gap matrix

All 34 active provenance claims associated with the bibliographic work were
reconciled. The machine-readable fixture records the pre-migration locator,
the directly checked locator, canonical source identifiers, and status for
each claim.

| Audit state | Count | Release treatment |
|---|---:|---|
| aligned | 13 | Coordinates retained; artifact and page vocabulary made explicit |
| correction_required | 17 | Coordinates or range corrected from direct artifact inspection |
| no_locator | 4 | Kept work-only and needs_locator; no derivative inspection implied |

High-impact corrections include:

- Vehicle: internal printed p. 11 / physical PDF p. 14, not internal p. 10.
- Well digging: internal printed p. 52 / physical PDF p. 56, not p. 51 / p. 55.
- Roof laying: internal printed p. 51 / physical PDF p. 55, not p. 50 / p. 54.
- Naming: internal printed p. 22 / physical PDF p. 25, not internal p. 21.
- Completed-house and building-land purchase: internal printed p. 54 /
  physical PDF p. 58, not p. 53 / p. 57.
- Home repair: internal printed pp. 54–55 / physical PDF pp. 58–59; the former
  range began early and omitted the continuation.
- General Panchanga Suddhi: internal printed p. 12 / physical PDF p. 15, not
  “printed p. 11.”
- Vidyarambha: internal printed p. 23 / physical PDF p. 26, not physical p. 27.
- Karnavedha: physical PDF p. 26 visibly carries internal footer 23; the
  earlier internal-p.22 note was wrong.
- Tyajyakala: internal printed p. 7 / physical PDF p. 10.
- Panchak: internal printed pp. 8–9 / physical PDF pp. 11–12.

The complete 34-row ledger is in
tests/fixtures/raman-artifact-identity-audit-v1.json.

## Authority and implementation boundary

The artifact verifies what the derivative says and where it says it. It does
not establish that every editorial choice reproduces the 1993 edition, promote
the derivative to primary scripture, or make the cited lineage universal.

Located Raman claims now cite both the bibliographic work and the exact
artifact inspected. The four claims without a locator remain linked only to
the bibliographic work and retain needs_locator; this avoids converting a
source association into false inspection evidence.

Non-source rule semantics remain unchanged after source metadata is stripped,
and the four protected scoring implementations remain byte-identical. The
source split changes provenance records, source disclosures, corrected page
coordinates, release metadata, and tests only. Runtime predicates, accepted
event values, ranking weights, the frozen engines, ICS generation, and
workflows are unchanged.

## Source ledger

- B. V. Raman, *Muhurtha (Electional Astrology)*, UBS Publishers'
  Distributors, 1993, ISBN 9788185674681, 181 pages:
  [Google Books catalogue](https://books.google.com/books/about/Muhurtha_Electional_Astrology.html?id=nHQlAcBkDXIC)
  and [Open Library edition record](https://openlibrary.org/books/OL9860226M/Muhurtha_%28Electional_Astrology%29).
  These corroborate bibliographic identity; neither was used as full-text
  evidence.
- B. V. Raman / Simon (Chistabo), *Muhurtha (Electional Astrology)*,
  2020 re-edited PDF:
  [inspected artifact](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf).
  This supplies the visible editorial notice and every physical/internal page
  coordinate in the migrated claims.

## Stop condition and remaining gap

The research stopped after the hosted file's identity and all 34 active claim
states were reproducible, the 17 corrections had direct page evidence, and a
second catalogue independently corroborated the 1993 record. Another search
would not change the required split.

One material gap remains: no physical or digitized copy of the catalogued
181-page 1993 UBS edition has been inspected. A future edition-collation story
may compare its text with the Chistabo derivative, but that work is not needed
to state the present evidence truthfully.
