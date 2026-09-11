# Election-chart interpretation conventions

This is the canonical policy boundary between source wording and reusable
election-chart computation. The machine-readable reference registry is the owner; the generated
browser contract is its exact mirror.

- Owner: `docs/reference/election-chart-interpretations.json`
- Browser mirror: `src/data/election-chart-interpretations.generated.json`
- Registry schema: `1`
- Applied-convention schema: `2` (unchanged)
- Election-rule schema: `4` (unchanged)

`selected` means that the repository has fixed a named computational meaning.
It does **not** mean the primitive is implemented or wired into an event. An
empty `implementation` list and `specified_unwired` implementation status
preserve that distinction. `partial` means released code consumes only a
documented subset. `unresolved` forbids
automation and ranking effects until a named mode is source-audited,
owner-accepted, versioned and tested.

## Claim/source ledger

| Concept | Canonical entry | Exact source locator | State |
|---|---|---|---|
| Aspect | `phaladeepika-full-graha-drishti-v1` | *Phaladeepika* II.23, Sastri 1950, book p. 18 / scan p. 55 | Selected and implemented for full classical aspects; partial and node aspects stay separate |
| Conjunction | `same-rasi-distributive-conjunction-v1` | Raman, Chapter X “Borrowing Money,” internal p. 45 / physical PDF p. 49 | Reusable Python/TypeScript primitive implemented with no degree orb; borrowing event effect remains unwired |
| Benefic/malefic | `phaladeepika-natural-graha-nature-whole-sign-v1` | *Phaladeepika* II.27, book pp. 19–20 / scan pp. 56–57; corroborating modern BPHS 3.11 witness | Selected, partially implemented for Annaprasana; generic Budha and benefic predicates remain #251 work |
| Dignity | `phaladeepika-rasi-dignity-v1` | *Phaladeepika* I.6, book pp. 3–4 / scan pp. 40–41 | Selected, partially implemented for Gold; not a strength score |
| Strength | `bounded-graha-strength-unresolved-v1` | Raman, Chapter XV “Surgical Operations,” internal pp. 64–65 / physical PDF pp. 68–69 | Unresolved; neither dignity alone nor an incomplete Shadbala may be relabelled strength |
| Fortification | `election-lagna-fortification-unresolved-v1` | Raman, Chapter IX marriage, internal pp. 41–42 / physical PDF pp. 45–46; Chapter XIV journey, internal pp. 60–61 / physical PDF pp. 64–65 | Unresolved; no composite fortification score |
| Affliction | `constituent-affliction-unresolved-v1` | Raman, Chapter XV “Surgical Operations,” internal pp. 64–65 / physical PDF pp. 68–69 | Unresolved; eventual output must expose constituent evidence |
| Combustion | `phaladeepika-kapoor-fixed-elongation-combustion-v1` | Kapoor commentary on *Phaladeepika* II.36, physical/printed pp. 26–27 | Selected for Guru and Shukra exact-chart use; not yet implemented or wired |
| Waxing/waning Chandra | `raman-180-degree-paksha-v1` | Raman, Chapter II “On certain special yogas,” internal p. 4 / physical PDF p. 7 | Selected with a separately disclosed 0.02° precision guard |
| Lord relationships | `phaladeepika-natural-relationships-v1` | *Phaladeepika* II.21–22, book p. 17 / scan p. 54 | Selected, partially implemented for Gold; temporary and compound modes unresolved |
| Navamsa | `bphs-modality-navamsa-v1` | BPHS 6.12 | Selected with a separately disclosed 0.01° internal-boundary guard |
| Hemming | `lagna-hemming-unresolved-v1` | Raman, Chapter IX marriage, internal pp. 41–42 / physical PDF pp. 45–46 | Unresolved; no hidden node, nature, aspect or orb semantics |
| Named Yoga | `named-election-yoga-patterns-unresolved-v1` | Raman, Chapter IX marriage, internal pp. 41–42 / physical PDF pp. 45–46 | Unresolved; every Yoga needs its own source and Boolean pattern |

