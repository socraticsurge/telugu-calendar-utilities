# Dharma-kriya Commencement Source Profile

The compatibility key `beginning` now means beginning Dharma-kriya: religious
or meritorious work. It is not a catch-all for a project, habit, relationship,
relocation or life change; those purposes require distinct elections.

The verified claim `muhurta.dharma_kriya.commencement` uses Rama Daivajna,
*Muhurta Chintamani*, Nakshatra-prakarana verse 30, printed pages 40–41
(Internet Archive OCR lines 2685–2700). The source register discloses the
undated scan's missing publisher metadata.

| Source criterion | Implementation | Boundary |
|---|---|---|
| Thirteen named Nakshatras | Exact `allowed_nakshatras` | Hard day gate |
| Sunday, Monday, Wednesday, Thursday and Friday | Exact `allowed_varas` | Hard day gate |
| Budha or Guru Lagna or Varga | Mithuna, Kanya, Dhanu and Meena in `allowed_lagnas` | Conservative slot gate; Varga remains manual |
| Guru in Lagna | Manual check | Mandatory practitioner review |
| Performer has Guru-bala | Manual check | Requires the personal chart |

`manual_prerequisites = true` caps results below Excellent until the Varga,
Guru placement and personal Guru-bala conditions are checked. The former Amrit
Choghadiya, Nanda-family and Wednesday/Thursday bonuses have been removed
because verse 30 does not supply them.
