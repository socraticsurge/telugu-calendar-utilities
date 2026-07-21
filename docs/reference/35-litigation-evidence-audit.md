# Litigation / Contest Evidence Audit

## Status

The user-facing Litigation / contest profile is **not source-verified**. Its
`audit_claim`, `muhurta.litigation.profile_conflict`, has state `contradicted`.

## Inspected authority

- B. V. Raman, *Muhurtha (Electional Astrology)*, UBS Publishers'
  Distributors, 1993.
- Chapter XVII, “Miscellaneous elections,” section “Filing law-suits.”
- Printed page 67; PDF page 71.
- Raman is a modern secondary authority, not scripture.

## Criterion crosswalk

| Criterion | Current profile | Inspected passage | Status |
|---|---|---|---|
| Vara | Tuesday receives a bonus | Tuesday and Saturday should be avoided | **Direct contradiction** |
| Tithi | Jaya family rewarded; Purna family penalized | Says to avoid the usual unfavorable Tithis, without authorizing either family-wide mapping | Unsupported family proxies |
| Nakshatra | No activity-specific gate | Ashwini, Rohini, Mrigashira, Pushya, Uttara Phalguni, Hasta, Chitra, Anuradha, Dhanishtha and Revati are admitted | Missing |
| Election chart | Not represented | Guru in a Trikona from a strengthened Lagna; no malefic in the 6th; separate Lagna and 6th lords; Mesha Lagna or Navamsa | Missing |
| Bhadra Puchha | Overlap receives +2 | Not discussed in this passage | Separate, incompletely located attribution |

## Bhadra Puchha boundary

The code attributes the 5:8:3 Vishti split and the auspicious Puchha use for
contests/litigation to *Muhurta Chintamani* and *Dharma Sindhu*. Those are
plausible classical source families, but the repository does not identify an
edition, chapter, verse, or page. This audit therefore neither rejects nor
verifies the bonus. It records the exact missing evidence needed to elevate it.

## Correction boundary

Existing tests preserve the Jaya/Purna families, Tuesday bonus, and Bhadra
Puchha score. Correcting those rules would change the current behavior contract
and requires owner approval. Until then, every Litigation result exposes the
weekday contradiction and the Bhadra-locator debt rather than presenting the
profile as source-verified.

The profile is currently available through Python and MCP but is absent from
the browser activity catalogue. This audit does not silently widen the public
UI; adding it there requires the repository's screenshot and owner-sign-off
workflow.
