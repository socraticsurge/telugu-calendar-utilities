# Muhurtam Activity Provenance Coverage

This page is the completeness report for the activity-specific rules used by
the Muhurtam finder. It deliberately separates a working rule profile from a
profile whose individual criteria have been checked at an exact source
locator.

Run the machine check with:

```bash
python tools/check_activity_provenance.py
```

## Current coverage

| Activity key | User-facing scope | Verified claim | Status |
|---|---|---|---|
| `bhumi_puja` | Bhumi Puja / foundation laying | `muhurta.bhumi_puja.foundation` | Verified rule-level profile |
| `well_digging` | Well digging | `muhurta.well_digging` | Verified rule-level profile |
| `property` | Land purchase for building | `muhurta.land_purchase.building` | Verified rule-level profile |
| `naming` | Naming ceremony (Namakarana) | `muhurta.namakarana` | Verified rule-level profile |
| `annaprasana` | First feeding (Annaprasana) | `muhurta.annaprasana` | Verified rule-level profile |
| `karnavedha` | Ear piercing (Karnavedha) | `muhurta.karnavedha` | Verified rule-level profile |
| `mundana` | First head-shave (Mundana / Chaula) | `muhurta.mundana` | Verified rule-level profile |
| `vidyarambha` | Education commencement (Vidyarambha) | `muhurta.vidyarambha` | Verified rule-level profile |
| `upanayana` | Sacred-thread ceremony (Upanayana) | `muhurta.upanayana` | Verified rule-level profile |
| `vehicle` | Vehicle purchase | `muhurta.vehicle.acquisition` | Verified activity-specific Nakshatra preference |
| `construction_roof` | Roof-laying / construction milestone | `muhurta.construction_roof` | Verified activity-specific Lagna gate |
| `coronation` | Coronation / title ceremony | `muhurta.coronation` | Verified rule-level profile |
| `wood_cutting` | Wood-cutting / felling trees | `muhurta.wood_cutting` | Verified last-quarter profile |
| `surgery` | Surgery / medical procedure | `muhurta.surgery` | Verified rule-level profile with clinical safety boundary |
| `gold` | Gold / jewelry purchase | `muhurta.gold_jewelry.purchase` | Verified chart-level instruction; ranking remains heuristic |
| `pilgrimage` | Pilgrimage (Tirtha Yatra) | `muhurta.pilgrimage` | Verified incorporated journey profile |
| `travel` | Travel / journey | `muhurta.travel` | Verified Nakshatra profile; Tithi and Disha Shoola corrections approval-gated |
| `wedding` | Wedding (Vivaha) | `muhurta.wedding.profile_conflict` | **Contradicted:** inspected Tithi rules conflict with configured scoring |
| remaining 12 keys | See `ACTIVITY_RULES` | — | Exact rule locators still required |

Coverage is therefore **17 of 30 profiles**. The verified profiles use
B. V. Raman's *Muhurtha*, with edition-specific printed and PDF page locators.
Raman is a modern secondary authority, not scripture; this
status means the implemented criteria match the cited passage, not that every
lineage treats the rule as universal.

Wedding is excluded from the verified count. Its `audit_claim` records a known
source conflict without granting authority to the current profile. See the
[wedding evidence audit](31-wedding-evidence-audit.md).

The remaining profiles are covered only by the umbrella ledger claim
`muhurta.activity_rules`, whose state is `needs_locator`. They may be used as
configured project rules, but must not be described as textually verified
until each receives its own claim ID, inspected edition, exact locator, scope
note, and review date.

## Enforcement

An activity opts into verified status by declaring `source_claim` beside its
rules in `telugu_panchangam/personal/activity_rules.py`. Tests require that the
claim exists in `docs/reference/provenance.json`, belongs to the `muhurtam`
surface, and has state `verified`. The same field is exported to the browser
contract and returned by MCP, so provenance cannot be maintained in a
surface-specific hard-coded map.

`tools/check_activity_provenance.py --json` supplies machine-readable lists of
verified profiles, known conflicts and unlinked profiles. Adding a
`source_claim` or `audit_claim` without the required ledger state makes the test
suite fail.
