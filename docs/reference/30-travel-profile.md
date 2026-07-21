# Travel Source Profile

## Claim and authority

The `travel` activity is linked to `muhurta.travel`. Its authority is B. V.
Raman's *Muhurtha*, Chapter XIV, "Journeys" and "Long-distance Journeys,"
printed pages 60-61 (PDF pages 64-65 in the registered edition). Raman is a
modern secondary authority, not scripture.

## Automated criteria

The passage says Bharani and Krittika should invariably be rejected. These are
hard slot-time gates. Ten Nakshatras described as best for satisfactory
completion and early return receive a preference rather than becoming an
exclusive list.

The implementation introduces a reusable `avoid_nakshatras` field so hard
negative evidence is not misrepresented as a positive allow-list. Python,
MCP, and the generated browser contract consume the same field.

## Chart checks and separate rules

The profile discloses Raman's Lagna, Guru/Shukra, waxing-Chandra, Mangala, and
7th-house checks. Vishti rejection follows the separately cited general
Panchanga-Suddhi rule. Chara-Lagna and Tiryan-Mukha scoring remain separately
attributed project rules and do not inherit authority from this claim.

## Known contract conflicts

Raman also says Chaturdashi plus Full and New Chandra days must be avoided at
any cost. An existing integration test explicitly requires travel slots on the
Amavasya of 2026-06-15, so implementing that hard gate requires owner approval
to change the existing contract.

Direction filtering is likewise outside this claim. Raman gives
time-of-day exceptions to the weekday-direction prohibitions; the current
implementation rejects the entire day, and existing tests explicitly pin that
behavior. Both corrections remain owner-approval-gated rather than being
concealed inside an otherwise verified Nakshatra profile.
