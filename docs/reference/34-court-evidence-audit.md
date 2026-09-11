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
| Lagna, or at least Navamsa, should be Mesha | `allowed_lagnas = ['Mesha']` | Conservative hard slot gate; the Navamsa alternative remains manual because it is unavailable on every surface |
| Strengthen Lagna with Guru in a Trikona; no malefic in the 6th; keep Lagna and 6th lords apart | `manual_checks`; `manual_prerequisites = true` | Results cannot be rated Excellent until a practitioner checks the chart |
| Benefics in Kendras, or benefic aspects from male Rasis, indicate peace | Manual interpretive note | Never presented as a guarantee of settlement or success |

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

This is a `specified_unwired` predicate foundation. It does not broaden the
current D1-only shortlist or change ranking. Conditional-admission issue 285
may later retain only a valid non-Mesha D1 candidate whose D9 alternative is
still unresolved; a resolved D1/D9 miss is never eligible. Court integration
issue 400 owns the eventual reject wiring and user-visible completion claim.

## Safety and alias boundary

Legal deadlines, court rules, counsel, evidence and personal safety always
take precedence over electional timing. A Muhurtam cannot predict or guarantee
a legal outcome. Scope and legal-safety disclosures are `inform` rows: neither
can make a chart result unknown, incomplete or practitioner-reviewed.

The legacy internal `litigation` key is now an explicit compatibility alias for
this narrow filing profile. It does not represent a broader election.

## Guru-Trikona computation foundation

Issue 396 adds an explicitly unwired computation foundation for the source
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
`synthetic_contract_fixture`, not a source golden. This foundation is not yet
wired into the Court scorer, does not change completion counts and does not
remove any practitioner-review language. Those changes remain owned by the
Court effect-policy and completion children under the parent assessor issue.

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

This foundation remains `specified_unwired`: it changes neither candidate
admission nor score, rank, tier or completion counts until issue 400 integrates
the accepted Court predicates. It also preserves
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
chart-request budget. This remains `specified_unwired`: issue 400 owns its
event integration, so this foundation changes no score, tier, candidate order,
completion count or user-facing review text.

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
`specified_unwired` until issue 400 and changes no score, rank, tier,
admission, qualification or completion count.
