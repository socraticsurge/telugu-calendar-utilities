# Natural graha nature v1

`phaladeepika-natural-graha-nature-whole-sign-v1` is a reusable, three-valued
classifier for election-chart predicates. It answers only whether each graha
is a **natural benefic**, **natural malefic**, or **unknown** under the stated
convention. It does not decide whether a graha is functionally favourable for
a particular Lagna or event.

No event scorer consumes this primitive yet. This page records the shared
contract that event-specific assessors can later reference without redefining
benefic and malefic status.

## Authority and interpretation boundary

The textual core has two independently registered authorities:

- [*Phaladeepika*, V. Subrahmanya Sastri, second edition (1950)](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri/page/n55/mode/1up),
  Chapter II, sloka 27, book pages 19-20 / scan pages n55-n57; and
- *Brihat Parashara Hora Shastra* 3.11, in the Sanskrit, word analysis and
  translation published by
  [Enjoy Learning Sanskrit](https://enjoylearningsanskrit.com/scriptures/parashara/chapter-3/verse-11/).

Both identify Surya, Kuja, Shani, Rahu, Ketu and waning Chandra as malefic,
leave the remaining grahas benefic, and make Budha malefic when joined to a
malefic. The selected translations agree on that operative rule. They do not
state a numerical waxing/waning boundary or conjunction orb. Explanatory
thresholds found in other translations or commentaries can therefore differ;
v1 does not silently promote any such commentary into source wording.

The following are explicit **project conventions**:

| Choice | v1 rule | Why it is separate from the source |
|---|---|---|
| Chandra boundary precision | Inclusive 0.02-degree unknown bands around 0, 180 and 360 degrees | The source says waxing or waning but gives no precision threshold. The guard matches the two-decimal chart contract and fails closed. |
| Cross-runtime quantization | Normalize elongation to ten decimal places with non-negative round-half-up integer quanta before testing a boundary | Python and JavaScript otherwise disagree at exact half-quantum inputs because their built-in rounding tie rules differ. This is an implementation-parity rule, not source wording. |
| Budha association | `yuta` is represented as sharing the same sidereal Rasi | Neither cited verse supplies a degree orb. Same-Rasi is a reproducible Whole Sign convention, not a translation of a numeric conjunction rule. |
| Unknown precedence | A resolved malefic companion makes Budha malefic; phase-unknown Chandra alone makes Budha unknown | This preserves a decisive known witness without guessing Chandra's phase at a rounded boundary. |

## Inputs and validation

The primitive requires one complete canonical set of:

```text
Surya, Chandra, Kuja, Budha, Guru, Shukra, Shani, Rahu, Ketu
```

Each item must have a canonical sidereal Rasi, a finite degree in `[0, 30)`,
an integer Whole Sign house in `[1, 12]`, and a Boolean retrograde flag. A
missing, duplicated, unknown or malformed item invalidates the set. The
classifier then returns `unknown` for every graha; it never computes from a
valid-looking subset.

The upstream election-chart contract is responsible for the Drik/Lahiri,
mean-node and local Whole Sign frame described in
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).
This pure primitive does not call an ephemeris or repair metadata.

## Formula

Let `L(g)` be the canonical sidereal longitude reconstructed from a graha's
Rasi and degree. Normalize Chandra's elongation from Surya as:

```text
E = (L(Chandra) - L(Surya)) mod 360
Q = round-half-up-nonnegative(E * 10^10)

0.02*10^10 < Q < 179.98*10^10       => Chandra is benefic
180.02*10^10 < Q < 359.98*10^10     => Chandra is malefic
distance to 0/180/360
  less than or equal to 0.02*10^10 => Chandra is unknown
```

The remaining rules are:

```text
fixed malefic = Surya, Kuja, Shani, Rahu, Ketu
fixed benefic = Guru, Shukra

Budha shares a Rasi with any resolved malefic => malefic
Budha shares a Rasi with phase-unknown Chandra,
  and no resolved malefic                     => unknown
otherwise                                     => benefic
```

The generated browser contract stores the fixed sets, guard, association
mode, house system and provenance claim IDs. Python reads the source
convention, TypeScript reads its generated JSON projection, and both consume
the same behavioural fixture.

## House-set witness predicates

Two predicates turn resolved natures into event-independent building blocks:

| Predicate | Pass | Fail | Unknown |
|---|---|---|---|
| Existential benefic | At least one resolved benefic occupies any required house | No benefic and no unknown-nature occupant occupies the set | No resolved benefic exists, but an unknown-nature occupant could satisfy it |
| Forbidden malefic | No malefic and no unknown-nature occupant occupies any forbidden house | At least one resolved malefic occupies the set | No resolved malefic exists, but an unknown-nature occupant could violate it |

The witness is decisive: a known benefic makes the existential predicate pass
even beside an unknown occupant, and a known malefic makes the prohibition
fail even beside an unknown occupant. Evidence names the decisive or unresolved
occupants and their houses.

## Verification and limitations

The shared fixture covers every fixed graha, waxing and waning Chandra,
inclusive guards at 0/180/360, values immediately outside each guard, Budha
alone and with fixed, waxing, waning or phase-unknown companions, half-quantum
rounding ties, incomplete
and malformed charts, and pass/fail/unknown/conflict witness cases. Python and
TypeScript execute that same fixture.

This slice deliberately excludes functional lordship, dignity, strength,
combustion, aspects, degree-based conjunction, affliction, cancellation and
event-specific ranking. It also does not prove a whole time window. Before an
event assessor can claim continuous-window completion, issue #254 must sample
both sides of Chandra phase boundaries and every relevant graha Rasi ingress,
in addition to Lagna boundaries. Until then, affected window-level clauses
remain `unknown`.

Implementation and verification artefacts:

- [Python graha-nature owner](../../telugu_panchangam/personal/election_assessors/graha_nature.py)
- [TypeScript graha-nature mirror](../../src/scorer/election-assessors/graha-nature.ts)
- [Shared fixture](../../tests/fixtures/natural_graha_nature_v1.json)
- [Provenance register](provenance.json)

