# Cremation / Antyeshti Evidence Audit

## Status

The Cremation rites profile is **not source-verified**. Its `audit_claim`,
`muhurta.cremation.profile_conflict`, has state `contradicted`.

## Inspected authority

- Rama Daivajna, *Muhurta Chintamani*, Sanskrit text with Hindi commentary.
- Internet Archive identifier `muhurta-chintamani-hindi`; the scan does not
  provide publisher or publication-date metadata.
- Nakshatra-prakarana, “Pretakriya ka muhurta,” verse 48.
- Printed pages 47–48; OCR lines 2956–2971.

The Sanskrit instruction and Hindi commentary identify the restricted span as
the latter half of Dhanishtha followed by Shatabhisha, Purva Bhadrapada, Uttara
Bhadrapada and Revati: four-and-a-half Nakshatras, not five whole Nakshatras.

## Criterion crosswalk

| Criterion | Current profile | Verse 48 | Status |
|---|---|---|---|
| Dhanishtha | Entire Nakshatra rejected | Only latter half rejected | **Direct precision conflict** |
| Remaining Panchaka | Shatabhisha through Revati rejected | Same four complete Nakshatras rejected | Matches |
| Timing basis | Generic good-Choghadiya slots after shared cut-outs | Passage discusses Pretakriya when it could not be performed at death | Scope not established |
| Ritual authority | No rite-specific context | Classical ritual-election context | Priest/Sampradaya judgment required |

## Safety and correction boundary

Antyeshti is not analogous to scheduling a purchase or business launch. Legal
and medical requirements, timely performance, family Sampradaya and the
officiating priest’s guidance take precedence over this project’s ranking.

The repository intentionally approximates Dhanishtha’s latter half as the full
Nakshatra, and existing tests pin that behavior. Correcting it needs a
Pada/longitude-aware Panchaka boundary and owner approval because the current
test contract would change. Until then, results expose both the over-broad
filter and the ritual-scope warning instead of claiming exact textual fidelity.

The activity is available through Python and MCP but not the browser catalogue.
This audit does not widen the UI without its screenshot and owner-sign-off flow.
