# Vakya lunar model: inspected source and remaining correction work

Maintainer research record for issue #176; not a replacement engine or a claim
that present Vakya output is independently verified. Review this record when
an exact replacement model and external comparison corpus are ready.

## Primary artifact

*Vakyakarana with Laghuprakasika*, edited by T. S. Kuppanna Sastri and K. V.
Sarma, 1962. [Inspected scan](https://www.ebharatisampat.in/pdfs/ebharati-pdf-1644580379VakyaKarana-LaghuParkasikaVyakhya-Ed-KuppannaSastri-SarmaKV-1962.pdf),
339 physical PDF pages, 11,159,128 bytes; SHA-256
`27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
Retrieved 2026-09-19. Relevant English pages were rendered and visually checked;
OCR was used for navigation, not as sole authority for numeric transcription.

## What the edition establishes

Printed pages 253–254 (physical PDF pages 290–291), chapter I verses 9–14a,
describe successive reductions of Kali days after subtracting 1,600,984:
divide by 12,372, then the remainder by 3,031, then the remainder by 248.
The final remainder selects a lunar mnemonic, with quotient-dependent angular
terms and a daily-motion correction. Appendix II, printed pages 125–134,
contains the lunar table identified by the translation's footnote 7.

Thus **3,031 is a sourced step**, but this does not establish the repository's
nine-value offset. The source does not describe adding one of nine half-degree
offsets to the Surya Siddhanta Moon for successive 3,031-day blocks.

The worked example on printed page 254 uses Kali day 1,844,004. Its reductions
yield quotients 19, 2 and 7, and remainder 154. The tabular longitude for entry
154 is 7 signs 21 degrees 48 minutes; entry 153 is 7 signs 7 degrees 36 minutes.
The example's final Moon longitude is 4 signs 11 degrees 17 minutes 32 seconds.
The two rows were also visually cross-checked in Appendix II, printed page 130
(physical PDF page 167). `tests/fixtures/vakya_1962_worked_example.json` and
`tests/test_vakya_source_example.py` reproduce the printed reductions, angular
sums, daily-motion correction and local correction with rational arithmetic.
This is an independently printed arithmetic example, not a modern city/date
Panchangam comparison.

Printed pages 255–256 (physical PDF pages 292–293), verses 14b–17a and example 4,
then reduce to local true sunrise using daylight, longitude relative to Ujjain,
and the specified equation-of-time component. The Pudukkottai example gives
4 signs 11 degrees 9 minutes 21 seconds after that reduction. Substituting a
modern sunrise helper without deciding this historical time model would not
be a source-faithful reconstruction.

## Gap register and bounded next work

| Claim or requirement | Evidence now | Remaining work |
|---|---|---|
| 3,031-day quantity | Located exactly in I.9–11 | Retain as one reduction, not an entire nine-phase model |
| 248-day lunar table | Complete 248-row numeric transcription with page/row locators | Independent second transcription, unresolved 100/148 discrepancy and wrap/zero-remainder indexing |
| Angular constants and correction | Located in I.9–14a and worked example 3 | Printed example reproduced; single-transcriber full table published, general boundary cases still required |
| Epoch, meridian and local sunrise | Kali-day and Ujjain/local reduction described in I.2–3 and I.14b–17a | Specify fractional-day and modern coordinate conversion explicitly |
| Modern published Vakya output | No independently inspected exact city/date corpus in this audit | Inspect published scans and establish their regional/table/time convention before comparison |
| Current engine | Nine offsets over 3,031-day blocks, regression-pinned | Replace only after model/corpus review and explicit frozen-core approval |

The correction should be a separate, versioned release with unchanged unrelated
engine, feed and workflow behavior. Keep #176 open and the current public
evidence state `engine_pinned` / `project_heuristic`; finding a primary source
does not retroactively validate the implementation. No frozen source was edited.

## Current published-output leads

The [Srirangam 2026–2027 scan collection](https://srirangaminfo.com/vakya-panchangam-srirangam.php)
and [NKMY Samithi publisher downloads](https://nkmysamithi.org/download_panchangam.php)
were located on 2026-09-19. These are leads, not fixture evidence: a search
listing or cover does not establish the exact daily values, city meridian,
time units, or correspondence to this edition's method. Do not use a Drik
or Surya Siddhanta almanac as a mislabeled Vakya lunar oracle.

## Complete numeric transcription — 2026-09-21

The [research transcription](../research/vakya-1962-lunar-table/README.md) records
all 248 Appendix II numeric rows, with CSV/JSON parity and physical/printed page
locators. It is single-transcriber evidence, with a separate spot review of
days 100 and 148; it is not full independent double-entry certification.
Both minute cells read 17. Their sum modulo a circle is 0 signs 27 degrees
34 minutes, ten arcminutes below the printed 27 degrees 44 minutes check.
Neither cell is silently corrected. The source-authority discrepancy remains
open, as do epoch, interpolation and modern comparison decisions. These data
are research evidence only and are not consumed by any calculation engine.
