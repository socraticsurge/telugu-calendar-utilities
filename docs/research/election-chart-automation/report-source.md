# Election-chart automation research record

Status: active program record

Parent epic: [#248](https://github.com/socraticsurge/telugu-calendar-utilities/issues/248)

First event story: [#255](https://github.com/socraticsurge/telugu-calendar-utilities/issues/255)
Branch: `codex/gold-assessor-release-20260904`

## Research question

How can every disclosed Muhurtam election-chart clause be converted into a
reproducible, explainable assessor without changing the frozen Panchangam
engines or presenting an interpretation choice as textual authority?

The working answer is a five-layer contract:

1. retain the event-specific source wording and locator;
2. name and version every interpretation convention needed to make it
   computable;
3. derive only the astronomical facts required by that convention;
4. apply a separately disclosed product decision for reject, qualify, prefer,
   or unknown outcomes; and
5. retain practitioner review only for a genuinely unresolved source clause,
   missing fact, unsupported system, or boundary uncertainty.

## Pre-Gold program baseline (captured 2026-08-29)

At this pre-Gold snapshot, the browser exposed 29 named events, excluding the
generic `any` search. Twenty-seven had at least one disclosed election-chart
clause. The contract then contained 23 deterministic predicates across 12
events, and only Pilgrimage had no event-clause remainder. Eleven events were
partially automated and 15 chart-bearing events had no assessor. Vehicle
acquisition and Homahuti/Yajna have no chart clause in their currently
registered source and must be closed only after a source-audited
`not-applicable` decision.

This dated baseline motivated the six shared-foundation stories and all 29
event stories, which are native sub-issues of #248. Work proceeds one event per
branch and review unit. Gold /
Jewelry is first because its visible manual-review state caused the current
product concern and because it establishes reusable placement, Navamsa,
aspect, evidence, and qualification semantics.

## Source register for Gold / Jewelry v1

| ID | Source and exact locator | Role in the computation |
|---|---|---|
| `BVR-MUHURTHA-1993`; `BVR-MUHURTHA-CHISTABO-2020` | B. V. Raman, *Muhurtha (Electional Astrology)*, Chapter X, “Buying Jewelry,” as inspected in the 2020 Chistabo derivative at internal printed p. 45 (physical PDF p. 49). The 181-page 1993 UBS bibliographic record and the 78-page inspected derivative are distinct; an exact edition match is not claimed. The same passage is inspectable in a [separate public mirror, physical PDF pp. 68–69](https://lakshminarayanlenasia.com/articles/Muhurtha-Electional-Astrology.pdf). | Event clause: Surya and Chandra should be well situated and aspected; unfavorable lunar days and asterisms should be avoided. |
| `PD-SASTRI-1950-2E` | Mantreswara, *Phaladeepika*, V. Subrahmanya Sastri translation, 2nd ed. (1950), [Internet Archive item](https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri). Chapter II, sloka 36, book p. 23 / scan p. 60; Chapter I, sloka 6; Chapter II, slokas 21–22. | Defines a planet as badly placed when `mudha`/overpowered by solar rays, debilitated in Rasi or Amsa, in an enemy sign, or in houses 6, 8, or 12; the additional passages supply Rasi lords, fall signs, and natural relationships. |
| `PD-SASTRI-1950-2E` | Chapter II, sloka 23, book p. 18 / scan p. 55, transcribed on the [chapter page](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621574.html). | Defines full Graha Drishti: every classical graha fully aspects the 7th; Shani also the 3rd and 10th, Guru the 5th and 9th, and Kuja the 4th and 8th. |
| `BPHS-ELS-6.12` | *Brihat Parashara Hora Shastra*, Chapter 6, verse 12, [Sanskrit, transliteration, word analysis, and English translation](https://enjoylearningsanskrit.com/scriptures/parashara/chapter-6/verse-12/). | Defines the first Navamsa: the Rasi itself for movable signs, the ninth from it for fixed signs, and the fifth from it for dual signs. |
| `SS-BURGESS-GANGOOLY-1935` | *Surya-Siddhanta*, Burgess translation revised by Phanindralal Gangooly (1935), Chapter X, “Moon's Rising and Setting,” verse 1, printed p. 262 / [scan p. 315](https://classicalastrologer.com/wp-content/uploads/2018/04/surya_siddhanta_english.pdf). | Historical rationale for a 12-degree lunar visibility boundary. The commentary identifies the measure as `kalamsa`, or time-degrees in oblique ascension, so v1 does not misrepresent it as an exact shortest-ecliptic-longitude formula. |
| Product policy | `gold-phaladeepika-placement-full-drishti-v1` | Selects full aspects only, excludes Rahu/Ketu as aspectors, treats “aspected” literally rather than silently changing it to “benefically aspected,” and caps a candidate below Excellent when a required positive chart condition is not met. |

The existing registry ID `PD-SASTRI-1942` points to the same public
transcription but labels the edition as 1942. The linked scan identifies
itself as the second edition of 1950. This work therefore registers the
edition-correct `PD-SASTRI-1950-2E` identifier additively instead of silently
reusing the inaccurate year.

## Claim-to-formula ledger

| Claim | Source boundary | Versioned operational formula | Product treatment |
|---|---|---|---|
| Surya is well situated | Raman supplies the event clause; Phaladeepika 2.36 supplies the selected definition. | Surya must be outside Whole Sign houses 6, 8, and 12; outside Rashis owned by its natural enemies Shukra and Shani (Vrishabha, Tula, Makara, Kumbha); outside debilitation Rasi Tula; and outside debilitation Navamsa Tula. Solar-ray overpowering is inapplicable to Surya itself. | `qualify`: failure retains the slot but caps an otherwise Excellent tier to Good. |
| Chandra is well situated | Same boundary. | Chandra must be outside Whole Sign houses 6, 8, and 12; outside debilitation Rasi and Navamsa Vrischika; and more than 12° from Surya under the disclosed v1 solar-clearance convention. V1 selects natural sign-lord enmity from Phaladeepika 2.21–22; that table gives Chandra friends and neutrals but no natural enemy, so this convention adds no enemy-owned-Rasi exclusion. | `qualify`. |
| Surya is aspected | Raman says “aspected,” not “benefically aspected.” Phaladeepika 2.23 supplies the selected aspect geometry. | At least one of Chandra, Kuja, Budha, Guru, Shukra, or Shani must cast a full whole-sign Graha Drishti to Surya. Rahu/Ketu, partial aspects, degree orbs, and self-aspect do not count in v1. | `qualify`. |
| Chandra is aspected | Same boundary. | At least one of Surya, Kuja, Budha, Guru, Shukra, or Shani must cast a full whole-sign Graha Drishti to Chandra under the same table. | `qualify`. |

For zero-based Rasi indexes, let

```text
D(source, target) = (R(target) - R(source) + 12) mod 12

full_offsets(Surya, Chandra, Budha, Shukra) = {6}
full_offsets(Kuja)                         = {3, 6, 7}
full_offsets(Guru)                         = {4, 6, 8}
full_offsets(Shani)                        = {2, 6, 9}

full_aspect(source, target) =
    D(source, target) is in full_offsets(source)
```

Planetary Navamsa is derived from absolute sidereal longitude. Each Rasi is
split into nine parts of 3°20′. The first Navamsa starts from the same Rasi for
movable signs, the ninth Rasi from the natal Rasi for fixed signs, and the
fifth Rasi from the natal Rasi for dual signs. Because the chart contract
rounds degrees within Rasi to 0.01°, a value
within 0.01° of a Navamsa boundary is `unknown`, never guessed across the
boundary.

The 12° Chandra threshold is a product interpretation of solar-ray clearance.
Surya-Siddhanta X.1 gives a 12-degree lunar visibility boundary, but the
translator's commentary identifies those units as time-degrees in oblique
ascension. V1 therefore uses 12° of shortest ecliptic elongation only as a
disclosed approximation. With two-decimal planetary degrees, separations
within 0.02° of that threshold are `unknown`. The implementation does not
present this as a numeric formula stated by Phaladeepika 2.36 or an exact
restatement of Surya-Siddhanta X.1.

## Why v1 does not classify the aspect as benefic or malefic

Raman uses more specific wording elsewhere in the same work when he intends a
“good aspect,” a “benefic aspect,” or freedom from a malefic aspect. The
jewelry sentence says only “aspected.” Turning that into “benefically aspected
and free from every malefic aspect” would add an unsupported requirement and
would force another convention for waxing Chandra, afflicted Budha, nodes,
and mixed aspects. Version 1 therefore computes the literal minimum claim and
shows the aspecting graha names as evidence. A future lineage mode may add a
separately sourced aspect-quality policy; it must not silently change v1.

## Outcome and aggregation semantics

`Reject` remains reserved for a source prohibition whose failure removes a
candidate. `Prefer` remains tie-break evidence and never changes the raw
Panchangam score. The new `Qualify` effect represents a positive source
condition central to the event: every sampled state must pass for an
Excellent label; a resolved failure retains the candidate and caps it below
Excellent. This avoids both arbitrary hard rejection and the misleading
result of calling an unmet source condition Excellent.

For a `qualify` rule across a displayed window:

```text
fail in any sample                    -> fail
otherwise, unknown in any sample      -> unknown
otherwise                             -> pass
```

A known failure therefore cannot be masked by an unrelated unknown fact.

A pass/fail change marks the window unstable. Missing or malformed chart
facts, a Navamsa rounding boundary, unavailable projection, a selected
non-Drik system, or the existing local-Lagna transition guard fails closed.
Only those unresolved cases retain review language. A fully resolved pass or
fail is an automated assessment, not a practitioner remainder.

## Assurance boundary

The v1 calculation uses the DashaFlow response only for the nine grahas’
Rashis and rounded degrees. Whole Sign houses are recomputed in the browser’s
validated local Drik/Lahiri Lagna frame. The sidecar Lagna degree is not used
as if it belonged to that local frame.

The displayed window is assessed at its start, final represented minute,
10-minute cadence points, and both sides of each known interior local Lagna
transition. Gold additionally applies the registered
`election_chart.gold_transition_envelope_v1` contract between every adjacent
pair. NASA's published maximum lunar orbital velocity and perigee distance
convert to 14.66°/day; v1 deliberately widens that to 24°/day for one
classical graha and 48°/day for a two-graha separation. Rounded endpoints are
expanded by that envelope. An excessive gap or displacement, or a possible
unrepresented Rasi, Navamsa, full-aspect, or 12° solar-clearance transition,
fails closed to `unknown`. When endpoint states differ, both sides are
evaluated; a sampled known failure dominates an unrelated unknown for the
same qualification rule. The full derivation, rounding terms, and limitations
are recorded in the Gold computation profile.

This completes Gold's disclosed election-chart clause under the named v1
convention. It does not turn the separate “usual unfavorable lunar days and
asterisms” wording into a jewelry-specific list; the existing Gold
Panchangam-ranking inputs retain their disclosed project-heuristic status.
This is not an empirical claim that electional astrology predicts purchase
outcomes, and it does not replace legal, financial, safety, consent, medical,
or ritual judgment.

## External calculation cross-check

On 2026-08-30, the DashaFlow 1.1.0 projection was compared with Drik
Panchang's sidereal planetary-position pages at three shared UTC instants in
Hyderabad and Sydney. The six interior fixtures cover Sydney in and out of
daylight-saving time.

| UTC instant | Hyderabad Drik / DashaFlow Lagna | Sydney Drik / DashaFlow Lagna |
|---|---|---|
| 2026-01-15 04:00 | Kumbha 14.911° / 14.69° | Mesha 22.720° / 22.39° |
| 2026-05-28 04:00 | Karka 4.694° / 4.54° | Kanya 16.999° / 16.38° |
| 2026-08-27 08:18 | Vrischika 27.540° / 27.38° | Kumbha 20.342° / 20.01° |

The source pages remain directly inspectable: Hyderabad
[January](https://www.drikpanchang.com/planet/position/planetary-positions-sidereal.html?geoname-id=1269843&date=15%2F01%2F2026&time=09%3A30%3A00&lang=en),
[May](https://www.drikpanchang.com/planet/position/planetary-positions-sidereal.html?geoname-id=1269843&date=28%2F05%2F2026&time=09%3A30%3A00&lang=en), and
[August](https://www.drikpanchang.com/planet/position/planetary-positions-sidereal.html?geoname-id=1269843&date=27%2F08%2F2026&time=13%3A48%3A00&lang=en);
Sydney
[January](https://www.drikpanchang.com/planet/position/planetary-positions-sidereal.html?geoname-id=2147714&date=15%2F01%2F2026&time=15%3A00%3A00&lang=en),
[May](https://www.drikpanchang.com/planet/position/planetary-positions-sidereal.html?geoname-id=2147714&date=28%2F05%2F2026&time=14%3A00%3A00&lang=en), and
[August](https://www.drikpanchang.com/planet/position/planetary-positions-sidereal.html?geoname-id=2147714&date=27%2F08%2F2026&time=18%3A18%3A00&lang=en).

Across all six fixtures, all nine graha Rashis matched and graha longitudes
matched within 0.01°. Whole Sign houses therefore matched when derived from
the same interior Lagna sign. The Lagna sign also matched at those interior
instants, but the Lagna degree differed by 0.15° to 0.62°.

Two transition-minute probes make the assurance boundary concrete:

- Hyderabad, 2026-01-15 10:19 local: Drik reports Meena 00°11′45″ while
  DashaFlow reports Kumbha 29.98°.
- Sydney, 2026-05-28 14:35 local: Drik reports Tula 00°03′45″ while DashaFlow
  reports Kanya 29.48°.

The application consequently projects houses in its validated local
Drik/Lahiri Lagna sign and keeps the five-minute transition guard. This is a
calculation-convention uncertainty, not an unimplemented Gold clause. The
synthetic shared Python/TypeScript oracle at
`tests/fixtures/election_chart_gold_oracle.json` covers pass, qualification
failure, unknown, ordinary and special aspects, exclusions, and Navamsa
boundaries.
Separately,
`tests/fixtures/election_chart_gold_gateway_oracle.json` freezes unedited HTTP
200 result cells from Astro revision
`4106f09708a154f1c2401880ebe8f9c0b9162eb5` and DashaFlow revision
`c84fd856b17120c80e1bb7e455246a0ec8e429ea`. Its Hyderabad and Sydney cases
span two dates and collectively cover pass, fail, unknown, conflict and
boundary Gold outcomes; each case must retain all nine unique grahas and Whole
Sign house consistency. These are actual deterministic gateway outputs, not
synthetic labels and not an additional independent ephemeris comparison. The
built browser matrix covers Gold pass, cap, and review dispositions at 390×844
and 1440×900.

The shared public calculation path is active independently of this frontend
feature release. On 2026-09-04, Astro production revision `4106f097` and
DashaFlow production revision `c84fd856` returned HTTP 200 for the synthetic
election-chart probe through the public guest gateway. DashaFlow issue
[#443](https://github.com/socraticsurge/telugu-calendar-utilities/issues/443)
is closed with the producer cross-field invariants released. The Gold UI and
predicate contract still require their own normal TCU review and release;
backend availability is not evidence that this branch is already public.

## Gold v1 oracle

The canonical test matrix must prove:

- all four rules pass with both luminaries outside houses 6/8/12, outside
  their Rasi/Navamsa debility, and each receiving a full aspect;
- each placement exclusion fails independently;
- Rasi and Navamsa debility fail independently;
- Surya enemy-Rasi placement fails while Chandra receives no invented
  enemy-Rasi exclusion;
- ordinary seventh aspects and Kuja/Guru/Shani special full aspects are
  recognized, while conjunctions, partial aspects, nodes, and self-aspects are
  not;
- a Navamsa boundary and an incomplete nine-graha payload return `unknown`;
- an interior failure cannot hide behind passing endpoints;
- resolved qualification failure caps Excellent to Good without calling it
  practitioner review;
- Gold requests the exact chart service and has an empty chart remainder;
- the result and shared text do not claim that only a subset was computed;
- frozen, unedited gateway cells cover pass, fail, unknown, conflict and
  boundary outcomes across Hyderabad and Sydney and at least two dates;
- Python and TypeScript produce the same status, effect, evidence, and
  convention metadata for the golden fixtures.

## Next event sequence

After Gold passes owner review, the next bounded stories are Annaprasana,
Karnavedha, Vidyarambha, completed-house purchase, general purchase,
well-digging, and business investment. They reuse placement, grouped-planet,
benefic/malefic, and composition primitives before the program advances to
lordship, Navamsa-Lagna, compatibility, named-Yoga, and medical-context work.
