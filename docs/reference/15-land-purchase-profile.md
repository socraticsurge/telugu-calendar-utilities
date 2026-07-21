# Land-purchase source profile

## Authority and corrected scope

The activity key remains `property` for API compatibility, but its user-facing
label is now **Land purchase (for building)**. B. V. Raman treats buying land
for building and buying a completed house as separate elections with different
criteria. One generic “Property / Land purchase” profile would therefore make
an authority claim broader than its evidence.

This profile uses B. V. Raman, *Muhurtha (Electional Astrology)*, Chapter XII,
“Buying Lands for Buildings,” printed page 53 (PDF page 57):

<https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf>

Raman is a modern synthesis and secondary authority, not primary scripture.

## Rule-to-code crosswalk

| Source statement | Locator | Implementation | Treatment |
|---|---|---|---|
| Fourteen named asterisms are best for buying land | p. 53 (PDF 57) | `allowed_nakshatras` | The active slot-time Nakshatra must be one of the fourteen names. |
| Rikta Tithis must be scrupulously avoided | p. 53 (PDF 57) | `avoid_tithi_numbers: [4, 9, 14]` | Both Pakshas are handled by active Tithi number; Rikta slots are rejected rather than merely down-ranked. |
| Monday, Wednesday, Thursday and Saturday are good | p. 53 (PDF 57) | `allowed_varas`; `prefer_vara` | Only those four sunrise weekdays are admitted and the match remains visible in the score explanation. |
| Tuesday is recommended by some writers, but Raman rejects it | p. 53 (PDF 57) | `allowed_varas` | Tuesday is outside the admitted list. The implementation does not erase the textual disagreement; it records that this is Raman's configured profile. |
| At final negotiations, preferably use a fixed rising Rasi | p. 53 (PDF 57) | `prefer_lagna_class: Sthira` | Fixed Lagna receives the disclosed activity bonus; it is a preference, not a hard gate. |
| Weekday lord in Lagna; Guru in Kendra/Trikona; Mangala in 11th and not Lagna; harmonious Lagna/7th lords; avoid 11th lord in 12th | p. 53 (PDF 57) | `manual_checks` | Preserved for practitioner review; the finder does not claim complete election-chart validation. |

## Product contract and limitations

Python, MCP, and browser consume the same generated profile. MCP exposes the
stable `muhurta.land_purchase.building` claim identifier. Every surviving
slot repeats the full election-chart checks that are not automated.

This profile must not be presented as an election for buying a completed
house. Raman gives that a separate Nanda-Tithi, Thursday/Friday and Nakshatra
profile. Adding that as its own activity requires a separate reviewed feature.
Legal due diligence, title verification, valuation, financing, soil testing
and structural advice remain professional—not astrological—requirements.
