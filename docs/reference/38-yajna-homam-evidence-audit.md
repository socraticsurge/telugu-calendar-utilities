# Homa Offering (Homahuti) Evidence Audit

## Verdict

The `yajna` compatibility key now represents the narrower, source-verified
**Homa offering (Homahuti)** election. It applies both computations in
Muhurta Chintamani, Nakshatra-prakarana 35-36 as hard gates. The former Purna,
Jaya, weekday and fixed-Lagna proxies have been removed.

## Source

- **MC-HINDI-IA** — *Muhurta Chintamani*, Hindi edition,
  Nakshatra-prakarana, “Homahuti Muhurta” and “Agnivasa,” verses 35-36,
  printed pp. 43-44; Internet Archive full-text OCR lines 2773-2796.

## Implemented reading

Verse 35 counts the active lunar Nakshatra inclusively from Surya's Nakshatra.
The 27 Nakshatras form nine consecutive groups of three, assigned in order to
Surya, Budha, Shukra, Shani, Chandra, Mangala, Guru, Rahu and Ketu. The
offering is rejected for a `khala` (malefic) group; automation therefore
admits the natural-benefic groups Budha, Shukra, Chandra and Guru and rejects
Surya, Mangala, Shani, Rahu and Ketu.

Verse 36 numbers the Tithi from Shukla Pratipat across the full 30-Tithi lunar
month, adds one, adds the weekday number counted Sunday=1 through Saturday=7,
and takes modulo four. Remainders 3 and 0 place Agni on earth and admit Homa;
remainder 1 places Agni in heaven and remainder 2 in the underworld, so both
are rejected.

Both tests are recomputed at each slot start using the selected Panchangam
engine's Sun and Moon model. Passing slots disclose the group lord and the
Agnivasa remainder in `activity_match`.

## Boundary

This verifies an election for a fire offering, not a universal election for
every ceremony called Yajna. The officiating priest's Kalpa/Sampradaya rules,
ritual arrangements and fire safety remain explicit manual prerequisites.
