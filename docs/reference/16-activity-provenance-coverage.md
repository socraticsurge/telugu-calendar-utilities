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
| `home_repair` | Home repair / renovation commencement | `muhurta.home_repair.commencement` | Verified weekday profile; conditional chart rules remain manual |
| `property` | Land purchase for building | `muhurta.land_purchase.building` | Verified rule-level profile |
| `house_purchase` | Purchase of a completed new or old house | `muhurta.house_purchase.completed` | Verified house-specific profile; chart conditions remain manual |
| `naming` | Naming ceremony (Namakarana) | `muhurta.namakarana` | Verified rule-level profile |
| `annaprasana` | First feeding (Annaprasana) | `muhurta.annaprasana` | Verified rule-level profile |
| `karnavedha` | Ear piercing (Karnavedha) | `muhurta.karnavedha` | Verified rule-level profile |
| `mundana` | First head-shave (Mundana / Chaula) | `muhurta.mundana` | Verified rule-level profile |
| `vidyarambha` | Education commencement (Vidyarambha) | `muhurta.vidyarambha` | Verified rule-level profile |
| `upanayana` | Sacred-thread ceremony (Upanayana) | `muhurta.upanayana` | Verified rule-level profile |
| `seemantha` | Seemantha (prenatal ceremony) | `muhurta.seemantha` | Verified against Raman; related Chintamani claim records the 5th/7th versus 6th/8th-month lineage conflict |
| `vehicle` | Vehicle purchase | `muhurta.vehicle.acquisition` | Verified activity-specific Nakshatra preference |
| `construction_roof` | Roof-laying / construction milestone | `muhurta.construction_roof` | Verified activity-specific Lagna gate |
| `coronation` | Coronation / title ceremony | `muhurta.coronation` | Verified rule-level profile |
| `wood_cutting` | Wood-cutting / felling trees | `muhurta.wood_cutting` | Verified last-quarter profile |
| `surgery` | Surgery / medical procedure | `muhurta.surgery` | Verified rule-level profile with clinical safety boundary |
| `gold` | Gold / jewelry purchase | `muhurta.gold_jewelry.purchase` | Verified chart-level instruction; ranking remains heuristic |
| `pilgrimage` | Pilgrimage (Tirtha Yatra) | `muhurta.pilgrimage` | Verified incorporated journey profile |
| `travel` | Travel / journey | `muhurta.travel` | Verified Nakshatra profile; Tithi and Disha Shoola corrections approval-gated |
| `purchase` | Purchase (general) | `muhurta.purchase.general` | Verified buyer-side Nakshatra profile; Labh remains a project heuristic |
| `business_inventory_purchase` | Buying inventory for trade | `muhurta.trade_inventory.purchase` | Verified buyer-side inventory profile; chart checks remain manual |
| `borrowing_money` | Borrowing money / taking a loan | `muhurta.borrowing_money` | Verified debtor-side profile; related Chintamani claim records the divergent formula |
| `lending_money` | Lending money / giving a loan | `muhurta.lending_money` | Verified creditor-side Raman profile; related published-panchangam claim records the Wednesday divergence |
| `wedding` | Wedding (Vivaha) | `muhurta.wedding` | Verified Raman-lineage profile; exact month/anga/Lagna gates, manual Pada/chart prerequisites and published-practice divergence disclosed |
| `engagement` | Engagement (Nischayam) | `muhurta.engagement.profile_conflict` | **Contradicted:** no dedicated passage found; nearest marriage rules conflict with copied scoring |
| `gruhapravesha` | First entry into a newly built home | `muhurta.gruhapravesha` | Verified Raman-lineage profile; exact day/anga/Lagna gates and published-practice divergence disclosed |
| `court` | Filing a lawsuit / court action | `muhurta.court.filing_lawsuit` | Verified Raman-lineage filing profile; exact weekday, Tithi, Nakshatra and conservative Lagna gates, with chart prerequisites disclosed |
| `litigation` | Litigation / contest | `muhurta.litigation.profile_conflict` | **Contradicted:** repeats the Tuesday reversal; Bhadra Puchha attribution lacks an exact locator |
| `cremation` | Cremation rites | `muhurta.cremation.profile_conflict` | **Contradicted:** whole-Dhanishtha block overstates the cited 4½-Nakshatra Panchaka |
| `yajna` | Yajna / Homam | `muhurta.yajna.profile_conflict` | **Contradicted:** family scoring omits and conflicts with Homahuti/Agnivasa formulas |
| `job` | Job start / Contract signing | `muhurta.job_contract.profile_conflict` | **Contradicted:** combines distinct service-entry and contract scopes under unsupported proxies |
| `business` | Business launch | `muhurta.business.profile_conflict` | **Contradicted:** nearest capital-deployment verse requires Chara, not configured Sthira, Lagna |
| `ceremony` | Ceremony / puja (general) | `muhurta.ceremony.profile_conflict` | **Contradicted:** narrow Shantika/Paushtika passage rejects Rikta, not configured Jaya, Tithis |
| `beginning` | New beginning (general) | `muhurta.beginning.profile_conflict` | **Contradicted:** nearest Dharma-kriya verse is narrower and does not support generic ranking proxies |
| `any` | Anything auspicious | `muhurta.any.shared_scoring` | **Heuristic:** neutral shared-score explorer, not an election for an unspecified act |

Coverage is therefore **27 of 36 profiles**. The verified profiles use
B. V. Raman's *Muhurtha* and *Muhurta Chintamani*, with edition-specific
printed, PDF, verse and OCR locators. Raman is a modern secondary authority,
not scripture; this
status means the implemented criteria match the cited passage, not that every
lineage treats the rule as universal.

Engagement, Litigation, Cremation, Yajna,
Job/Contract, Business, Ceremony and New Beginning are excluded from the
verified count. Their
`audit_claim` fields record known source conflicts without granting authority
to the current profiles. See the [Engagement evidence audit](36-engagement-evidence-audit.md), the
[Court evidence audit](34-court-evidence-audit.md), and the
[Litigation evidence audit](35-litigation-evidence-audit.md), and the
[Cremation evidence audit](37-cremation-evidence-audit.md), and the
[Yajna/Homam evidence audit](38-yajna-homam-evidence-audit.md), and the
[Job/Contract evidence audit](40-job-contract-evidence-audit.md), and the
[Business evidence audit](41-business-evidence-audit.md), and the
[Ceremony evidence audit](42-ceremony-evidence-audit.md), and the
[New Beginning evidence audit](43-beginning-evidence-audit.md).

Every activity key now has an explicit disposition: verified source profile,
known textual conflict, or intentional project heuristic. The umbrella ledger
claim `muhurta.activity_rules` remains `needs_locator` as a warning that shared
defaults never confer textual authority on a newly added profile.

## Enforcement

An activity declares exactly one of `source_claim`, `audit_claim`, or
`heuristic_claim` beside its rules in
`telugu_panchangam/personal/activity_rules.py`. Tests require that the claim
exists in `docs/reference/provenance.json`, belongs to the `muhurtam` surface,
and has the matching `verified`, `contradicted`, or `heuristic` state. These
fields are exported to the browser contract and returned by MCP, so provenance
cannot be maintained in a surface-specific hard-coded map.

`tools/check_activity_provenance.py --json` supplies machine-readable lists of
verified profiles, known conflicts, explicit heuristics and unlinked profiles.
Adding any claim field without the required ledger state makes the test suite
fail.
