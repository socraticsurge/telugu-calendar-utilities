# Borrowing-money source profile

## Default authority and artifact identity

The `borrowing_money` activity follows B. V. Raman, *Muhurtha (Electional
Astrology)*, Chapter X, “Borrowing Money,” internal printed page 45. The
inspected artifact is the hosted 2020 Chistabo derivative, physical PDF page
49, SHA-256
`b8b878a444a487c83810329fdf8f057c40e92221a867db480d864da8be21a133`.
The registered 1993 Raman work is bibliographic identity only; the source
registry does not falsely claim that physical edition was inspected.

This is strictly the borrower or debtor side of taking a loan. Lending money,
receiving repayment, investing capital and purchasing inventory are different
acts.

## Raman clauses and inherited baseline

Raman prohibits borrowing under Krittika, Moola, Punarvasu and Dhanishtha and
under the primary borrower’s Janma Nakshatra. The four universal exclusions
remain deterministic. The browser now requires exactly one primary borrower
for the personal star gate; other selected profiles continue to participate in
generic multi-person ranking but do not become borrowers.

The paragraph supplies no event-specific weekday or Tithi list. It does,
however, explicitly say that purity of Tithi, weekday, Nakshatra and Tarabala
is essential for any election. The default mode therefore inherits the
registered Raman general-purity baseline. That reusable baseline is incomplete
under issue #284, so the product may describe the attributable Borrowing event
layer as complete but cannot call the whole election complete.

## Automated chart rule

The accepted conjunction convention is
`same-rasi-distributive-conjunction-v1`:

`R(Chandra) = R(Kuja) OR R(Chandra) = R(Shani)`

There is no degree orb. Either known equality rejects the candidate; pass
requires both inequalities to resolve. Missing, malformed, duplicate or
conflicting facts are unknown. Across a window, a known failure dominates
unknown, unknown dominates pass, and an all-pass window remains unknown unless
the Chandra, Kuja and Shani Rasi transitions are covered within the chart
request budget. The event evaluator wires that one accepted predicate; it
does not import any Chintamani or current-Drik clause.

## Borrower and ephemeral purpose context

Version 1 accepts exactly one `primary_borrower` and one of these broad values:

- `quick_domestic_or_personal`
- `business`
- `other_or_unknown`

The purpose choice is page-memory only. It is not written to browser storage,
sent to the chart service, placed in a URL or emitted to analytics. The product
does not ask for or transmit amount, lender, collateral, repayment terms,
address or financial notes. A missing or `other_or_unknown` purpose is an
unknown completion state, never a pass. Only the applicable purpose guidance
is shown; inactive purpose rows are not evaluated or displayed as failures or
unknowns.

## Qualitative-purpose research decision

The complete registered Raman artifact and the registered aspect, natural
nature, lordship, relationship and dignity authorities were checked. Raman
does not define either qualitative phrase used in this paragraph. Version 1
therefore keeps both manual instead of hiding an arbitrary composite behind
“favourable.”

| Candidate interpretation | Domestic “good aspect to Lagna” | Business “favorable situation” | Decision |
| --- | --- | --- | --- |
| Literal full Graha Drishti | Defines geometry only; does not define “good” | Does not resolve the three-way Chandra–Budha–Lagna-lord grammar | Unselected |
| Kendra/Trikona relation | Plausible placement proxy but not stated here | Does not define direction or Budha/lord combination | Unselected |
| Conjunction or full aspect | Adds an unstated OR and no quality rule | Does not define deduplication when Budha is Lagna lord | Unselected |
| Natural or temporary friendship | Not an aspect to Lagna | Directed natural friendship does not define the complete phrase; temporary and compound friendship remain unresolved | Unselected |
| Dignity or strength | Conflates quality with aspect geometry | Creates an unstated composite and risks calling a bounded proxy full strength | Unselected |
| Manual source wording | Preserves geometry, quality and product effect as separate unresolved choices | Preserves Budha, Lagna-lord and Chandra facts without inventing precedence | Selected v1 |

For quick domestic or personal use, a practitioner must assess whether Chandra
is in good aspect to Lagna. For business use, a practitioner must assess
Chandra’s favorable situation with Budha and the Lagna lord. The unresolved
checks cap completion without adding score or claiming a financial outcome.

## Alternate, non-blended modes

The machine-readable registry is
`telugu_panchangam.personal.borrowing.BORROWING_MODE_REGISTRY`. Exactly one
mode may be active. The default is always `raman-borrowing-1993-v1`; either
alternate requires its explicit mode ID and is presently registered but not
implemented as a runtime assessor.

### Muhurta Chintamani verse 27

The registered scan is *Muhurta Chintamani*, Nakshatra-prakarana verse 27,
printed pages 38–39, physical PDF pages 47–48, OCR lines 2578–2599, SHA-256
`9e931eb7fdc1958516424590a168680be60753f4cfccea8f327cae973dfe4777`.
Its commentary combines debt-taking with broader Dravyaprayoga. The separate
mode records its twelve Nakshatras, Chara Lagna, benefics in houses 5 and 9,
empty house 8, and its Tuesday, Sankranti, Vriddhi Yoga, Hasta and Sunday
prohibitions. Its Wednesday statement belongs to lending, not borrowing. This
is an alternate lineage, not evidence that either text falsifies the other.

### Current Drik published practice

The dated `drik-loan-taking-2026-09-v1` record captures the methodology
reviewed on 12 September 2026: avoid Tuesday, Vriddhi Yoga, Sankranti and the
Sunday-plus-Hasta Amrit Siddhi combination; prefer Wednesday; use its published
monetary Nakshatras and movable Lagna; and prefer houses 5, 8 and 9 vacant.
This is a dated description of published practice, not a derivation or
validation oracle for Raman or Chintamani.

## Completion and financial safety

The attributable automated Borrowing checks are the universal Nakshatra gates,
the explicit primary-borrower Janma gate and the same-Rasi conjunction reject.
Purpose phrases and the inherited general baseline remain visibly incomplete.
Alternate-mode incompleteness does not block the Raman event-layer result, but
does block any statement that every Borrowing lineage is automated.

Muhurtam cannot establish affordability or predict repayment success.
Repayment capacity, total cost, lender terms, collateral risk and qualified
financial or legal advice always take precedence over timing.

## UI review evidence

The browser form was verified at desktop and mobile sizes with a required
primary-borrower selector, a broad purpose selector, an explicit no-financial-
details prompt and a fail-closed empty state:

- [Desktop 1440×900](../screenshots/borrowing-chart-assessor-2026-09-12/borrowing-context-desktop-1440x900.png)
- [Mobile 390×844](../screenshots/borrowing-chart-assessor-2026-09-12/borrowing-context-mobile-390x844.png)

Owner screenshot sign-off is required before the feature branch is pushed.
