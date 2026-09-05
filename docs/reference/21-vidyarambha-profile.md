# Aksharabhyasa (First-letter writing) source profile

## Product identity and exact scope

This profile assesses the first-letter-writing rite described under B. V.
Raman, *Muhurtha (Electional Astrology)*, Chapter VIII, “Post-natal
ceremonies” / “Commencing education (Aksharabhyasa),” internal printed page
23 (physical PDF page 26) in the inspected 2020 Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

The bibliographic work and inspected artifact are deliberately separate:

- `BVR-MUHURTHA-1993` is the catalogued 181-page UBS 1993 work. No scan of
  that edition was inspected.
- `BVR-MUHURTHA-CHISTABO-2020` is the directly inspected 78-physical-page
  2020 Chistabo re-edited transcription. Its editorial notice, checksum,
  byte size, and page-number model are registered in
  [the provenance ledger](provenance.json).

The controlling passage is B. V. Raman, Chapter VIII, “Post-natal ceremonies”
/ “Commencing education (Aksharabhyasa),” at **internal printed p. 23
(physical PDF p. 26)** in the inspected derivative. The catalogued work is
linked as the related bibliographic identity; exact edition equivalence has
not been established.

Raman is a modern synthesis, not primary scripture. This product helps audit
one disclosed election method. It neither limits when a child may learn nor
replaces educational, developmental, family, or officiant judgment.

## Inputs and chart facts

The browser first applies the documented Panchangam, safeguard, and personal
gates. Surviving Drik candidates are sampled at the offered window edges and
on both sides of each known interior Drik Lagna transition. The sidecar
supplies nine-graha Rashis; the browser recomputes Whole Sign houses in the
validated local Drik/Lahiri Lagna frame.

Let:

- `H(p)` be the recomputed Whole Sign house of graha `p`.
- `G` contain Surya, Chandra, Kuja, Budha, Guru, Shukra, Shani, mean Rahu,
  and Ketu.
- `S` be every chart sample used for an offered window.

## Exact predicates and product effects

| Rule ID | Exact predicate at one sample | Effect |
|---|---|---|
| `vidyarambha.house-8-vacant` | `for every p in G: H(p) != 8` | **Hard reject.** Any known occupant of house 8 removes the candidate. |
| `vidyarambha.budha-shukra-guru-9` | `H(Budha) = 9 AND H(Shukra) = 9 AND H(Guru) = 9` | **Preference only.** A pass supplies one tie-break; it changes neither raw score nor tier, and a miss has no penalty. |

The second formula is the project convention
`vidyarambha-benefic-trio-co-location-v1`, registered under
`election_chart.vidyarambha_co_location_policy_v1`. The inspected English
text names the three grahas and the ninth house but does not explicitly
distinguish all-three co-location from distributive or alternative readings.
Version 1 therefore selects the strict, reproducible AND interpretation. It
does not invent dignity, aspect, orb, house-lord, strength, or composite-score
conditions.

## Precedence and window aggregation

The source does not state whether the favorable trio can neutralize the
separately stated vacant-eighth condition. The owner-approved project
convention `election_chart.vidyarambha_reject_precedence_policy_v1` resolves
that product ambiguity as:

```text
vacant-eighth hard reject > all eligibility gates > trio preference tie-break
```

Therefore a failed vacancy rule always rejects, even when the trio passes.
The trio never changes raw score or tier and never cancels a Panchangam,
personal, safeguard, or chart rejection. This precedence is explicitly a
project convention, not textual authority.

The window aggregator behaves exactly as follows:

| Rule | Sample states | Window state and disposition |
|---|---|---|
| Vacancy | Any `fail` | `fail`; reject |
| Vacancy | No fail, at least one `unknown` | `unknown`; retain for review |
| Vacancy | Every sample `pass` | `pass` |
| Trio | Every sample `pass` | `pass`; one tie-break preference |
| Trio | Every sample definitively `fail` | `fail`; retain without preference or penalty |
| Trio | Mixed pass/fail, or unresolved samples | `unknown` and unstable; retain for review |

When the local house frame is uncertain, both rules are unknown; the browser
does not substitute the sidecar's house numbers. Missing, malformed,
duplicated, noncanonical, or out-of-range nine-graha facts also fail closed.
An unknown rule kind returns unknown and cannot fall through to another
predicate.

