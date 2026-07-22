# Capital Deployment Source Profile

## Scope and authority

The `business` compatibility key now means **deploying capital / business
investment**, not founding or launching a company generally. The verified claim
is `muhurta.capital_deployment`.

The source is Rama Daivajna, *Muhurta Chintamani*, undated Sanskrit text with
Hindi commentary, Nakshatra-prakarana, “Dravyaprayoga and taking a loan,”
verse 27, printed pages 38–39 (Internet Archive OCR lines 2578–2599).

The commentary explains Dravyaprayoga as putting funds to work, including
lending or investing them in employment/business. The product already has a
separate lender-side profile, so this key is restricted to deploying investment
capital in an enterprise. Marketplace opening, inventory purchase and company
formation remain distinct acts.

## Exact crosswalk

| Source criterion | Implementation | Boundary |
|---|---|---|
| Twelve named Nakshatras | Exact `allowed_nakshatras` | Hard slot-time gate |
| Chara Lagna | `required_lagna_class = 'Chara'` | Hard slot-time gate |
| Benefics in the 5th and 9th | Manual check | Mandatory chart review |
| Eighth house unoccupied | Manual check | Mandatory chart review |

`manual_prerequisites = true` caps results below Excellent until the chart is
checked. The former Amrit Choghadiya, Nanda Tithi, weekday and Sthira-Lagna
proxies have been removed because verse 27 does not supply them.

Commercial viability, diversification, liquidity, contracts, taxation,
securities law, due diligence and qualified advice take precedence over timing.
