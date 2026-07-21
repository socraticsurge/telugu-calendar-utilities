# Namakarana source profile

## Authority and scope

The configured naming-ceremony profile is based on B. V. Raman,
*Muhurtha (Electional Astrology)*, Chapter VIII, “Post-natal ceremonies” /
“Naming the child (Namakarana),” printed page 21 (PDF page 25):

<https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf>

Raman is a modern synthesis and secondary authority, not primary scripture.
The source describes an election for the ceremony; it does not replace family,
sampradaya or priestly rules for choosing the name itself.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Prefer the 10th, 12th or 16th day after birth; otherwise elect an auspicious day | `manual_checks` | The finder has no birth-date input, so it discloses rather than fabricates this check. |
| Sixteen named Nakshatras are auspicious | `allowed_nakshatras` | Any other active slot-time Nakshatra rejects the candidate. |
| Reject Tithis 4, 6, 8, 9, 12, 14, Purnima and Amavasya | `avoid_tithi_numbers` | The engine numbers Tithis 1–15 within each Paksha, so both Purnima and Amavasya map to terminal number 15. |
| Monday, Wednesday, Thursday and Friday are good; other weekdays are not | `allowed_varas` | An unlisted weekday rejects the entire day with an explicit reason. |
| Fixed Lagnas are preferable; common Lagnas are good with benefic occupancy | `prefer_lagna_class`; `manual_checks` | Fixed Lagna receives the existing disclosed preference; the exceptional chart condition remains manual. |
| Strengthen Lagna, leave the 8th vacant, and consider the stated Guru/malefic/Shukra/Chandra placements | `manual_checks` | Full election-chart occupancy, dignity and aspect judgment is not claimed by the finder. |
| The name should suit the ruling Nakshatra | `manual_checks` | Naming guidance is visible but not generated automatically. |

## Product contract and limitations

The existing samskara filters, hard avoid windows, Shubh-Choghadiya and
Tithi-family ranking preferences, personal scoring and relative tiers are
shared project rules. This Chapter VIII locator does not establish them. MCP
returns the stable `muhurta.namakarana` claim and repeats every manual check;
the browser consumes the same generated activity contract.
