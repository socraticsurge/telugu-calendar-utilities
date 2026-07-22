# Muhurtam Activity Coverage Roadmap

The current selector has 33 activity keys, all with an explicit provenance
state. That closes attribution ambiguity; it does not mean the activity
catalogue is complete. The machine-readable gap inventory is
[`muhurta-activity-backlog.json`](muhurta-activity-backlog.json).

## Immediate finding about house warming

House warming is already present as `gruhapravesha`, correctly narrowed to the
first entry into a newly built home. It is not counted as verified: the current
soft Tithi/Lagna preferences conflict with Raman's exact gates. The existing
[Gruhapravesha evidence audit](33-gruhapravesha-evidence-audit.md) records the
correction required. A completed-house purchase, rental move, post-renovation
re-entry and first occupation of a newly built home are different acts and must
not silently share one profile.

## Highest-impact additions

| Order | Activity | Why it comes next |
|---|---|---|
| 1 | Seemantha | **Implemented:** source-verified profile with pregnancy and medical boundaries |
| 2 | Completed-house purchase | **Implemented:** dedicated new/old completed-house profile |
| 3 | Home repair / renovation start | **Implemented:** scoped repair-commencement profile |
| 4 | Buying inventory for trade | Replaces one concrete slice of the unsupported Business launch catch-all |
| 5 | Borrowing and lending | Source explicitly distinguishes the two transaction roles |

Seemantha, completed-house purchase and home-repair commencement are now
implemented as separate, source-verified profiles with explicit medical,
legal, safety and scope boundaries. Buying inventory for trade is now the
highest-priority missing profile.

## Important holds and splits

- Pumsavana is on policy hold because the inspected source presents fetal sex
  selection and efficacy claims that the product must not endorse.
- Garbhadhana requires consent, fertility and medical-safety language before
  implementation.
- Agriculture must be split into ploughing, sowing, planting, pruning,
  harvesting and storage. A generic profile would be textually indefensible.
- Deity installation is specialist-only: Raman explicitly says the summary is
  not a substitute for the full ritual and chart authorities.
- Medicine preparation can never supersede pharmacy standards, qualified
  practice or clinical evidence.

## One-feature-at-a-time gate

For each addition:

1. inspect the complete passage and at least one independent authority;
2. record exact edition/page/verse locators and disagreements;
3. write the rule crosswalk and tests before implementation;
4. add a new activity module/profile without changing the frozen engines;
5. expose identical provenance and decisive rules through MCP and browser;
6. capture browser screenshots and obtain owner sign-off before pushing;
7. run the full verifier and stop after the feature is concluded.

Candidate locators in the backlog prove discoverability only. They do not grant
`verified` status to any future activity.
