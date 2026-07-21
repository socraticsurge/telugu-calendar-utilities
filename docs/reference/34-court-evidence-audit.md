# Court / Legal Matter Evidence Audit

## Status

The user-facing Court / legal matter profile is **not source-verified**. Its
`audit_claim`, `muhurta.court.profile_conflict`, has state `contradicted`.

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
| Lagna/Navamsa | No activity-specific gate | Lagna, or at least Navamsa, must be Mesha | Missing |
| Election chart | Not represented | Strengthen Lagna with Guru in a Trikona; no malefic in the 6th; separate Lagna and 6th lords | Manual checks |

The passage adds that benefics in Kendras, or benefic aspects from male Rasis,
indicate peace between the parties. That is an interpretive chart outcome, not
a universally automatable admission gate.

## Correction boundary

Existing tests preserve a Jaya-family Court bonus, and the present configuration
preserves a Tuesday bonus. Correcting the rule requires an owner-approved change
to the existing behavior contract. Until then, the finder surfaces the direct
weekday conflict and chart checks on every result instead of claiming authority.

The separate internal `litigation` key currently shares similar configured
preferences, but it has not been granted this claim. Provenance is activity-
specific: an alias does not inherit verification or contradiction silently.
