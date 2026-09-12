# Lawsuit-Filing Muhurtam Profile

## Status and scope

The user-facing `court` activity is a **verified Raman-lineage profile** for
filing or initiating a lawsuit. It is not a generic legal-matter election and
does not cover hearings, responses, settlement, appeals or case outcomes. Its
source claim is `muhurta.court.filing_lawsuit`.

The bibliographic authority is B. V. Raman, *Muhurtha (Electional
Astrology)*, UBS Publishers' Distributors, 1993. The cited Chapter XVII
passage, “Miscellaneous elections,” section “Filing law-suits,” was inspected
in the distinct 2020 Chistabo derivative at internal printed page 67
(physical PDF page 71). Raman's work is a modern secondary authority, not
scripture; verification means that the implemented criteria match this named
passage, not that every lineage treats them as universal.

## Criterion crosswalk

| Source criterion | Implementation | Boundary |
|---|---|---|
| Avoid Tuesday and Saturday | `allowed_varas` admits the other five weekdays | Hard day gate |
| Avoid the usual unfavorable lunar days | `avoid_tithi_numbers` = 4, 6, 8, 9, 12, 14, 15 | The passage does not define “usual.” The unchanged list is a conservative project policy recorded below; 15 covers both Pournami and Amavasya. |
| Ten named Nakshatras are good | Exact `allowed_nakshatras` list | Hard day gate |
| Lagna, or at least Navamsa, should be Mesha | `court.mesha-lagna-or-navamsa` | A resolved miss rejects. The Python/MCP finder retains its conservative Mesha-D1 gate because it has no exact-chart sidecar; the Drik browser may retain a non-Mesha D1 candidate provisionally until guarded D9 resolves. |
| Strengthen Lagna with Guru in a Trikona | `court.guru-trikona` | Score-neutral tie-break preference. |
| Place no malefic in the 6th | `court.house-6-without-natural-malefic` | A resolved natural-malefic occupant rejects. |
| Keep Lagna and 6th lords as far apart as possible | `court.lagna-sixth-lords-max-separated` | Binary, score-neutral tie-break preference under the registered maximum-distance convention. |
| Benefics in Kendras, or benefic aspects from male Rasis, indicate peace | `court.peace-benefic-pattern` | Non-ranking information only; never a guarantee of settlement, victory or success. |

## Tithi shorthand decision

The Chapter XVII paragraph says only “Avoid the usual unfavorable Tithis.” It
does not identify a cross-reference. Direct inspection found three materially
different reusable lists in the same artifact:

| Candidate | Exact locator | Avoided Paksha-local ordinals |
|---|---|---|
| General hints | Chapter II, internal printed p. 6 / physical PDF p. 9 | 4, 8, 12, 14 |
| General Panchang Suddhi | Chapter V, internal printed p. 12 / physical PDF p. 15 | 4, 6, 8, 12, 14, 15 |
| Namakarana | Chapter VIII, internal printed p. 22 / physical PDF p. 25 | 4, 6, 8, 9, 12, 14, 15 |

The first list is on the Chapter II “General hints” page immediately before
Chapter III; it is not a Chapter III rule despite an earlier ticket shorthand.
The Namakarana locator is therefore ratified as printed p. 22 / physical PDF
p. 25, but the Court paragraph never says to inherit Namakarana. Version 1
keeps the existing 4, 6, 8, 9, 12, 14 and 15 behavior as the explicit
`court-tithi-operational-policy-v1`. In particular, Navami rejection is a
conservative project interpretation, not quoted Chapter XVII wording. No
candidate behavior changes in this policy record.

## Effect and baseline policy

The five atomic chart clauses have separate product effects:

| Rule | Effect | Consequence |
|---|---|---|
| Mesha Lagna or Mesha Navamsa | `reject` | A resolved miss removes the candidate. |
| Guru in a Trikona | `prefer` | Tie-break evidence only; no raw-score change. |
| No natural malefic in the sixth | `reject` | A resolved natural-malefic occupant removes the candidate. |
| Lagna and sixth lords maximally separated | `prefer` | Binary tie-break evidence; no graduated score. |
| Peace benefic pattern | `inform` | Explanation only; never affects score, rank, tier, admission or outcome prediction. |

