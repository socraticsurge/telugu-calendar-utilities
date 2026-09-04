# Annaprasana source profile

## What this implementation claims

The Drik browser path implements six **Annaprasana-specific** election-chart
clauses from the public B. V. Raman transcription identified below. A complete
result means only that those six clauses were evaluated across every represented
state of the candidate window. It does not close the general election-chart
baseline tracked in [issue #284](https://github.com/socraticsurge/telugu-calendar-utilities/issues/284),
and it is not a universal electional verdict.

Python and MCP return the Panchangam shortlist and the original source-guidance
rows. They do not request candidate-time charts. MCP therefore labels the exact
assessor `drik_browser_only` and the general baseline `open_issue_284`.

## Artifact identity and authority

The public file used here is
[B. V. Raman, *Muhurta*](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf),
a 78-page Chistabo derivative uploaded in 2020. Its physical PDF page 3 says it
was re-edited, that additions were placed in brackets, and that the appendix
was omitted. It is therefore registered as
`BVR-MUHURTHA-CHISTABO-2020`, the directly inspected derivative. The related
`BVR-MUHURTHA-1993` record preserves the
181-page UBS work's [Google Books](https://books.google.com/books/about/Muhurtha_Electional_Astrology.html?id=nHQlAcBkDXIC)
and [Open Library](https://openlibrary.org/books/OL9860226M/Muhurtha_%28Electional_Astrology%29)
bibliographic identity, but that edition was not inspected.
Located Raman claims cite both IDs: the UBS ID identifies the work while the
Chistabo artifact supplies the visible wording and page locator. The registry
does not claim that the derivative is the UBS edition.

The Annaprasana profile occupies Chapter VIII, internal printed pages 22–23
(physical PDF pages 25–26). All six chart clauses occur together on **internal
printed page 22 / physical PDF page 25**. The Chapter V cross-reference for
the general Panchanga-Suddhi Tithis is internal printed page 12 / physical PDF
page 15.

## Profile-to-code crosswalk

| Source criterion | Implementation | Product treatment |
|---|---|---|
| 6th, 8th, 9th or 12th month | original manual information row | Disclosed because the search does not take the child's age-month as input. |
| Twelve named Nakshatras | `allowed_nakshatras` | Conservative Panchangam admission gate. |
| General unfavorable Tithis | `avoid_tithi_numbers` | Chapter V cross-reference; 4, 6, 8, 12, 14 and both terminal lunar days, represented as 15. |
| Monday, Wednesday, Thursday and Friday | `allowed_varas` | Other weekdays reject the day. |
| Mesha, Vrischika and Meena rising are unfavorable | `allowed_lagnas` | The other nine Rasis form the slot-time admission set. |

The shared samskara exclusions, Choghadiya and Tithi-family weights, personal
scoring and relative tiers are project rules. They do not inherit authority
from the Annaprasana paragraph.

## Six-clause chart contract

All six rows use claim
`muhurta.annaprasana.raman_transcription_chart` and the exact locator
“B. V. Raman, Chapter VIII, ‘First feeding on rice (Annaprasana),’ Chistabo
derivative internal printed p. 22 (physical PDF p. 25).”

| Rule ID | Source wording represented | Effect |
|---|---|---|
| `annaprasana.house-10-vacant` | Leave the 10th unoccupied | Mandatory: any known failure removes the slot. |
| `annaprasana.budha-not-7` | Budha is outside the 7th | Mandatory. |
| `annaprasana.kuja-not-8` | Mangala is outside the 8th | Mandatory. |
| `annaprasana.shukra-not-9` | Shukra is outside the 9th | Mandatory. |
| `annaprasana.benefic-occupies-lagna` | Budha, Guru or Shukra in Lagna is commended | Preference only. Absence does not reject, change score or cap the rating; a fully resolved pass breaks ties. |
| `annaprasana.no-natural-malefic-in-lagna` | No natural malefic in Lagna | Mandatory under the separately disclosed classification below. |

“In Lagna” means physical occupation of Whole Sign house 1. The assessor does
not import the Namakarana passage's different “strengthen Lagna” instruction,
nor does it turn aspect, lordship or an undisclosed strength score into
occupation.

## Engineering conventions, kept separate from the text

### Whole Sign occupation

Using the validated local Drik/Lahiri Lagna Rasi, every returned graha is
projected locally:

```text
house(graha) = 1 + ((RasiIndex(graha) - RasiIndex(Lagna) + 12) mod 12)
```

All nine returned grahas count for vacancy. This is
`election_chart.whole_sign_house_policy_v1`, not a quotation from Raman.

### Natural-malefic set and node choice

The fixed set is Surya, Mangala, Shani, Rahu and Ketu. Chandra joins the set
only when classified as waning below. The enumeration has a modern supporting
witness in the Enjoy Learning Sanskrit rendering of
[BPHS 3.11](https://enjoylearningsanskrit.com/scriptures/parashara/chapter-3/verse-11/).
That page is registered as a `modern_text_witness`, not a critical edition.

Rahu and Ketu use the sidecar's explicitly returned **mean-node** convention.
Choosing mean nodes is `election_chart.mean_node_policy_v1`, a product
convention.

BPHS 3.11 also conditions Budha on association with a malefic. This version
limits “association” to same-sign occupation. It creates no second Budha
failure: the accompanying fixed natural malefic already fails the same Lagna
prohibition. Aspect, dispositor and lordship associations are not inferred.
That boundary is `election_chart.budha_same_sign_association_policy_v1`.

### Waxing and waning Chandra

Raman Chapter II, internal printed page 4 / physical PDF page 7, describes Chandra as
waxing below 180 degrees of longitude difference from Surya and waning above
180 degrees. The implementation makes the arithmetic explicit:

```text
E = (longitude(Chandra) - longitude(Surya)) mod 360
0 < E < 180       => waxing
180 < E < 360     => waning
```

If Chandra occupies Lagna, waxing passes this one prohibition and waning
fails. Because the chart contract reports two-decimal degrees and the source
does not classify exact conjunction/opposition, `E` at or within **0.02°** of
0° or 180° returns `unknown`. The split and boundary guard are separately
registered as `election_chart.raman_180_degree_paksha_policy_v1` and
`election_chart.lunar_phase_boundary_guard_policy_v1`.

### Sample aggregation and fail-closed behavior

Each window is checked at its represented start, final minute, ten-minute
cadence points, and both sides of every known interior local Lagna transition.

For a mandatory rule:

```text
any fail => fail
else any unknown => unknown
else => pass
```

For the positive Lagna preference, every sample must pass to earn the
preference; all-fail is a resolved preference miss; mixed pass/fail or any
unknown is `unknown`. A fixed natural-malefic failure in Lagna controls even
if Chandra simultaneously lies on a phase boundary. Missing, duplicate or
invalid chart facts fail closed. These are product decisions recorded under
`election_chart.annaprasana_fail_closed_aggregation_policy_v1`.

## Material source disagreement

The implemented policy is explicitly
`election_chart.annaprasana.raman_transcription_policy_v1`; it does not merge
conflicting lists.

| Witness | Exact locator | Visible difference |
|---|---|---|
| N. P. Subramania Iyer, [*Kalaprakasika*](https://storage.yandexcloud.net/j108/library/2xtizybv/N.P._Subramania_Iyer_-_Kalaprakasika.pdf), first English publication 1917; AES reprint 1982 | Chapter III, “To Feed on Rice,” printed p. 34 (public PDF p. 66; OCR lines 3305–3317) | Places **Shukra outside the 7th** and **Budha outside the 9th**, reversing Raman's Budha-7/Shukra-9 assignment. |
| Rama Daivajna, [*Muhurta Chintamani* with Piyushadhara commentary](https://jainqq.org/booktext/Muhurt_Chintamani/002342), Nirnaya Sagar Press, 5th ed., 1945 | Samskara-prakarana verse 18, printed p. 178 (scan p. 194); commentary printed p. 180 (scan pp. 196–197) | The verse places Chandra outside houses 1, 6 and 8. The commentary qualifies Lagna adversity as **weak or waning Chandra** and describes **full Chandra in Lagna** as favorable. This is not silently simplified to “Moon in Lagna is always prohibited.” |

Those differences are machine-registered as
`muhurta.annaprasana.source_divergence` with state `contradicted`. A future
source-selectable assessor would need its own policy and tests; it must not
quietly change this version.

## What the result states

- A hard failure removes the candidate and the UI lists the failed rule plus
  observed chart fact.
- A missing Lagna-benefic commendation is shown as “Preference not present ·
  no penalty.”
- A supported unknown retains the candidate, caps an otherwise Excellent
  rating at Good, and says review is still needed.
- Only an unbounded, fully resolved Drik run may say “Annaprasana
  event-specific chart assessment complete.” Every such result also says the
  general election-chart baseline #284 remains open.

The source IDs, claims, locators and convention scopes are canonical in
[`provenance.json`](provenance.json). The generated all-prerequisite crosswalk
is [`muhurtam-rule-crosswalk.json`](muhurtam-rule-crosswalk.json), and the
shared Python/TypeScript behavior oracle is
`tests/fixtures/election_chart_annaprasana_oracle.json`. That oracle combines
synthetic clause-isolation cases with two frozen DashaFlow 1.1.0/Lahiri
geographic projections: Hyderabad on 2026-01-15 and Sydney on 2026-05-28,
retrieved on 2026-08-30. Both language implementations also recompute and
assert every Whole Sign house from the returned Rasi and the recorded local
Lagna rather than trusting a sidecar house number.
