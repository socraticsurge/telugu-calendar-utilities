# Completed-house purchase source profile

## Authority and scope

The `house_purchase` activity uses B. V. Raman, *Muhurtha (Electional
Astrology)*, Chapter XII, “Buying Houses,” printed page 53 (PDF page 57).
Raman explicitly includes both new and old completed houses. This is not the
election for buying land for construction, starting building work, moving into
a rental, or performing Gruhapravesha.

Rama Daivajna's *Muhurta Chintamani*, Nakshatra-prakarana verse 16, printed
pages 33–34 (OCR lines 2336–2350), was inspected as an independent buyer-side
authority. Its generic purchase Nakshatras are materially different. The
implementation therefore links that claim for comparison but does not combine
the two formulas or let the generic rule override the house-specific passage.

## Automated crosswalk

| Source statement | Product rule |
|---|---|
| Nanda Tithis are favourable | Admit Tithi numbers 1, 6 and 11 |
| New and old houses may be purchased Thursday and Friday | Admit `Guruvaram` and `Shukravaram` |
| Eight auspicious constellations | Admit Mrigashira, Ashlesha, Magha, Purva Phalguni, Vishakha, Moola, Punarvasu and Revati |
| Five signs are “best” | Prefer, but do not require, Vrishabha, Mithuna, Simha, Tula and Vrischika Lagnas |

“Best” is implemented as a score bonus rather than an exclusion. This avoids
turning a textual preference into an unsupported hard prohibition.

## Practitioner and practical checks

The Drik browser post-screen rejects Mangala in Lagna at any sampled state
(the window edges and both sides of every known interior Drik Lagna
transition). Keeping malefics out of the 7th remains a qualitative practitioner check,
so unresolved review still caps the result below `Excellent`. Python/MCP retain
both clauses as manual wording because they do not call the chart service. See
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).

Legal title, structural inspection, finance affordability and qualified
contract advice always take precedence over electional timing. The profile
does not predict property quality, ownership security or investment return.