`general_baseline_mode` is `none`: the p. 67 paragraph does not explicitly
incorporate a general election baseline. Tarabalam, Chandrabalam, Muhurta
nature, Choghadiya, Nitya Yoga, Anandadi, personal Lagna fit and Panchaka can
still affect the upstream product shortlist, but they are disclosed product
policy rather than Court-source rules. This Court-specific decision does not
claim that the broader baseline registry in issue 292 is complete.

### Mesha D1-or-D9 predicate foundation

Issue 395 adds a mirrored, three-valued predicate for the first chart clause:

- authoritative local Drik/Lahiri Mesha D1 passes immediately;
- otherwise the sidecar's exact Lagna degree can derive D9 only when its Rasi
  agrees with the canonical local D1;
- guarded Mesha D9 passes, while two resolved non-Mesha values fail;
- missing or conflicting authority, a value within 0.01 degrees of a 3 degrees
  20 minutes Navamsa boundary, incomplete transitions, non-Drik input, and
  chart unavailability remain `unknown`.

Issue 400 wires this predicate into the integrated five-rule assessor. In the
Drik browser, a valid non-Mesha D1 candidate can survive the initial activity
gate only provisionally; it is shown as resolved only when the guarded D9 arm
passes. A resolved D1/D9 miss is removed, while a missing, conflicting or
boundary-guarded fact stays visibly review-gated. The Python/MCP finder keeps
its earlier D1-only gate because that surface has no exact-chart sidecar.

## Safety and alias boundary

Legal deadlines, court rules, counsel, evidence and personal safety always
take precedence over electional timing. A Muhurtam cannot predict or guarantee
a legal outcome. Scope and legal-safety disclosures are `inform` rows: neither
can make a chart result unknown, incomplete or practitioner-reviewed.

The legacy internal `litigation` key is now an explicit compatibility alias for
this narrow filing profile. It does not represent a broader election.

## Guru-Trikona computation foundation

Issue 396 added the computation foundation for the source
clause “strengthen Lagna with Guru in a Trikona.” Under the registered
`whole-sign-physical-occupation-v1` convention, the predicate passes exactly
when Guru occupies house 1, 5 or 9 from the validated local Drik/Lahiri Lagna.
It fails in every other house and returns `unknown` when the complete canonical
nine-graha chart or local-Lagna house frame is unavailable or contradictory.

The predicate is a preference only. It never rejects a candidate, changes raw
score, predicts a legal outcome or treats Guru's occupation as proof that
Lagna is otherwise strong. A preference is earned only when every represented
chart state passes and both local-Lagna and Guru-Rasi transition coverage are
complete within the chart-request budget. A known non-Trikona state defeats an
unrelated unknown; incomplete coverage never earns the preference.

The shared Python/TypeScript oracle is labelled
`synthetic_contract_fixture`, not a source golden. Issue 400 now wires the
result as a score-neutral preference. It can break a tie only after every
represented state and transition is resolved; a miss adds no penalty.

## Sixth-house natural-malefic computation foundation

Issue 397 adds the source clause “place no malefic in the 6th” as a mirrored,
three-valued predicate. It consumes the shared
`phaladeepika-natural-graha-nature-whole-sign-v1` classifier delivered by issue
354; Court does not define another benefic/malefic list. A resolved fixed
malefic, waning Chandra, or malefic-associated Budha physically occupying
Whole Sign house 6 fails. Fixed benefics and a sixth house without a resolved
natural malefic pass. A phase-guarded Chandra or conditionally unresolved
Budha remains `unknown` only when no known malefic already controls.

The accepted `muhurta.court.effect_policy_v1` maps a known failure to `reject`.
Across a candidate window, a known failure defeats unrelated unknown evidence;
otherwise unknown defeats pass. An all-pass result still requires complete
local-Lagna, graha-Rasi, Chandra-phase and Budha-association transition
coverage within the request budget.

