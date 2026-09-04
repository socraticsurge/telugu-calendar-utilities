# Vehicle-acquisition source profile

## Authority and scope

The vehicle-purchase profile uses B. V. Raman, *Muhurtha (Electional
Astrology)*, Chapter IV, “Influence of Nakshatras,” movable-Nakshatra
classification, internal printed page 11 (physical PDF page 14) in the inspected 2020
Chistabo derivative:

[inspected 2020 Chistabo derivative](https://www.panchanga.lv/wp-content/uploads/2020/06/Muhurta_Raman.pdf)

Raman is a modern synthesis and secondary authority, not primary scripture.
The cited passage says that Shravana, Dhanishtha, Shatabhisha, Punarvasu and
Swati are auspicious for acquiring vehicles. It does not provide a complete
vehicle-purchase election in that passage.

## Rule-to-code crosswalk

| Source statement | Implementation | Treatment |
|---|---|---|
| Five movable Nakshatras are auspicious for acquiring vehicles | `prefer_nakshatras` | These stars receive a disclosed +1 activity-specific preference. The passage does not state that every other star must be rejected. |

## Product contract and limitations

The existing Labh-Choghadiya, Bhadra-Tithi, Friday and fixed-Lagna preferences
are transparent project-ranking rules. They are not supported by this Chapter
IV locator and do not inherit its verified status. The claim therefore verifies
the activity-specific Nakshatra preference—not a universal or complete vehicle
election. MCP returns `muhurta.vehicle.acquisition`; the browser consumes the
same generated preference list.
