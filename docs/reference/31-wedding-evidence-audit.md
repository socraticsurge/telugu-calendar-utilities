# Wedding Evidence Audit

## Status

The wedding profile is **not source-verified**. Its machine-readable
`audit_claim` is `muhurta.wedding.profile_conflict`, whose state is
`contradicted`. This is an evidence warning, not an authority badge.

## Inspected authority

- B. V. Raman, *Muhurtha (Electional Astrology)*, UBS Publishers'
  Distributors, 1993.
- Chapter IX, “Electing a time for marriage,” printed page 41, PDF page 45.
- Raman is a modern secondary authority, not scripture.

## Material conflicts

| Criterion | Current profile | Inspected passage | Consequence |
|---|---|---|---|
| Jaya Tithi family | Penalized wholesale | Shukla Tritiya and Trayodashi are named among the best; Ashtami is rejected | A family-level penalty reverses two explicit recommendations |
| Purna Tithi family | Rewarded wholesale | Pournami and Amavasya are rejected | The score can reward expressly rejected Tithis |
| Vara | Guruvara and Somavara preferred | Monday, Wednesday, Thursday and Friday are best; Tuesday rejected | The current preference is incomplete and has no hard Tuesday gate |
| Nakshatra | No wedding-specific list | Eleven best Nakshatras are listed; others are called unsuitable, with Pada exceptions | Major activity-specific admission rule is absent |
| Lagna | Fixed class preferred | Three Rasis are best, five middling, and the rest unsuitable | The class-level proxy does not reproduce the named-Rasi rule |

## Correction boundary

Existing tests explicitly preserve the Jaya penalty and Purna reward. Project
policy treats those assertions as the frozen contract, so correcting them
requires explicit owner approval. Until then:

1. the profile must not declare `source_claim`;
2. browser and MCP contracts expose `audit_claim`;
3. coverage reports wedding separately from both verified and merely unlocated
   profiles; and
4. downstream copy must not call wedding recommendations textually verified.

Once approved, the correction should use exact Tithi numbers/names and named
Nakshatra/Rasi gates rather than Tithi or Lagna class proxies. Pada-level
exceptions and election-chart conditions should remain explicit manual checks
unless the relevant chart data is available across every surface.
