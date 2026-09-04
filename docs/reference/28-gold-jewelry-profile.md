# Gold / Jewelry Source and Computation Profile

## Source clause and authority

The `gold` activity is linked to `muhurta.gold_jewelry.purchase`. Its event
authority is B. V. Raman's *Muhurtha*, Chapter X, "Buying Jewelry," internal
printed page 45 (physical PDF page 49 in the inspected 2020 Chistabo
derivative). Raman is a modern secondary
authority, not scripture.

The passage says that Surya and Chandra should be well situated and aspected,
and that the usual unfavorable Tithis and Nakshatras should be avoided. It
does **not** define what “well situated” or “aspected” means, nor does it state
whether failure rejects a candidate. Those missing choices come from the
separately named interpretation and product-policy layers below; they do not
inherit Raman's authority merely because they make his clause computable.

## Gold v1 computation

For a successful Drik browser screen, the chart assessor evaluates four
positive `qualify` rules at every sampled chart state:

| Rule ID | Condition |
|---|---|
| `gold.surya-well-situated` | Surya is outside Whole Sign houses 6, 8 and 12; outside Rashis owned by its natural enemies Shukra and Shani; and outside its debilitation Rasi and Navamsa, Tula. |
| `gold.chandra-well-situated` | Chandra is outside Whole Sign houses 6, 8 and 12; outside its debilitation Rasi and Navamsa, Vrischika; and more than 12° from Surya, subject to a 0.02° rounding guard. The selected natural-relationship table gives Chandra no enemy Rasi, so v1 invents none. |
| `gold.surya-fully-aspected` | At least one other classical graha casts a full Graha Drishti to Surya. |
| `gold.chandra-fully-aspected` | At least one other classical graha casts a full Graha Drishti to Chandra. |

The placement convention is `phaladeepika-well-placed-v1`. Phaladeepika II.36
supplies the selected adverse-placement categories; I.6 supplies fall signs;
II.21–22 supplies natural relationships; and *Brihat Parashara Hora Shastra*
6.12 supplies the Navamsa sequence. The 12° Chandra solar-clearance threshold
and its precision guard are explicit project conventions: Phaladeepika states
the qualitative solar-ray condition but does not state that number.
*Surya-Siddhanta* X.1 gives historical rationale for a 12-degree lunar
visibility boundary, but its translator identifies the measure as time-degrees
in oblique ascension. V1's shortest-ecliptic-longitude test is therefore a
disclosed approximation, not an exact restatement of that verse.

The aspect convention is `phaladeepika-full-graha-drishti-v1`, based on
Phaladeepika II.23:

```text
every classical graha  -> 7th
Kuja                    -> 4th and 8th also
Guru                    -> 5th and 9th also
Shani                   -> 3rd and 10th also
```

Raman says “aspected,” not “benefically aspected.” V1 therefore accepts any
full classical Graha Drishti and shows the aspecting graha as evidence. It
does not count Rahu, Ketu, conjunction, partial aspects, degree orbs or
self-aspect. This is a disclosed literal interpretation, not a claim that
Raman selected Phaladeepika's model or that every lineage must use it.

Planetary Navamsa is computed by splitting each Rasi into nine 3°20′ parts.
Because the chart contract rounds a graha's degree to 0.01°, a value within
0.01° of any Navamsa boundary, including a Rasi edge, is `unknown` rather
than guessed across the boundary. Full-aspect geometry likewise treats a
rounded target Rasi edge as unknown. A potential aspector at an edge makes the
rule unknown only when no securely placed graha already supplies the required
full aspect.

## Transition-complete window evaluation

The browser includes the start and final represented minute, ten-minute
cadence points, and both sides of every known local-Lagna transition. Gold v1
then checks each adjacent chart pair under the separately registered
`election_chart.gold_transition_envelope_v1` policy.

NASA's *Moon Facts* lists a maximum lunar orbital velocity of 1.076 km/s and
a perigee distance of 363,300 km. Their ratio converts to 14.66°/day. Swiss
Ephemeris documents that its longitude-speed output is measured in degrees
per day. The assessor deliberately widens the engineering envelope to 24°/day
for any one classical graha and, by the triangle inequality, 48°/day for a
two-graha separation. This is a conservative product safety policy, not a
traditional formula or a claim that NASA states those chosen bounds.

