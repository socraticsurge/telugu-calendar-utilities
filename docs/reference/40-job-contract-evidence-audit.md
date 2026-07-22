# Service-entry Source Profile

## Scope and authority

The `job` compatibility key now means the employee-side act of **entering
employment / starting service**. It does not cover offer acceptance, signing a
modern employment or commercial contract, incorporation, or hiring staff.

The verified claim `muhurta.service_entry` uses Rama Daivajna, *Muhurta
Chintamani*, undated Sanskrit text with Hindi commentary,
Nakshatra-prakarana, “Entering the service of a master,” verse 26, printed page
38 (Internet Archive OCR lines 2565–2577).

## Exact crosswalk

| Source criterion | Implementation | Boundary |
|---|---|---|
| Ashwini, Pushya, Hasta, Chitra, Anuradha, Mrigashira and Revati | Exact `allowed_nakshatras` | Hard day gate |
| Wednesday, Friday, Sunday and Thursday | Exact `allowed_varas` | Hard day gate |
| Benefic in Lagna | Manual check | Mandatory chart review |
| Surya or Mangala in the 10th or 11th | Manual check | Mandatory chart review |
| Employer/employee Yoni friendship | Manual check | Requires both birth Nakshatras |
| Friendship between both Janma-Rasi lords | Manual check | Requires both natal Rasis |

`manual_prerequisites = true` caps results below Excellent until the chart and
two-person compatibility checks are complete. The former Amrit Choghadiya,
Nanda Tithi and Sthira-Lagna proxies have been removed.

The separately inspected Sandhana verse concerns peace, alliance or friendship
and is not treated as authority for a modern contract. Employment terms,
labour law, compensation, benefits and workplace safety take precedence.
