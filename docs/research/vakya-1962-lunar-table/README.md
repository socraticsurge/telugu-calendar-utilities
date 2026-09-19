# Appendix II lunar longitudes: research transcription

This is a research-only numeric transcription of all 248 lunar longitude rows.
Source: the 1962 scan linked in `metadata.json`, physical PDF pages
162-171, printed pages 125-134. The opening page's printed numeral is absent;
125 is inferred from the following printed 126 and the book pagination.

## Files

- `lunar-longitudes.csv`: flat machine-readable rows and locators.
- `lunar-longitudes.json`: identical structured rows.
- `metadata.json`: source SHA256, units, page ranges, method and limitations.
- `ambiguities-and-source-discrepancies.json`: unresolved discrepancy and header errors.
- `symmetry-check.json`: diagnostic against the source's printed verification rule.

The Sanskrit mnemonic column is outside this numeric transcription's scope.
Physical page numbers and row-on-page locators are one-based.
The separate `pdf_page_index` is zero-based.
Intermediate unnumbered day rows follow their printed anchors in order.

## Findings requiring care

1. Day 100, physical 165 / printed 128 / body row 21 reads **8r1deg17min**.
2. Day 148, physical 167 / printed 130 / body row 16 reads **4r26deg17min**.
3. These sum modulo 360 degrees to **0r27deg34min**, ten arcminutes below the
   printed page 134 verification target **0r27deg44min**.
4. Both minute cells visibly read 17; no corrected value is assigned.
5. Physical 170's running header says 208-232, but its 27 body rows span 208-234.
6. Physical 171's header says 233-248, but its 14 body rows explicitly begin 235.

There are no remaining visually unreadable numeric cells in this reading.
The source-authority discrepancy above remains unresolved.
An initial low-resolution reading of day16's minutes as 16 was rejected after
250dpi inspection: the source visibly reads15; the final artifacts use15.
Faint cells in rows 142,148 and155 were checked at 300 dpi.

## Validation and limits

All 248 sequential day indices are present exactly once.
All numeric cells satisfy their column ranges.
The book's complement relation passes all pairs except 100/148;
this arithmetic diagnostic never supplies or silently corrects a cell.
Day 124 is 6r13deg52min and day 248 is 0r27deg44min, consistent with the printed
midpoint statement on page 134.
Days 153 and154 agree with root's separate readings:7r7deg36min and7r21deg48min.

This is a single-transcriber draft, not an independently certified table.
No epoch, ahargana, interpolation, time-of-day or engine model is implemented.
It does not validate the current nine-offset engine.
Publication of this transcription changes no engine or calculation behavior.

Next evidence steps are independent double-entry transcription, checking an
alternate edition or errata for 100/148, and separately reconstructing the
source's epoch/argument rules before any proposed model comparison.

## Root spot review — 2026-09-21

A separate visual spot review of complete physical pages 165 and 167, plus the
higher-resolution crops, confirmed the day100 and day148 readings and their
row locators. Both minute cells read17; the ten-arcminute inconsistency remains.
This checks the flagged pair only, not independent double-entry of all248 rows.
