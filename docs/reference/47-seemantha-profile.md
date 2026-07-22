# Seemantha Source Profile

## Authority and scope

The `seemantha` activity is linked to the verified claim
`muhurta.seemantha`. Its authority is B. V. Raman's *Muhurtha*, Chapter VII,
“Seemantha,” printed pages 20–21 (PDF pages 24–25 of the registered scan).
Raman is a modern secondary synthesis, not primary scripture; this status
means the implemented criteria match this inspected passage within its stated
scope.

The profile also exposes the related contradicted claim
`muhurta.seemantha.chintamani_divergence`, from *Muhurta Chintamani*,
Samskara-prakarana verse 8, printed page 77 (OCR lines 4157–4180). This is not
used to launder Raman's profile into universal authority; it records where an
independent classical passage agrees and disagrees.

Raman treats Seemantha as a prenatal rite for the first pregnancy,
normally in the fifth or seventh month. If that schedule cannot be kept, it
reports the view of sage Sankha that the rite should still occur before
delivery. The calendar month is not the pregnancy month, so the finder cannot
automate this prerequisite and displays it as a practitioner check.

Muhurta Chintamani instead prescribes the sixth or eighth month. It corroborates
the automated Tithi exclusions, includes the profile's nine stars across its
primary and alternative lists, supplies the same Monday/Wednesday/Thursday/
Friday alternative, and likewise relaxes Guru/Shukra combustion. Its
male-planet Lagna/Navamsha and house-placement formulation differs from Raman's
ten admitted Rasis. A family must choose its lineage with a qualified
practitioner; the product does not call either pregnancy-month rule universal.

## Automated crosswalk

| Criterion | Inspected passage | Implementation |
|---|---|---|
| Nakshatra | Raman's nine primary stars; all occur across Chintamani's primary and alternative lists | Exact Raman admission list |
| Tithi | Reject Chaturthi, Shashthi, Ashtami, Navami, Chaturdashi and Amavasya | Exact Paksha-qualified admission list |
| Vara | Raman rejects Sunday, Tuesday and Saturday; Chintamani gives the admitted set as an alternative | Monday, Wednesday, Thursday and Friday admitted |
| Lagna | Reject Simha and Vrischika | The remaining ten Rasis admitted |
| Pournami | Allowed only when Chandra is dignified | Conservatively omitted pending chart judgment |
| Combustion | Pregnancy month takes precedence; Guru/Shukra combustion may be ignored | No combustion gate |

## Practitioner checks

- Confirm that this is the first pregnancy and choose the pregnancy-month rule
  with a qualified practitioner: Raman gives the fifth/seventh month and
  Chintamani verse 8 gives the sixth/eighth.
- Ashwini, Anuradha and Moola are only unavoidable-circumstance alternatives;
  they are not included in automatic results.
- Leave the eighth house vacant and keep Chandra out of the eighth.
- Check the passage's 3rd, 7th, 8th, 10th and 22nd relative birth-Nakshatra
  exclusions for the mother.
- Admit Pournami only after judging Chandra dignified.

## Safety boundary

The profile schedules a cultural ceremony; it does not assess pregnancy or
maternal/fetal health. Maternal comfort, clinician instructions and timely
medical care always override electional timing. No result predicts a medical
outcome.

## Cross-surface contract

The Python rules are the source of truth. The generated browser contract and
MCP `activity_profile` expose the same claim, hard gates and manual checks.
Tests protect the exact source crosswalk, reject accidental generic samskara
filters and require catalogue parity. Because the pregnancy-month, relative
birth-Nakshatra and election-chart prerequisites cannot be computed from the
finder inputs, `manual_prerequisites` caps every result below `Excellent` until
practitioner review; a high relative score never hides that uncertainty.
