# Litigation Compatibility Alias and Bhadra Audit

## Corrected product boundary

`litigation` is retained only as a backward-compatible Python/MCP alias for
`court`, whose verified scope is filing or initiating a lawsuit. It is no
longer a separate rule profile, does not appear in the browser selector, and
does not claim to time hearings, responses, settlements, appeals, contests or
case outcomes.

This removes three unsupported behaviors from the former duplicate profile:
the Jaya-family reward, Purna-family penalty and Tuesday reward. It also removes
the activity-specific Bhadra Puchha bonus. Alias resolution happens before rule
lookup, so legacy callers receive the exact `muhurta.court.filing_lawsuit`
profile and the MCP response discloses `alias_of: court` and
`resolved_activity: court`.

## Authorities inspected

- B. V. Raman, *Muhurtha (Electional Astrology)*, UBS Publishers'
  Distributors, 1993, Chapter XVII, “Filing law-suits,” printed page 67
  (PDF page 71).
- Rama Daivajna, *Muhurta Chintamani*, undated Sanskrit text with Hindi
  commentary, Shubhashubha-prakarana, verses 43–45, printed pages 20–21
  (Internet Archive OCR lines 1743–1797).

Raman supplies the narrow lawsuit-filing election. Chintamani verse 44 calls
the specified Puchha periods auspicious generally; it does not name litigation
or authorize an activity-specific score.

## Newly isolated computational debt

The project currently divides every observed Vishti span proportionally into
5:8:3 and labels the first 5/16 Mukha and final 3/16 Puchha. Chintamani verse 44
instead locates five-Ghati Mukha and three-Ghati Puchha windows in different
numbered Yamas for each of eight Vishti-bearing Tithis. The proportional
implementation is therefore an approximation, not a verified rendering of
this edition.

This branch does not alter that shared Panchangam computation. The debt is now
recorded as `panchangam.bhadra_mukha_puchha.approximation`; correcting it must
be a dedicated feature because it changes shared engine outputs and existing
tests. Until then, the Bhadra sub-window must not be cited as a precise
scriptural basis for a legal-election bonus.

## Safety

Legal deadlines, court rules, counsel, evidence and personal safety always
take precedence. Electional timing cannot predict or guarantee a legal result.
