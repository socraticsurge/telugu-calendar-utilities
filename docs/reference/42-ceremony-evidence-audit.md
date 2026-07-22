# Shantika / Paushtika Source Profile

## Scope and authority

The `ceremony` compatibility key now names a **Shantika / Paushtika rite** and
links to verified claim `muhurta.shantika_paushtika`. It is not a generic
election for every ceremony or Puja.

The source is Rama Daivajna, *Muhurta Chintamani*, undated Sanskrit text with
Hindi commentary, Nakshatra-prakarana, “Shantika and Paushtika Muhurta,” verse
34, printed pages 42–43 (Internet Archive OCR lines 2749–2772). The scan lacks
publisher and date metadata, which the source register discloses.

## Exact crosswalk

| Source criterion | Implementation | Boundary |
|---|---|---|
| Reject Rikta, Ashtami, Pournami and Amavasya | `avoid_tithi_numbers = [4, 8, 9, 14, 15]` | 15 covers both lunar termini |
| Reject Sunday, Tuesday and Saturday | Four-day `allowed_varas` | Hard day gate |
| Fifteen named Nakshatras | Exact `allowed_nakshatras` | Hard day gate |
| Reject Sankramana | `skip_on_sankramana = true` | Hard day gate |
| Surya in the 10th, Chandra in the 4th, Guru in Lagna | Manual chart check | `manual_prerequisites = true` caps results below Excellent |
| Ideally avoid Guru/Shukra combustion and exceptional omens | Manual purity check | Not uniformly computable across all surfaces |

The passage's examples are auspicious Puja, welfare-oriented Purashcharana and
Mula-shanti. Those examples do not authorize a universal “ceremony” profile.

## Remedial exception

The commentary says that when an ominous event itself creates the need for
Shanti, ordinary timing defects need not prevent the remedial rite. The finder
therefore must not be used to delay an urgent Shanti; the officiating
practitioner determines how the exception applies.
