# Annaprasana source profile

## Authority and scope

The configured first-feeding profile is based on B. V. Raman,
*Muhurtha (Electional Astrology)*, Chapter VIII, “Post-natal ceremonies” /
“First feeding on rice (Annaprasana),” printed pages 21–22 (PDF pages 25–26).
Its “usual unfavorable Tithis” reference is resolved through the same book's
general Panchanga Suddhi list in Chapter V, printed page 11 (PDF page 15):

<https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf>

Raman is a modern synthesis and secondary authority, not primary scripture.
The election supplements rather than replaces pediatric feeding guidance and
the family's ritual tradition.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Perform in the 6th, 8th, 9th or 12th month; month is most important | `manual_checks` | Child age is not an input, so every result discloses this prerequisite. |
| Twelve named Nakshatras are admitted; seven others explicitly rejected | `allowed_nakshatras` | Conservative allow-list; unlisted active slot-time Nakshatras reject the candidate. |
| Avoid usual unfavorable Tithis | `avoid_tithi_numbers` | Cross-referenced to Chapter V's 4th, 6th, 8th, 12th, 14th, Purnima and Amavasya list; terminal days both map to 15. |
| Monday, Wednesday, Thursday and Friday are good | `allowed_varas` | Other weekdays reject the day with an explicit reason. |
| Mesha, Vrischika and Meena rising are inauspicious | `allowed_lagnas` | The other nine Rasis form the conservative slot-time allow-list. |
| Leave the 10th vacant; specified Budha/Mangala/Shukra placements; benefic Lagna and no malefic there | `manual_checks` | Full election-chart occupancy and benefic/malefic judgment remain practitioner checks. |

## Product contract and limitations

The existing samskara filters, hard avoid windows, Shubh-Choghadiya and
Tithi-family ranking preferences, personal scoring and relative tiers are
shared project rules and are not established by this locator. MCP exposes the
stable `muhurta.annaprasana` claim and all manual checks; the browser consumes
the same generated contract.
