# Gruhapravesha Evidence Audit

## Status

Gruhapravesha (first entry into a newly built home) is supported as an activity,
but its current finder profile is **not source-verified**. The machine-readable
`audit_claim` is `muhurta.gruhapravesha.profile_conflict`, with state
`contradicted`.

## Inspected authority

- B. V. Raman, *Muhurtha (Electional Astrology)*, UBS Publishers'
  Distributors, 1993.
- Chapter XII, “House building,” section “Entering a new house.”
- Printed pages 52–54; PDF pages 56–58.
- Raman is a modern secondary authority, not scripture.

## Criterion crosswalk

| Criterion | Current profile | Inspected passage | Status |
|---|---|---|---|
| Tithi | Bhadra family receives a bonus; every Jaya Tithi receives a penalty | Krishna Pratipat and Shukla Dvitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi and Trayodashi are named | **Conflict:** Tritiya and Trayodashi are Jaya Tithis that the profile penalizes |
| Vara | Monday and Thursday receive a bonus; other weekdays remain admissible | Monday, Wednesday, Thursday and Friday are auspicious; Saturday is reported by some writers with a theft caution | Incomplete and too permissive |
| Nakshatra | No activity-specific gate | Rohini, Mrigashira, Uttara Ashadha, Chitra and Uttara Bhadrapada are best; Anuradha and Revati permissible; others rejected | Missing |
| Lagna | Fixed class receives a bonus | Fixed Rasi is the default; common is ordinary; movable generally avoided except with Vrishabha Navamsa | Preference is weaker than the source rule |
| Solar/Graha state | Broad seasonal and calendar exclusions | Surya in Uttarayana; Guru and Shukra strong; Chandra strong | Only partly represented |
| Election chart | Not computed across every surface | 8th vacant; malefics in Upachayas; benefics in Kendras; preferably Guru- or Shukra-owned rising Rasi | Manual check |
| Personal/ritual | Not derivable from date alone | Worship and Bhootabali before entry; own Janma Rasi/Nakshatra/Lagna beneficial; avoid after six months of the wife's pregnancy | Manual check |

## Correction boundary

An existing test explicitly preserves Sunday as an admissible Gruhapravesha
day and expects only a soft Bhadra bonus. Applying Raman's weekday and exact
Tithi/Nakshatra admission rules would change that contract. Under the project's
working agreement, the finder behavior remains unchanged until the owner gives
specific approval for that correction.

When approved, the implementation should use exact Paksha-aware Tithi names,
the seven admitted Nakshatras, the four unambiguously auspicious weekdays, and
a fixed-Lagna gate with the stated Navamsa exception. Chart, ritual and
pregnancy conditions should remain visible manual checks unless reliable input
and calculation support is added to every surface.
