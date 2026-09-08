# Election assessor boundaries

Python is the owner implementation and TypeScript is its browser mirror. The
legacy `primitives.py` and `primitives.ts` paths are compatibility façades;
new code imports the domain owner directly.

| Domain | Python owner | TypeScript mirror | Admission rule |
| --- | --- | --- | --- |
| chart geometry | `chart_geometry.py` | `chart-geometry.ts` | Rasi/Navamsa geometry, house predicates, classical full aspects, and transition envelopes only |
| graha nature | `graha_nature.py` | `graha-nature.ts` | Natural benefic/malefic classification and lunar-phase policy only |
| combustion | `combustion.py` | `combustion.ts` | Reserved for the accepted combustion foundation; do not place it in geometry |
| conjunction | `conjunction.py` | `conjunction.ts` | Reserved for the accepted conjunction foundation; do not place it in geometry |
| Vedha | `vedha.py` | `vedha.ts` | Reserved for the accepted Vedha foundation and its source-specific facts |
| event admission | `event_admission.py` | `event-admission.ts` | Validate and normalize complete chart facts before predicate evaluation |
| non-scoring event context | `event_context.py` | `event-context.ts` | Reserved for disclosed context that cannot affect score or admission |

Reserved paths are boundaries, not empty modules. They are created only when
their accepted issue lands. Source- or event-specific policy belongs in its
domain module or event assessor, never in chart geometry. Every future mirrored
module must preserve JSON fixture parity and remain dependency-acyclic:
contracts and facts feed domains, domains feed event assessors, and event
assessors feed the public election-chart evaluator.
