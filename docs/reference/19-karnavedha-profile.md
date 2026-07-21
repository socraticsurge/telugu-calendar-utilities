# Karnavedha source profile

## Authority and scope

The configured ear-piercing profile is based on B. V. Raman,
*Muhurtha (Electional Astrology)*, Chapter VIII, “Post-natal ceremonies” /
“Ear boring (Karnavedha),” printed page 22 (PDF page 26). Its reference to
Tithis “usually declared as inauspicious” is resolved through Chapter V's
general Panchanga Suddhi list, printed page 11 (PDF page 15):

<https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf>

Raman is a modern synthesis and secondary authority, not primary scripture.
The profile screens electional time; medical safety, consent, sterile technique
and aftercare remain matters for qualified practitioners and guardians.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Perform on the 12th or 16th day after birth, or in the 6th, 7th or 8th month | `manual_checks` | Child age is not an input and is disclosed on every candidate. |
| Use forenoon or afternoon, never night | `daytime_only` | `night_slots` returns no candidates even when MCP requests `include_night`. The website is already daytime-only. |
| Reject a day ruled by two Nakshatras or two Tithis | `manual_checks` | The relevant ceremony interval is not supplied, so transition counting is not inferred. |
| Reject generally inauspicious Tithis | `avoid_tithi_numbers` | Cross-referenced to Chapter V: 4th, 6th, 8th, 12th, 14th, Purnima and Amavasya; both terminal Tithis map to 15. |
| Monday, Wednesday, Thursday and Friday are good | `allowed_varas` | Other weekdays reject the day. |
| Reject Kumbha, Simha and Vrischika rising | `allowed_lagnas` | The other nine Rasis are admitted at slot time. |
| Leave the 8th house unoccupied | `manual_checks` | Full election-chart occupancy remains practitioner-reviewed. |

## Product contract and limitations

The existing samskara exclusions, hard avoid windows, Tithi-family ranking,
personal scoring and relative tiers remain shared project rules not established
by this citation. MCP exposes `muhurta.karnavedha`, the daytime-only constraint
and every manual check; the browser receives the same generated contract.
