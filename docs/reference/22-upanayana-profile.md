# Upanayana source profile

## Authority and scope

The sacred-thread profile is based on B. V. Raman, *Muhurtha (Electional
Astrology)*, Chapter VIII, “Post-natal ceremonies” / “Investiture of sacred
thread (Upanayanam),” internal printed pages 24–25 (physical PDF pages 27–28) in the inspected
2020 Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

Raman is a modern synthesis and secondary authority, not primary scripture.
Eligibility, age, ritual procedure and lineage-specific exceptions belong to
the family's sampradaya and officiating Acharya; the finder only screens time.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Perform in the 5th or 8th year, with later-age limits and exceptions | `manual_checks` | Age and community/lineage rules are not finder inputs. |
| Magha, Phalguna, Chaitra and Vaishakha are good | `allowed_maasams` | Other lunar months reject the day. |
| Surya's northern course, Makara through Mithuna | `allowed_solar_signs` | The exact six-Rasi allow-list rejects a day outside Uttarayana. |
| Different admitted Tithis in Shukla and Krishna Paksha | `allowed_tithi_names` | Exact Paksha-qualified names prevent a Shukla rule from leaking into Krishna Paksha. The delayed-age Chaturdashi exception remains manual. |
| Monday, Wednesday, Thursday and Friday propitious; reject Wednesday if Budha combust | `allowed_varas`; `manual_checks` | Four best weekdays are admitted; conditional combustion remains visible because the browser feed lacks a reliable slot-level Budha-combustion fact. |
| Sixteen named Nakshatras are good | `allowed_nakshatras` | Unlisted active slot-time Nakshatras reject a candidate. |
| Seven rising Rasis are good | `allowed_lagnas` | Only the seven stated Rasis survive slot-time Lagna screening. |
| Ceremony before noon | `forenoon_only` | The entire named Muhurta must end by local solar noon; night search returns none. |
| Detailed Chandra, malefic, house and Yoga conditions | `manual_checks` | Full election-chart occupancy, aspects, dignity and exceptions remain practitioner-reviewed. |

## Product contract and limitations

Shared samskara exclusions, hard avoid windows, Tithi-family ranking, personal
scoring and relative tiers are not established by this locator. MCP exposes
`muhurta.upanayana`, exact Tithi/solar-Rasi constraints and every manual check;
the browser consumes the same generated contract.
