# Land-purchase source profile

## Authority and corrected scope

The activity key remains `property` for API compatibility, but its user-facing
label is now **Land purchase (for building)**. B. V. Raman treats buying land
for building and buying a completed house as separate elections with different
criteria. One generic “Property / Land purchase” profile would therefore make
an authority claim broader than its evidence.

This profile uses B. V. Raman, *Muhurtha (Electional Astrology)*, Chapter XII,
“Buying Lands for Buildings,” internal printed page 54 (physical PDF page 58) in the inspected 2020 Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

Raman is a modern synthesis and secondary authority, not primary scripture.

## Rule-to-code crosswalk

| Source statement | Locator | Implementation | Treatment |
|---|---|---|---|
| Fourteen named asterisms are best for buying land | internal printed p. 54 (physical PDF p. 58) | `allowed_nakshatras` | The active slot-time Nakshatra must be one of the fourteen names. |
| Rikta Tithis must be scrupulously avoided | internal printed p. 54 (physical PDF p. 58) | `avoid_tithi_numbers: [4, 9, 14]` | Both Pakshas are handled by active Tithi number; Rikta slots are rejected rather than merely down-ranked. |
| Monday, Wednesday, Thursday and Saturday are good | internal printed p. 54 (physical PDF p. 58) | `allowed_varas`; `prefer_vara` | Only those four sunrise weekdays are admitted and the match remains visible in the score explanation. |
| Tuesday is recommended by some writers, but Raman rejects it | internal printed p. 54 (physical PDF p. 58) | `allowed_varas` | Tuesday is outside the admitted list. The implementation does not erase the textual disagreement; it records that this is Raman's configured profile. |
| At final negotiations, preferably use a fixed rising Rasi | internal printed p. 54 (physical PDF p. 58) | `prefer_lagna_class: Sthira` | Fixed Lagna receives the disclosed activity bonus; it is a preference, not a hard gate. |
| Guru in Kendra/Trikona; Mangala in 11th and not Lagna | internal printed p. 54 (physical PDF p. 58) | `ELECTION_CHART_RULES[property]` | The Drik browser post-screen counts the first two as preferences only across every sampled state and rejects Mangala in Lagna at any sample (edges and both sides of known interior Lagna transitions). |
| Weekday lord in Lagna; harmonious Lagna/7th lords; avoid 11th lord in 12th | internal printed p. 54 (physical PDF p. 58) | `manual_checks` | Lordship and relationship judgment remain for practitioner review. |

## Product contract and limitations

Python, MCP, and browser consume the same generated activity profile. MCP
exposes the stable `muhurta.land_purchase.building` claim identifier and keeps
the complete chart wording in `manual_checks`. The Drik browser adds the
bounded chart post-screen above; it does not make Python/MCP chart-aware. See
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).

This profile must not be presented as an election for buying a completed
house. Raman gives that a separate Nanda-Tithi, Thursday/Friday and Nakshatra
profile. Adding that as its own activity requires a separate reviewed feature.
Legal due diligence, title verification, valuation, financing, soil testing
and structural advice remain professional—not astrological—requirements.
