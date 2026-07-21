# Yajna / Homam Evidence Audit

## Status

The Yajna / Homam profile is **not source-verified**. Its `audit_claim`,
`muhurta.yajna.profile_conflict`, has state `contradicted`.

## Inspected authority

- Rama Daivajna, *Muhurta Chintamani*, Sanskrit text with Hindi commentary.
- Internet Archive identifier `muhurta-chintamani-hindi`; publisher and date
  are not exposed by the scan metadata.
- Nakshatra-prakarana, “Homahuti Muhurta” and “Agnivasa,” verses 35–36.
- Printed pages 43–44; OCR lines 2773–2796.

## What the verses actually require

Verse 35 divides the 27 Nakshatras into nine consecutive groups of three,
counted from the Nakshatra occupied by Surya. The groups are assigned in order
to Surya, Budha, Shukra, Shani, Chandra, Mangala, Guru, Rahu and Ketu. The
day’s Nakshatra determines the Graha into whose “mouth” the offering falls;
an offering to a malefic group is rejected.

Verse 36 computes Agnivasa by adding one to the Tithi number, adding the
weekday number counted from Sunday, and taking the remainder modulo four.
Remainders 3 and 0 place Agni on earth and support Homa; remainder 1 places
Agni in the sky and warns of danger to life; remainder 2 places Agni below and
warns of loss of wealth.

## Criterion crosswalk

| Criterion | Current profile | Verses 35–36 | Status |
|---|---|---|---|
| Tithi | Every Purna rewarded; every Jaya penalized | Tithi participates in a weekday-dependent modulo-four result | **Direct scoring conflict** |
| Vara | Monday and Thursday preferred | Every weekday changes the Agnivasa result | Unsupported standalone preference |
| Nakshatra | No Homam-specific calculation | Three-star group counted from Surya’s Nakshatra | Missing |
| Lagna | Fixed signs preferred | No fixed-Lagna rule in these verses | Unsupported here |
| Scope | Yajna and Homam combined | Homahuti election | Broader than citation |

Both Purna and Jaya families contain combinations producing favorable and
unfavorable Agnivasa results. Family membership therefore cannot substitute
for verse 36’s joint Tithi/weekday computation.

## Correction boundary

Implementing the source exactly requires Surya’s Nakshatra at the candidate
time plus a dedicated Homahuti/Agnivasa evaluator. The current data contract
does not expose the former to this activity scorer, and existing tests preserve
the family and weekday bonuses. Until an owner-approved behavior change lands,
all three source checks remain visible to practitioners.

A broader Yajna can carry ritual-specific Kalpa and Sampradaya requirements
beyond these Homahuti verses. The officiating priest’s requirements take
precedence over this generic profile.
