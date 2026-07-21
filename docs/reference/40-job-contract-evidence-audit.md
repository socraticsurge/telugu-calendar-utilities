# Job Start / Contract Signing Evidence Audit

## Status

The combined Job start / Contract signing profile is **not source-verified**.
Its `audit_claim`, `muhurta.job_contract.profile_conflict`, has state
`contradicted`.

## Inspected authority

- Rama Daivajna, *Muhurta Chintamani*, Sanskrit text with Hindi commentary.
- Internet Archive identifier `muhurta-chintamani-hindi`; publisher and date
  are absent from the scan metadata.
- Nakshatra-prakarana, “Entering the service of a master,” verse 26, printed
  page 38; OCR lines 2565–2577.
- “Sandhana Muhurta,” verse 42, printed pages 45–46; OCR lines 2880–2891.

## Service-entry crosswalk

| Criterion | Current profile | Verse 26 | Status |
|---|---|---|---|
| Nakshatra | No activity-specific preference | Ashwini, Pushya, Hasta, Chitra, Anuradha, Mrigashira and Revati | Missing |
| Vara | Wednesday and Thursday preferred | Wednesday, Friday, Sunday and Thursday | Incomplete |
| Lagna | Fixed-sign preference | Benefic occupying Lagna | Different criterion |
| Houses | Not represented | Surya or Mangala in the 10th or 11th | Missing |
| Relationship | Not represented | Employer/employee birth-Yoni and Rasi-lord friendship | Missing |
| Other ranking | Amrit and Nanda rewarded | Not supplied by this verse | Project heuristics |

## Contract-signing boundary

Verse 42 concerns Sandhana: making peace, alliance or friendship. It gives
Pushya, Anuradha and Purva Phalguni; Ashtami and Dwadashi; Monday, Wednesday,
Thursday and Friday; Taitila Karana; and a Shukra-influenced Lagna. Translating
Sandhana into a modern employment agreement or commercial contract is a
semantic leap the text does not establish.

The user-facing option therefore combines two distinct activities while
implementing neither source profile. A single citation cannot make that
taxonomy precise.

## Correction boundary

The clean correction is to separate service entry from modern contract signing
and give each a defensible rule set. That changes the 30-activity public
contract and existing tests, so this audit does not perform it without owner
approval. Until then, Python, MCP and browser results expose the three manual
checks and the conflict claim rather than presenting the option as verified.
