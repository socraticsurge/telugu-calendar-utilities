# Muhurtam Activity Coverage Roadmap

The current selector has 36 activity keys, all with an explicit provenance
state. That closes attribution ambiguity; it does not mean the activity
catalogue is complete. The machine-readable gap inventory is
[`muhurta-activity-backlog.json`](muhurta-activity-backlog.json).

## Immediate finding about house warming

House warming is present as `gruhapravesha`, correctly narrowed to the first
entry into a newly built home. Its former soft Tithi-family scoring has been
replaced with Raman's exact weekday, Paksha-qualified Tithi, Nakshatra,
Uttarayana and Lagna gates. Chart, ritual and pregnancy conditions remain
visible manual prerequisites, while the current Drik Panchang Saturday/month
methodology divergence is disclosed. See the
[Gruhapravesha source profile](33-gruhapravesha-evidence-audit.md). A
completed-house purchase, rental move, post-renovation re-entry and first
occupation of a newly built home remain separate acts.

## Highest-impact additions

| Order | Activity | Why it comes next |
|---|---|---|
| 1 | Seemantha | **Implemented:** source-verified profile with pregnancy and medical boundaries |
| 2 | Completed-house purchase | **Implemented:** dedicated new/old completed-house profile |
| 3 | Home repair / renovation start | **Implemented:** scoped repair-commencement profile |
| 4 | Buying inventory for trade | **Implemented:** buyer-side inventory profile distinct from launch |
| 5 | Borrowing and lending | **Implemented:** separate debtor- and creditor-side profiles |
| 6 | Gruhapravesha correction | **Implemented:** conflicting soft profile replaced by exact Raman-lineage gates |
| 7 | Wedding correction | **Implemented:** contradictory family scoring replaced by the complete Raman election crosswalk |
| 8 | Lawsuit-filing correction | **Implemented:** generic Court proxies replaced by the exact Raman filing election |
| 9 | Litigation duplicate correction | **Implemented:** legacy key now resolves to Court; unsupported Bhadra/legal scoring removed |
| 10 | Ceremony correction | **Implemented:** generic Puja proxies replaced by the exact Shantika/Paushtika election |
| 11 | New Beginning correction | **Implemented:** generic proxies replaced by the exact Dharma-kriya commencement election |

Seemantha, completed-house purchase, home-repair commencement and trade-
inventory purchase, borrowing and lending are now implemented as separate,
source-verified profiles with explicit medical, legal, safety and scope
boundaries. Borrowing discloses its Chintamani divergence; lending discloses
the current Drik Panchang Wednesday divergence. Gruhapravesha is now corrected
and verified, with its published-practice divergence visible. The
highest-priority unresolved item is deity installation, which remains
specialist-only pending a bounded product design.

The Wedding profile is likewise corrected: exact lunar-month exceptions,
Paksha-aware Tithis, weekday grades, Nakshatras, Nitya Yogas, Vishti and named
Lagnas replace the former Purna/Jaya and fixed-class proxies. Pada and complete
election-chart conditions remain mandatory practitioner checks, and the current
Drik Panchang methodology divergence is visible.

The Court profile is now narrowly scoped to filing or initiating a lawsuit.
Raman's weekday and Nakshatra rules, his recurring unfavorable-Tithi list and
conservative Mesha-Lagna gate replace the former Tuesday and Tithi-family
proxies. The remaining election-chart conditions are mandatory practitioner
checks, and legal deadlines and professional counsel always take precedence.

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
