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
| Avoid the usual unfavorable lunar days | `avoid_tithi_numbers` = 4, 6, 8, 9, 12, 14, 15 | “Usual” is resolved to Raman's recurring explicit list in the same inspected derivative; 15 covers both Pournami and Amavasya |
| Ten named Nakshatras are good | Exact `allowed_nakshatras` list | Hard day gate |
| Lagna, or at least Navamsa, should be Mesha | `allowed_lagnas = ['Mesha']` | Conservative hard slot gate; the Navamsa alternative remains manual because it is unavailable on every surface |
| Strengthen Lagna with Guru in a Trikona; no malefic in the 6th; keep Lagna and 6th lords apart | `manual_checks`; `manual_prerequisites = true` | Results cannot be rated Excellent until a practitioner checks the chart |
| Benefics in Kendras, or benefic aspects from male Rasis, indicate peace | Manual interpretive note | Never presented as a guarantee of settlement or success |

The recurring unfavorable-Tithi list is stated explicitly earlier in the same
inspected derivative in the Namakarana passage (Chapter VIII, internal printed
page 22, physical PDF page 25):
Chaturthi, Shashthi, Ashtami, Navami, Dwadashi, Chaturdashi, Pournami and
Amavasya. This cross-reference is disclosed because the lawsuit passage itself
uses shorthand rather than restating the numbers.

## Safety and alias boundary

Legal deadlines, court rules, counsel, evidence and personal safety always
take precedence over electional timing. A Muhurtam cannot predict or guarantee
a legal outcome.

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