The authoritative machine-readable source records, artifact identities,
verification states and scope caveats are in `provenance.json`. The table is a
review aid, not a second source of truth.

## Selected formulae and boundaries

### Full Graha Drishti

Let `delta = (target Rasi - source Rasi + 12) mod 12`. Every classical
graha uses offset `6`; Kuja additionally uses `3, 7`, Guru `4, 8`, and Shani
`2, 9`. The relation is directed. Nodes, conjunction, self and partial aspects
do not satisfy this mode.

### Same-Rasi distributive conjunction

The Borrowing mode is
`R(Chandra) = R(Kuja) OR R(Chandra) = R(Shani)`. Either equality controls the
prohibition. Pass requires both inequalities to resolve. There is no angular
orb and this mode is not a global default.

The Python owner is
`telugu_panchangam/personal/election_assessors/conjunction.py`; the browser
mirror is `src/scorer/election-assessors/conjunction.ts`. Both consume only a
strictly admitted, complete nine-graha chart. Missing, malformed, duplicate or
conflicting facts return `unknown`. At one sampled state, either known equality
returns `fail`; both known inequalities return `pass`.

The window combiner is also three-valued: a known failure dominates unknown,
unknown dominates pass, and an all-pass set is still `unknown` when an interior
Rasi transition is not covered or the chart-request budget is exhausted. The
shared synthetic oracle covers both sides of the 360°/0° ingress, empty
samples, malformed input and every precedence branch.

The separately named event policy
`borrowing-money.same-rasi-conjunction-reject-v1` records that a future
Borrowing assessor will map a known failure to `reject`. Its status is
`specified_unwired`: the primitive is not imported by an event evaluator, the
existing manual check remains visible, and no score, ordering, completion
count or user-facing result changes in this delivery.

### Natural graha nature

Surya, Kuja, Shani, mean Rahu and mean Ketu are fixed malefics; Guru and Shukra
are fixed benefics. Chandra follows `raman-180-degree-paksha-v1`. Budha becomes
malefic only under the selected same-Rasi association policy. Functional
lordship is a different, currently unresolved fact.

### Exact-chart combustion

For Guru or Shukra, compute the shortest longitude separation from Surya:

`delta = abs(((longitude(graha) - longitude(Surya) + 180) mod 360) - 180)`

The Kapoor thresholds are Guru `11°`, direct Shukra `10°`, and retrograde
Shukra `8°`. Version 1 returns combust below `T - 0.02°`, clear above
`T + 0.02°`, and unknown inside the guard. This does not reuse the
observer/atmosphere-dependent heliacal calendar.

### Lunar phase

Let `E = (Chandra longitude - Surya longitude) mod 360`. Waxing is
`0.02 < E < 179.98`; waning is `180.02 < E < 359.98`. The guarded cells around
conjunction and opposition are unknown because the source does not classify
the exact boundaries and the chart contract rounds to two decimals.

### Navamsa

Divide a Rasi into nine parts. Start from that Rasi for movable signs, its ninth
for fixed signs, and its fifth for dual signs, then advance by the zero-based
division index. A value within `0.01°` of an internal division boundary is
unknown.

## Precedence and conflicts

Every evaluator remains three-valued: `pass`, `fail`, or `unknown`. A source
clause and its computational convention remain separate claim IDs. An event
effect (`reject`, `qualify`, or `prefer`) is a third layer and cannot be inferred
from either one.

Unresolved concepts produce no automated result. Selected conventions do not
silently absorb their alternatives: full aspects do not absorb partial or node
aspects; natural relationships do not absorb temporary ones; same-Rasi
association does not imply a degree orb; dignity does not imply complete
strength; and one named Yoga cannot authorize another.

Existing privacy, batching, local Drik/Lahiri Whole Sign projection, mean-node,
five-minute Lagna-transition guard and fail-closed exact-chart contracts remain
unchanged. Primitive and event tickets must reference these stable registry IDs
and may only mark an implementation path after parity and boundary tests pass.
