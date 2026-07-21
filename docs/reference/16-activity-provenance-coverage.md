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
| remaining 23 keys | See `ACTIVITY_RULES` | — | Exact rule locators still required |

Coverage is therefore **7 of 30 profiles**. The verified profiles use
B. V. Raman's *Muhurtha*, Chapter XII, with edition-specific printed and PDF
page locators. Raman is a modern secondary authority, not scripture; this
status means the implemented criteria match the cited passage, not that every
lineage treats the rule as universal.

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

`tools/check_activity_provenance.py --json` supplies a machine-readable list
of verified and unlinked profiles. Adding a `source_claim` without completing
the ledger evidence makes the test suite fail.
