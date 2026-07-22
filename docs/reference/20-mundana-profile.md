# Mundana / Chaula source profile

## Authority and scope

The first-head-shave profile is based on B. V. Raman, *Muhurtha (Electional
Astrology)*, Chapter VIII, “Post-natal ceremonies” / “Tonsure (Chowlam),”
printed pages 22–23 (PDF pages 26–27):

<https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf>

Raman is a modern synthesis and secondary authority, not primary scripture.
The election does not replace family sampradaya, priestly guidance, guardian
consent, hygiene or child-safety requirements.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Perform in the 3rd or 5th year; not while the mother is pregnant | `manual_checks` | Age and pregnancy are not finder inputs and remain explicit prerequisites. |
| Guru and Shukra free from combustion | `skip_on_combust` | A combust Guru or Shukra rejects the day using computed engine state. |
| Bright fortnight gives longevity; dark fortnight affects health | `allowed_pakshams: Shukla` | Conservative child-facing automation admits only Shukla Paksha. |
| Seven Tithis are good | `allowed_tithi_numbers` | Only 2, 3, 5, 7, 10, 11 and 13 survive at slot time. |
| Nine Nakshatras favorable and six ordinary | `allowed_nakshatras`; `prefer_nakshatras` | Both groups survive; only the favorable group receives the disclosed +1 distinction. |
| Always perform in the forenoon | `forenoon_only` | A named Muhurta survives only when its full interval ends by local solar noon; Python and browser enforce the same boundary. |
| Monday, Wednesday, Thursday and Friday are good | `allowed_varas` | Other weekdays reject the day. |
| Seven rising Rasis are good; other Rasis need benefic Lagna; reject Kumbha absolutely | `allowed_lagnas`; `manual_checks` | Conservative automation admits the seven unconditionally good Rasis; exceptional chart judgment remains manual. |
| Detailed benefic/malefic house placements and vacant 8th | `manual_checks` | Full election-chart occupancy remains practitioner-reviewed. |
| Surya in the “tropic of Karkataka” | `manual_checks` | The edition's seasonal wording is disclosed for practitioner interpretation rather than silently mapped to a possibly incorrect solar-sign gate. |

## Product contract and limitations

Shared samskara exclusions, hard avoid windows, Tithi-family ranking, personal
scoring and relative tiers are not established by this locator. MCP exposes
`muhurta.mundana`, the Paksha/forenoon gates and every manual requirement; the
browser consumes and enforces the same generated rule contract.
