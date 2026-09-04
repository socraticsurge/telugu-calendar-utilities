# Bhumi Puja / house-foundation source profile

## Authority and scope

The configured profile is for laying the foundation of a house. It is based
on B. V. Raman, *Muhurtha (Electional Astrology)*, Chapter XII, “House
Building” / “Laying the Foundation,” internal printed pages 50–51 (physical PDF pages 54–55) in the inspected 2020 Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

Raman is a modern synthesis and secondary authority, not a primary scripture.
The product label “Bhumi Puja / Foundation laying” is broader than Raman's
heading; this profile elects the foundation-laying moment and does not claim
to prescribe the complete Puja paddhati.

## Rule-to-code crosswalk

| Source statement | Locator | Implementation | Treatment |
|---|---|---|---|
| Chaitra, Vaishakha, Shravana, Kartika and Magha are best; the other seven named months are rejected | internal printed pp. 50–51 (physical PDF pp. 54–55) | `allowed_maasams` | Only the five stated months are admitted. `Adhika`/`Nija` prefixes are normalized before comparison. |
| Surya should occupy a fixed Rasi or at least a movable Rasi; common Rasis are rejected | internal printed pp. 50–51 (physical PDF pp. 54–55) | `allowed_solar_classes` | Fixed and movable solar-sign classes are admitted; common signs reject the day. |
| Eight Nakshatras are best, seven ordinary/middling, and the remaining twelve rejected | internal printed pp. 50–51 (physical PDF pp. 54–55) | `allowed_nakshatras`; `prefer_nakshatras` | Best and middling groups survive; only the best group receives the disclosed +1 distinction. |
| All odd Tithis except the 9th; among even Tithis, 2nd, 6th and 10th | internal printed pp. 50–51 (physical PDF pp. 54–55) | `allowed_tithi_numbers` | The active slot-time Tithi number must be one of 1, 2, 3, 5, 6, 7, 10, 11, 13 or 15. |
| Monday, Wednesday, Thursday and Friday are best; waning-Moon Monday rejected | internal printed pp. 50–51 (physical PDF pp. 54–55) | `allowed_varas`; `avoid_vara_paksha` | Only the four stated best weekdays are automated; Krishna-Paksha Monday is then explicitly rejected. |
| Fixed rising Rasi is best; movable rejected; common possible only with strong benefics | internal printed pp. 50–51 (physical PDF pp. 54–55) | `required_lagna_class: Sthira` | Conservative automation requires a fixed Lagna because the exceptional benefic-strength condition is not fully computed. |
| Malefics in 3/6/11, benefics in Kendras/Trikonas; 8th vacant and without malefic aspect | internal printed pp. 50–51 (physical PDF pp. 54–55) | `manual_checks` | Disclosed for practitioner review; the finder does not claim full election-chart validation. |
| First foundation stone at the north-eastern corner after Puja | internal printed pp. 50–51 (physical PDF pp. 54–55) | `manual_checks` | Ritual/site instruction only; never inferred from astronomical data. |

## Product contract and limitations

Python, MCP, and browser consume one activity-rule contract. Day-level source
failures are explained; active slot-time Tithi, Nakshatra and Lagna gates are
applied after day admission. Every result repeats the manual checks, and MCP
exposes the stable `muhurta.bhumi_puja.foundation` provenance identifier.

The existing samskara-yoga exclusion, hard inauspicious windows, Panchaka,
Tarabalam, Chandrabalam, choghadiya contribution and relative tiers are shared
project rules. This Chapter XII citation does not establish them. A surviving
candidate is therefore a screened foundation-laying time, not a complete
Vastu or ritual certification.
