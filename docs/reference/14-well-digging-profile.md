# Well-digging source profile

## Authority and scope

The configured election profile is based on B. V. Raman, *Muhurtha
(Electional Astrology)*, Chapter XII, “Digging Wells,” internal printed page 52
(physical PDF page 56) in the inspected 2020 Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

Raman is a modern synthesis and secondary authority, not a primary scripture.
The profile selects a time to begin digging; it does not perform hydrology,
site divination, engineering assessment, or water-safety certification.

## Rule-to-code crosswalk

| Source statement | Locator | Implementation | Treatment |
|---|---|---|---|
| Revati, Uttara Bhadrapada, Hasta, Anuradha, Magha, Shravana, Rohini and Pushya are favourable | internal printed p. 52 (physical PDF p. 56) | `allowed_nakshatras` | The active slot-time Nakshatra must be one of the eight named values. |
| Rising Rasi should be Meena, Karkataka or Makara | internal printed p. 52 (physical PDF p. 56) | `allowed_lagnas` | The active slot-time Lagna must be one of these three exact Rasis. This also excludes the specifically discouraged Kumbha and Vrisabha. |
| Beginning in the Rasi occupied by Surya causes delay from hard rock | internal printed p. 52 (physical PDF p. 56) | `caution_lagna_solar` | When Lagna and Surya's Rasi coincide, the result carries the source caution. It is not converted into an invented score or absolute rejection. |
| Shukra and Chandra should occupy Kendras | internal printed p. 52 (physical PDF p. 56) | `manual_checks` | Disclosed for practitioner review; the finder does not yet validate complete election-chart house occupancy. |
| Abundant sweet water when Chandra or Shukra is in a Kendra identical with a full watery Rasi | internal printed p. 52 (physical PDF p. 56) | `manual_checks` | Preserved as a source condition, not presented as a hydrological prediction or automated guarantee. |

## Product contract and limitations

This replaces the former generic “Adho Nakshatra Mukha +1” proxy for well
digging. Python, MCP, and browser now use one generated activity contract;
the browser selector exposes the activity directly. Every surviving result
states its admitted Lagna and repeats the manual chart checks. MCP exposes the
stable `muhurta.well_digging` provenance identifier and the same constraints.

Hard inauspicious windows, choghadiya contribution, Tarabalam, Chandrabalam,
Panchaka and relative tiers are shared project rules. This citation does not
establish them. Geological suitability, lawful permits, structural safety and
water potability require qualified local professionals.
