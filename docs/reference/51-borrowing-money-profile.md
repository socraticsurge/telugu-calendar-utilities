# Borrowing-money source profile

## Authority and transaction role

The `borrowing_money` activity follows B. V. Raman, *Muhurtha (Electional
Astrology)*, Chapter X, “Borrowing Money,” internal printed page 45 (physical
PDF page 49 in the inspected 2020 Chistabo derivative). It is
strictly the borrower or debtor side of taking a loan. Lending money, receiving
repayment, investing capital and purchasing inventory are different acts.

Rama Daivajna's *Muhurta Chintamani*, Nakshatra-prakarana verse 27, printed
pages 38–39 (OCR lines 2578–2599), was inspected independently. That commentary
combines debt-taking with a broader Dravyaprayoga/capital-deployment election
and supplies a different Nakshatra/Lagna framework. It does not corroborate
Raman's four-star exclusion set. The disagreement is recorded as
`muhurta.borrowing.chintamani_divergence`; the formulas are not blended.

## Automated rules

Raman prohibits borrowing under Krittika, Moola, Punarvasu and Dhanishtha, and
also under the individual borrower's Janma Nakshatra. The four universal stars
are hard exclusions. When users supply their birth stars, the Janma-star gate
is now enforced identically in Python and the browser.

No weekday, Tithi, Lagna-class or Choghadiya preference is added: the cited
paragraph supplies none.

## Manual chart and purpose checks

- Avoid Chandra conjoined with Mangala or Shani.
- For quick domestic or personal use, Chandra should favour Lagna.
- For business use, Chandra should favour Budha and the Lagna lord.

The first clause now has an unwired reusable computation primitive:
`same-rasi-distributive-conjunction-v1` evaluates
`R(Chandra) = R(Kuja) OR R(Chandra) = R(Shani)` with no degree orb. It is not
yet an event result: issue #271 must wire the separately recorded reject policy
alongside the remaining purpose-specific clauses and prove complete sampled-
window coverage. Until then, all three conditions remain visible for
practitioner review and automated results cannot receive `Excellent`.

## Financial safety

Muhurtam cannot establish affordability or predict repayment success.
Repayment capacity, total cost, lender terms, collateral risk and qualified
financial or legal advice always take precedence over timing.
