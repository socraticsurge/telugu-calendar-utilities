# General Purchase Source Profile

## Authority and scope

The generic Purchase profile uses Rama Daivajna’s *Muhurta Chintamani*,
Sanskrit text with Hindi commentary, Internet Archive identifier
`muhurta-chintamani-hindi`:

- Nakshatra-prakarana, purchase/sale distinction and purchase Muhurta,
  verse 16, printed pages 33–34; OCR lines 2336–2350.
- Marketplace election, verse 17, printed pages 34–35; OCR lines 2351–2374.

The scan does not expose publisher or publication-date metadata. The stable
verse, printed-page, repository-source and OCR locators make that limitation
explicit rather than hiding it.

## Automated rule

Verse 16 names six Nakshatras as favorable for purchase:

- Revati
- Shatabhisha
- Ashvini (source-facing configuration retains “Ashwini” and normalizes it)
- Swati
- Shravana
- Chitra

These stars receive the activity-specific source-backed bonus. The passage
calls them favorable; it does not say that every other Nakshatra is forbidden,
so the implementation uses a preference instead of a hard admission gate.

## Role and marketplace checks

Verse 16 expressly distinguishes buying from selling. This profile is for the
buyer; a seller election cannot silently inherit it.

Verse 17 adds marketplace-chart criteria that remain practitioner checks:
reject Rikta Tithis, Tuesday and Kumbha Lagna; prefer Chandra and Shukra in
Lagna; keep malefics out of the 8th and 12th; place benefics in the 2nd, 10th
or 11th.

## Non-inherited heuristics and narrower profiles

The Labh-Choghadiya bonus is a transparent project-ranking heuristic. Verses
16–17 do not authorize it.

When the object is known, the dedicated vehicle, building-land or gold/jewelry
profile is the narrower authority and takes precedence. A generic purchase
citation must not flatten their distinct rules.