## Why the assessment remains partial

Both event-specific Chapter VIII chart clauses are now computed. The product
still labels the overall chart assessment **partial/provisional**, because
the shared general election-chart baseline tracked by issue #284 is not yet a
completed assessor. A valid result means the two disclosed Chapter VIII
predicates were evaluated; it is not complete chart certification.

Non-Drik searches, unavailable chart service, malformed responses,
boundary-uncertain frames, and bounded candidate searches add their own
separate incompleteness. The child-age and ceremony-time disclosures remain
information rather than chart predicates.

## Full rule-to-code crosswalk

| Source statement represented | Implementation | Treatment |
|---|---|---|
| Most propitious marker: fifth day, fifth month, fifth year | First manual information row | Disclosed guidance, not a finder input. |
| Monday, Wednesday, Thursday, and Friday are good | `allowed_varas` | An unlisted weekday rejects the day. |
| Eight named Nakshatras are good | `allowed_nakshatras` | An unlisted active slot-time Nakshatra rejects the candidate. |
| Movable and common Rashis are good | `allowed_lagnas` | Four Chara and four Dvisvabhava Rashis form the slot-time allow-list. |
| Prefer forenoon and noon | Second manual information row | Preference disclosure; no invented hard cutoff. |
| Leave the eighth vacant | `vidyarambha.house-8-vacant` | Exact nine-graha vacancy predicate; hard rejection on failure. |
| Budha, Shukra, and Guru in the ninth | `vidyarambha.budha-shukra-guru-9` | Strict AND/co-location convention; tie-break only. |

## Material alternatives kept separate

### Raman Chapter XI: broader education elections

Chapter XI, “Elections Pertaining to Education,” appears at **internal printed
pp. 46–47 (physical PDF pp. 50–51)** in the inspected derivative. It discusses
beginning study generally and then fields including Vedas, astrology, grammar,
medicine, music, science, and trades. Its Nakshatra, Tithi, Lagna, Yoga, and
chart guidance is a different scope. It is registered as
`muhurta.vidyarambha.raman_chapter_xi_scope`, not blended into this Chapter
VIII first-letter-writing assessor.

### Muhurta Chintamani 5.37–5.38: distinct lineage

The 1945 fifth Nirnaya Sagar edition of Rama Daivajna's *Muhurta Chintamani*,
with commentary catalogued under Narayanram Acharya, distinguishes
Akshararambha in verse 5.37 from Vidyarambha in verse 5.38 and gives its own
Tithi, Nakshatra, Vara, Lagna, and benefic-placement conditions:

- [verse 5.37, internal printed p. 197 / physical scan p. 213](https://jainqq.org/explore/002342/213)
- [verse 5.38, internal printed p. 198 / physical scan p. 214](https://jainqq.org/explore/002342/214)

Registered source ID: `MC-NSP-1945-5E`. These verses do not
support the Raman Budha-Shukra-Guru trio. They are documented as
`muhurta.vidyarambha.chintamani_divergence`, not used as corroboration and
not merged into v1.

## Deterministic verification corpus

The shared Python/TypeScript oracle covers:

- full pass;
- hard rejection;
- preference miss retained without score or tier change;
- simultaneous trio pass and vacancy failure, proving reject precedence;
- missing, malformed, duplicated, and out-of-range facts;
- mixed preference states;
- every-sample preference failure;
- house-frame uncertainty.

The projection replay adds four dates across Hyderabad and Washington, D.C.
It distinguishes external first-instant anchors from local DashaFlow contract
projections and does not present the local projections as published-page
matches.

Machine-readable evidence:

- `tests/fixtures/election_chart_vidyarambha_oracle.json`
- `tests/fixtures/election_chart_vidyarambha_projection.json`

## Product contract and limits

Shared samskara exclusions, hard avoid windows, Amrit-Choghadiya and
Tithi-family ranking preferences, personal scoring, raw weights, relative
tiers, and the shared baseline are not established by the Chapter VIII
citation. MCP exposes the stable `vidyarambha` identifier, the public label,
the exact source scope, and the original manual disclosures. Python/MCP slot
ranking does not call the remote chart sidecar.

For the shared sampling, boundary, data-minimization, and failure contract, see
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).