At the maximum ten-minute gap, the envelope is 0.1667° for one graha and
0.3333° for a pair, with the chart contract's 0.005° half-step added for each
rounded endpoint. The algorithm applies these rules:

- if adjacent instants are missing, non-monotone, or more than ten minutes
  apart, all otherwise-passing Gold predicates fail closed to `unknown`;
- if sampled displacement itself exceeds the envelope, affected predicates
  fail closed;
- when endpoint states differ, both sides of the transition are already
  evaluated; the one-body envelope is much narrower than the smallest 3°20′
  Navamsa state, so more than one unrepresented division cannot be traversed;
- when endpoint states match but an expanded endpoint can reach a controlling
  Rasi, Navamsa, or 12° solar-clearance boundary, the predicate is `unknown`
  because a cross-and-return cannot be excluded; and
- a full-aspect pass requires at least one aspector whose relation stays
  securely present across the pair. Changing or boundary-adjacent aspectors
  alone cannot create an assumed pass.

A sampled known failure still dominates an unrelated unknown for the same
qualification rule. This closes the between-sample failure path at the
product's represented-minute resolution without pretending to know an exact
unreturned ingress second.

## Decision semantics

`Qualify` is a transparent ranking policy, not a textual command from Raman:

- all four rules pass across the sampled window: the chart clause is satisfied
  under Gold v1, meaning only these four event-specific clauses are resolved;
- a known failure in any sample: the slot remains available, but an otherwise
  `Excellent` tier is capped to `Good` while the raw score remains unchanged;
  this is a conclusive event-specific condition miss and does not receive
  practitioner-review wording; or
- no known failure, but a needed fact or guarded boundary is unresolved: the
  result is labelled indeterminate at a calculation boundary or missing fact,
  remains visible, keeps its raw score, earns no assumed pass and has a maximum
  `Good` tier pending review.

One slot can have a conclusive miss for one rule and an unknown for another.
The capped and review-gated summary counts can therefore overlap, and the UI
reports how many retained slots are included in both counts.

For one rule, aggregation is “fail if any sample fails; otherwise unknown if
any sample is unknown; otherwise pass.” A known failure therefore cannot be
hidden by another unresolved sample.

After a complete, valid Drik screen, the remainder for the four event-specific
Gold v1 conditions is empty: the UI must not ask a practitioner to re-check
those same conditions. This does not claim that the inherited general
election-chart baseline is complete; that separate work remains tracked in
[#284](https://github.com/socraticsurge/telugu-calendar-utilities/issues/284).
A non-Drik search is still `unsupported-system`; a missing or invalid chart
response is `unavailable`; and Python/MCP results do not call the DashaFlow
service. Those fallbacks retain the original full chart-check disclosure and
must not claim that Gold v1 ran.

## What the event citation does not support

The passage does not name a jewelry-specific weekday, Tithi, Nakshatra,
Lagna, or Choghadiya. Consequently, the existing Labh-Choghadiya,
Bhadra-Tithi, Friday/Thursday, and fixed-Lagna preferences remain explicitly
classified as project heuristics. They do not inherit textual authority from
the Gold claim, from Phaladeepika, or from the BPHS Navamsa verse.

Likewise, the automated chart result is not financial, authenticity or safety
advice, and it is not empirical evidence that electional astrology predicts a
purchase outcome. See
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md)
for sampling, privacy, fallback, source-register and verification details.

## Verification fixtures

The Gold test suite deliberately keeps two kinds of evidence separate:

- `tests/fixtures/election_chart_gold_oracle.json` is a synthetic predicate
  oracle. It isolates pass, fail, missing-fact and boundary behavior and is
  shared by the Python and TypeScript evaluators.
- `tests/fixtures/election_chart_gold_gateway_oracle.json` contains frozen,
  unedited HTTP 200 response cells from the governed public Astro guest gateway
  at gateway revision `4106f09708a154f1c2401880ebe8f9c0b9162eb5` and
  DashaFlow revision `c84fd856b17120c80e1bb7e455246a0ec8e429ea`. Its
  Hyderabad and Sydney cases span two dates and collectively exercise pass,
  fail, unknown, conflict and boundary outcomes. Each case asserts all nine
  unique grahas and Whole Sign house consistency before checking the Gold
  result.

The frozen gateway cells prove that the assessor accepts the actual deployed
calculation contract; they are not a second ephemeris comparison and do not
turn astrology into an empirically validated predictor.
