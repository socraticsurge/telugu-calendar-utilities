# Wedding (Vivaha) source profile

## Authority and status

`wedding` follows B. V. Raman, *Muhurtha (Electional Astrology)*, Chapter IX,
“Electing a Time for Marriage,” internal printed pages 41–42 (physical PDF
pages 45–46 in the inspected 2020 Chistabo derivative). Raman is
a modern secondary authority, not scripture. The claim `muhurta.wedding` means
the configured criteria match this named passage; it does not claim that all
regional Panchangams use the same method.

The former profile was contradicted: it rewarded the entire Purna family and
penalized the entire Jaya family, reversing Raman on Pournami, Shukla Tritiya
and Shukla Trayodashi. Those proxies have been removed.

## Exact automated crosswalk

| Criterion | Passage | Product treatment |
|---|---|---|
| Lunar month | Magha, Phalguna, Vaishakha and Jyeshtha good; Kartika and Margashira ordinary | All six admitted |
| Conditional month | Pushya with Surya in Makara; Chaitra with Surya in Mesha | Exact `(Maasa, solar Rasi)` pairs admitted |
| Tithi | Reject Krishna Ekadashi through Amavasya, Rikta, Shashthi, Ashtami and Dwadashi; seven named Shukla Tithis best | Every non-rejected Shukla/Krishna Tithi admitted by exact Paksha-qualified name; no family proxy |
| Vara | Monday, Wednesday, Thursday and Friday best; Sunday/Saturday middling; Tuesday rejected | Six admitted, four receive a preference bonus |
| Nakshatra | Rohini, Mrigashira, Magha, Uttara, Hasta, Swati, Anuradha, Moola, Uttara Ashadha, Uttara Bhadrapada and Revati | Exact eleven-star gate; “Uttara” resolved as Uttara Phalguni |
| Yoga | Vyatipata, Dhruva, Mrityu, Ganda, Vajra, Shoola, Vishkambha, Atiganda, Vyaghata and Parigha rejected | Nine matching Nitya Yogas hard-gated; Mrityu remains manual because it is not one of the engine's 27 Nitya Yogas |
| Karana | Vishti rejected | Slot-level hard gate |
| Lagna | Mithuna, Kanya and Tula best; Vrishabha, Karka, Simha, Dhanu and Kumbha middling | Exact eight-Rasi gate with a bonus only for the best three |

The finder also retains separately sourced conservative samskara safeguards:
Adhika and Pitru Paksha, Sankramana, Guru/Shukra combustion, Simha-Stha and the
shared Visha/Dagdha layer. The Raman claim does not falsely attribute those
extra filters to this passage.

## Computed and mandatory manual prerequisites

Reject Magha and Moola Pada 1 and Revati Pada 4. Pada is not computed across
every product surface, so these remain explicit mandatory checks. The same is
true for Raman's named “Mrityu Yoga,” whose definition is not represented in
the 27-Nitya-Yoga model.

The Drik browser chart post-screen rejects an occupied 7th, Mangala in the 8th,
or Shukra in the 6th at any sampled state (the window edges and both sides of
every known interior Drik Lagna transition). Malefics around Lagna,
Chandra's association with another Graha, the named fortifications,
compatibility, Tarabala, Chandrabala and Panchaka still require couple-specific
review. Those unresolved facts cap every automated result below `Excellent`.
Python/MCP retain the complete list as `manual_checks` because they do not call
the chart service. See
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).

## Published-practice divergence

Drik Panchang's 2026 Hyderabad marriage table admits qualifying Tuesdays and
Tithis including Chaturdashi, Pournami, Shashthi and Navami that this Raman
method rejects. Drik Panchang also applies its own solar/lunar-month, Adhika,
Chaturmas and Guru/Shukra Asta method.

This is recorded as `muhurta.wedding.drkpanchang_divergence`. The application
does not present Raman-lineage results as identical to Drik Panchang's date
set, and timing cannot replace consent or relationship judgment.
