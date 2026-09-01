# Gruhapravesha source profile

## Status and ritual boundary

`gruhapravesha` is a source-verified Raman-lineage profile for the first
ceremonial entry into a newly built home. It is not the election for buying a
completed house, moving into a rental, returning after renovation, or laying a
foundation or roof. Those acts have separate scopes.

The governing claim is `muhurta.gruhapravesha`. B. V. Raman, *Muhurtha
(Electional Astrology)*, UBS Publishers' Distributors, 1993, Chapter XII,
“House building,” section “Entering a new house,” printed pages 52–54 (PDF
pages 56–58), is a modern secondary authority rather than scripture.

## Automated crosswalk

| Criterion | Raman passage | Product treatment |
|---|---|---|
| Tithi | Krishna Pratipat; Shukla Dwitiya, Tritiya, Panchami, Saptami, Dashami, Ekadashi and Trayodashi | Exact Paksha-qualified hard gate |
| Vara | Monday, Wednesday, Thursday and Friday | Exact sunrise-weekday hard gate |
| Nakshatra | Rohini, Mrigashira, Uttara Ashadha, Chitra and Uttara Bhadrapada best; Anuradha and Revati permissible | All seven admitted; no invented score difference |
| Solar state | Surya in Uttarayana | Makara through Mithuna hard gate, the traditional six-Rasi mapping |
| Lagna | Fixed preferred; dual ordinary; movable generally avoided except with Vrishabha Navamsa | Fixed and dual Rasis admitted, with a fixed-Rasi bonus; movable exception omitted because Navamsa is not computed across every surface |

Omitting the movable-Rasi exception is conservative: it can reject a source
exception, but it cannot admit a time Raman rejects. The UI and MCP response
state that boundary explicitly.

## Browser-computed and manual prerequisites

The Drik browser post-screen rejects an occupied 8th at any sampled state.
Selecting a primary householder also turns a match to that person's Janma
Rasi, Nakshatra or Lagna across every sampled state into one source preference
without a raw-score bonus. Samples cover the window edges and both sides of
every known interior Drik Lagna transition.
A practitioner must still review Guru, Shukra and Chandra strength; malefics in
Upachayas; benefics in Kendras; and preferably a Guru- or Shukra-owned rising
Rasi. Worship and Bhootabali precede entry. Python/MCP retain the full list as
manual checks because they do not call the chart service. See
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).

Raman advises against the entry after six months of the wife's pregnancy.
Maternal comfort, clinician instructions and medical care always take
precedence; the timing profile makes no health or pregnancy-outcome claim.

## Published-practice divergence

Drik Panchang's 2026 Griha Pravesh methodology and date table reject Sunday
and Tuesday but admit qualifying Saturdays. Raman names Monday, Wednesday,
Thursday and Friday, mentioning Saturday only as another-writers' view with a
theft caution. Drik Panchang also applies lunar-month and Adhika-month filters
not imported into this Raman profile.

The disagreement is recorded as
`muhurta.gruhapravesha.drkpanchang_divergence`. The application names and
follows one lineage instead of silently blending both.
