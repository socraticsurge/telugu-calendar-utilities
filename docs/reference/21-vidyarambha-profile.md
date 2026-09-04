# Vidyarambha / Aksharabhyasa source profile

## Authority and scope

The education-commencement profile is based on B. V. Raman, *Muhurtha
(Electional Astrology)*, Chapter VIII, “Post-natal ceremonies” / “Commencing
education (Aksharabhyasa),” internal printed page 23 (physical PDF page 26) in the inspected 2020
Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

Raman is a modern synthesis and secondary authority, not primary scripture.
This is an election for formal commencement; it neither limits when children
may learn nor replaces educational, developmental or family judgment.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Most propitious marker: 5th day, 5th month, 5th year | `manual_checks` | Child age is not a finder input and remains explicit. |
| Monday, Wednesday, Thursday and Friday are good | `allowed_varas` | Other weekdays reject the day. |
| Eight named Nakshatras are good | `allowed_nakshatras` | An unlisted active slot-time Nakshatra rejects the candidate. |
| Movable and common Rasis are good | `allowed_lagnas` | The four Chara and four Dvisvabhava Rasis form the slot-time allow-list. |
| Prefer forenoon and noon | `manual_checks` | This is a preference, not an absolute prohibition; it is disclosed rather than converted into the hard Mundana cutoff. |
| Leave the 8th vacant; Budha, Shukra and Guru in the 9th counteract adverse influences | `manual_checks` | Full election-chart occupancy remains practitioner-reviewed. |

## Product contract and limitations

Shared samskara exclusions, hard avoid windows, Amrit-Choghadiya and
Tithi-family ranking preferences, personal scoring and relative tiers are not
established by this citation. MCP exposes `muhurta.vidyarambha` and every
manual requirement; the browser consumes the same generated activity rules.