Issue 400 wires this result as a hard Court gate: a known failure removes the
candidate, while an unknown keeps it visible with a review cap. It preserves
`general_baseline_mode = none`; a future general election baseline must not
double-count this Court-specific exclusion. The shared oracle is a
`synthetic_contract_fixture`, not a source golden or outcome prediction.

## Lagna–sixth-lord separation computation foundation

Issue 398 resolves Raman's qualitative “as far apart as possible” phrase with
the owner-accepted `court-lagna-sixth-lord-whole-sign-opposition-v1` policy.
The reusable lordship layer derives both lords from the classical seven-graha
table supported by *Phaladeepika* I.6; Rahu and Ketu never become lords. It then
computes the undirected shortest distance between their observed Rasis on the
twelve-sign circle. The Court preference passes only at the maximum distance
of 6. A same-owner Lagna/sixth pair has distance 0 and therefore does not earn
the preference.

This numerical formula is project policy, not wording supplied by Raman. Exact
angular opposition was not selected because the passage gives no orb or
precision threshold. “Best among the returned candidates” was also rejected
because it would make the same chart change status when unrelated candidates
are added or removed. The result is therefore a stable binary
`pass | fail | unknown`, never a graduated score.

Across a candidate window, any represented miss prevents the preference;
otherwise unknown defeats pass. An all-pass result still requires complete
local-Lagna, Lagna-lord-Rasi and sixth-lord-Rasi transition coverage within the
chart-request budget. Issue 400 wires the result as a score-neutral tie-break
preference; a miss or unknown never reduces the raw Panchangam score.

## Peace-pattern information foundation

Issue 399 resolves the final sentence's ambiguous grammar under the
owner-accepted `court-peace-benefic-subject-continuity-v1` convention. The
subject “benefics” continues across both OR arms: either a resolved natural
benefic physically occupies Whole Sign house 1, 4, 7 or 10, or a resolved
natural benefic in an odd/male Rasi receives a full classical aspect from a
different resolved natural benefic. The six odd Rasis are Mesha, Mithuna,
Simha, Tula, Dhanu and Kumbha.

The implementation consumes the existing natural-nature, Whole Sign
occupation and directed full-Graha-Drishti conventions. It does not reverse
the aspect direction, expand the second arm to any planet, or admit partial,
node, self, functional-benefic or conjunction semantics. Either resolved arm
passes; without a pass, a potentially satisfying unresolved nature or aspect
returns `unknown`, while only a fully resolved miss returns `fail`.

That status is informational, not evaluative. A miss never predicts conflict,
failed settlement, victory or loss. Missing facts affect chart-completion
disclosure only. Across a window, a positive statement requires every
represented state plus complete local-Lagna, graha-Rasi, Chandra-phase,
Budha-association and full-aspect transition coverage. This foundation remains
non-ranking after issue 400 integration: it changes no score, rank, tier,
admission or qualification.

## Integrated assessor and completion boundary

Issue 400 delivers one integrated five-rule assessor for `court`; the legacy
`litigation` alias canonicalizes to the same rules and produces the same
result. The default mode contains only the five Raman clauses above. The
optional Chintamani/Ghata-Chandra proposal in issue 300 is not selected or
silently blended into this mode.

The browser samples the first and final represented minute, each ten-minute
cadence point, and both sides of every known canonical Drik/Lahiri Lagna
transition. A positive completion claim additionally requires:

- canonical Lagna coverage without an edge-overlapping five-minute convention
  guard;
- sidecar Lagna agreement at every sample, guarded Navamsa endpoints, and less
  than one Navamsa of forward Lagna motion between adjacent samples;
- complete nine-graha facts whose sampled motion stays within the documented
  24 degrees/day body envelope, with no unrepresented Rasi boundary;
- Chandra-Surya relative motion within 48 degrees/day and no unrepresented
  waxing/waning boundary; and
- no exhausted chart-request or candidate budget.

A represented hard-gate failure wins even if some unrelated evidence is
unknown. Otherwise, malformed facts, a cadence gap above ten minutes, an
unrepresented transition, a non-Drik system, unavailable calculation or an
exhausted budget remains visibly incomplete. Scope and legal-safety rows stay
informational/practical disclosures and do not themselves trigger review.
