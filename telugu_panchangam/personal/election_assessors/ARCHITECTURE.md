# Election assessor boundaries

Python is the owner implementation and TypeScript is its browser mirror. The
legacy `primitives.py` and `primitives.ts` paths are compatibility façades;
new code imports the domain owner directly.

| Domain | Python owner | TypeScript mirror | Admission rule |
| --- | --- | --- | --- |
| interpretation policy | `docs/reference/election-chart-interpretations.json` | `election-chart-interpretations.generated.json` | Source wording, selected computation, alternatives and unresolved states only; it does not evaluate or apply event effects |
| chart geometry | `chart_geometry.py` | `chart-geometry.ts` | Rasi/Navamsa geometry, house predicates, classical full aspects, and transition envelopes only |
| graha nature | `graha_nature.py` | `graha-nature.ts` | Natural benefic/malefic classification and lunar-phase policy only |
| combustion | `combustion.py` | `combustion.ts` | Reserved for the accepted combustion foundation; do not place it in geometry |
| conjunction | `conjunction.py` | `conjunction.ts` | Reserved for the accepted conjunction foundation; do not place it in geometry |
| classical Rasi lordship and separation | `lordship.py` | `lordship.ts` | Seven-graha sign ownership and undirected Whole Sign distance only; nodes and event effects stay outside |
| benefic placement and aspect patterns | `benefic_patterns.py` | `benefic-patterns.ts` | Natural-benefic Kendra/odd-Rasi full-aspect OR facts only; event effects stay outside |
| Court event rules | `court.py` | `court.ts` | Source-scoped Court predicates and their event effects; reusable Rasi/Navamsa, house, nature, lordship and aspect facts stay in their domain owners |
| Vedha | `vedha.py` | `vedha.ts` | Reserved for the accepted Vedha foundation and its source-specific facts |
| event admission | `event_admission.py` | `event-admission.ts` | Validate and normalize complete chart facts before predicate evaluation |
| non-scoring event context | `event_context.py` | `event-context.ts` | Reserved for disclosed context that cannot affect score or admission |

Reserved paths are boundaries, not empty modules. They are created only when
their accepted issue lands. Source- or event-specific policy belongs in its
domain module or event assessor, never in chart geometry. Every future mirrored
module must preserve JSON fixture parity and remain dependency-acyclic: the
interpretation registry constrains domain meanings; contracts and facts feed
domains; domains feed event assessors; and event assessors feed the public
election-chart evaluator. A selected registry entry with an empty
`implementation` list and `specified_unwired` status is approved policy
metadata, not delivered computation; `partial` identifies an existing bounded
consumer without claiming the generic primitive complete.
