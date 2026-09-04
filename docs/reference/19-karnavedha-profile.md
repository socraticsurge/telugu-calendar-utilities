# Karnavedha source profile and assessor

## Named policy and authority boundary

The product's automated Karnavedha policy is
`raman-karnavedha-daylight-v1`. It follows B. V. Raman's *Muhurtha
(Electional Astrology)*, Chapter VIII, “Ear boring (Karnavedha),” as inspected
in the registered 2020 Chistabo derivative at internal printed page 23
(physical PDF page 26). The cross-reference to generally inauspicious Tithis
is inspected in Chapter V at internal printed page 12 (physical PDF page 15).

The provenance ledger distinguishes the bibliographic work
`BVR-MUHURTHA-1993` from the inspected artifact
`BVR-MUHURTHA-CHISTABO-2020`. The latter is a derivative copy rather than a
verified edition-matched scan; that relationship is part of the published
evidence record. Raman is a modern synthesis and secondary authority, not a
primary scripture.

This is a deliberately named lineage choice. Vidyamadhava's
*Vidyamadhaviyam*, volume II, chapter VI, verse 18 (printed page 39, commentary
page 41) gives daylight language but its commentary also describes a
before-Lagna exception. *Muhurta Chintamani*, Samskara-prakarana verses 24–25
(internal printed pages 184–185; Internet Archive leaves n192–n193), supplies
another comparator. Neither alternate is silently blended into the Raman
policy. Their differences are registered as related, contradicted claims so a
future policy may implement them explicitly without changing this result.

## The three effective predicates

| Rule ID | Input owner | Exact test | Product effect |
|---|---|---|---|
| `karnavedha.daylight-tithi-single` | Local Drik Panchangam day | The Tithi active at sunrise has no transition inside `[sunrise, sunset)` | Reject the complete day on fail or unknown |
| `karnavedha.daylight-nakshatra-single` | Local Drik Panchangam day | The Nakshatra active at sunrise has no transition inside `[sunrise, sunset)` | Reject the complete day on fail or unknown |
| `karnavedha.house-8-vacant` | DashaFlow candidate-time chart facts plus the selected-city Drik/Lahiri Lagna frame | All nine named Grahas are outside Whole Sign house 8 throughout the sampled candidate window | Remove only the failing candidate; unknown remains review-gated |

The first two predicates are evaluated once per civil day. They are not
duplicated per offered window and are not inferred by sampling candidate
times. DashaFlow is used only after a day passes, and only to supply
candidate-time planetary Rasi facts for the vacant-house predicate.

## Daylight algorithm

Let `S` be local sunrise, `E` local sunset, and let `[A, B)` be the exact
transition span returned for the limb active at `S`. The controlling interval
is half-open:

```text
valid_daylight = aware(S) and aware(E) and S < E
active_at_sunrise = aware(A) and aware(B) and A <= S < B
single_limb = valid_daylight and active_at_sunrise and B >= E
```

Therefore:

- a transition at sunrise belongs to the new limb and is included;
- a transition one instant before sunset is inside daylight and fails;
- a transition exactly at sunset is outside `[S, E)` and passes;
- a missing, timezone-naive, unordered, or non-covering boundary is
  `unknown`, and admission fails closed.

Python uses timezone-aware second-precision engine instants. The deployed ICS
feed exposes only civil minutes. A browser boundary in the same displayed
minute as sunset cannot prove the ordering, so it resolves `unknown` rather
than guessing. Next-day and previous-day markers are applied before comparing
minutes.

## Candidate-chart algorithm

For every bounded candidate window, the browser requests the already-defined
privacy-minimal DashaFlow chart facts at its start, final represented minute,
10-minute cadence, and known local Lagna-transition guard samples. It validates
the complete nine-Graha response and recomputes Whole Sign houses in the
selected-city Lagna frame:

```text
house(graha) = ((rasi(graha) - rasi(local_lagna) + 12) mod 12) + 1
vacant_8 = every graha has house(graha) != 8
```

Rahu and Ketu are included. A fail at any sampled state removes the candidate.
An incomplete chart, uncertain house frame, or unresolved between-sample
boundary produces `unknown` and never becomes a claimed pass. This bounded
sampling is disclosed honestly; it is not a continuous-time proof between
all instants.

## External boundary oracle

The engine and category decisions are pinned against eight manually inspected
DrikPanchang day pages. Direct HTTP retrieval returned 403, so the rendered
Chrome pages were inspected. DrikPanchang publishes minute precision; the
fixture permits at most ±120 seconds and separately requires the same
pass/fail category. The maximum observed timestamp difference is 91 seconds.

| Place and local date | Sunrise–sunset | Next Tithi transition | Next Nakshatra transition | Outcome |
|---|---|---|---|---|
| Hyderabad, 2026-01-01 | 06:46:10–17:52:54 | 22:22:44 | 22:48:34 | pass / pass |
| Hyderabad, 2026-01-03 | 06:46:50–17:54:06 | 15:32:54 | 17:28:02 | fail / fail |
| Hyderabad, 2026-01-08 | 06:48:13–17:57:09 | next day 07:05:55 | 12:24:41 | pass / fail |
| Hyderabad, 2026-03-13 | 06:25:53–18:25:25 | 06:29:31 | next day 03:03:18 | fail / pass |
| New York, 2026-01-01 (EST) | 07:20:06–16:39:24 | 11:52:44 | 12:18:34 | fail / fail |
| New York, 2026-01-03 (EST) | 07:20:14–16:41:08 | next day 02:00:27 | next day 04:41:29 | pass / pass |
| New York, 2026-01-11 (EST) | 07:19:16–16:49:00 | next day 02:13:13 | 07:42:17 | pass / fail |
| New York, 2026-05-04 (EDT) | 05:50:53–19:55:18 | 19:54:48 | next day 03:24:51 | fail / pass |

The source URLs, DrikPanchang minute values, engine second values, DST offsets,
expected categories and tolerance are preserved in
`tests/fixtures/karnavedha_daylight_drikpanchang_oracle.json`.

## Remaining profile rules

| Source statement | Implementation | Treatment |
|---|---|---|
| Perform on the 12th or 16th day after birth, or in the 6th, 7th or 8th month | `manual_checks` | Child age is not an input; it remains information for guardians. |
| Use forenoon or afternoon, never night | `daytime_only` | Night candidates are never generated, including MCP requests with `include_night`. |
| Reject generally inauspicious Tithis | `avoid_tithi_numbers` | Chapter V resolves 4th, 6th, 8th, 12th, 14th, Purnima and Amavasya; both terminal Tithis map to 15. |
| Monday, Wednesday, Thursday and Friday are good | `allowed_varas` | Other weekdays reject the day. |
| Reject Kumbha, Simha and Vrischika rising | `allowed_lagnas` | The other nine Rasis are admitted at candidate time. |

The shared samskara exclusions, additive scores, Tithi-family ranking,
personal scoring and relative tiers remain project rules not established by
this citation. Medical safety, consent, sterile technique and aftercare remain
matters for qualified practitioners and guardians.

## Surfaces and completion semantics

Python, MCP, the generated browser contract and the documentation crosswalk
publish the same policy ID and criterion IDs. A day admitted by both daylight
rules proceeds to candidate generation. A failed or unknown daylight rule
returns one day diagnosis naming each unresolved limb once; it does not call
the chart service. After chart screening, a conclusive occupied eighth house
removes the candidate, while an unavailable or incomplete chart remains an
explicit review gate. Once all three predicates pass, the UI no longer repeats
the former generic practitioner-review sentence for these clauses.
