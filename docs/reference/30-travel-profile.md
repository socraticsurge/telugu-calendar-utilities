# Travel Source Profile

## Claim and authority

The `travel` activity is linked to `muhurta.travel`. Its authority is B. V.
Raman's *Muhurtha*, Chapter XIV, "Journeys" and "Long-distance Journeys,"
internal printed pages 60-61 (physical PDF pages 64-65 in the inspected 2020
Chistabo derivative). Raman is a
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

The browser asks for one primary traveller. It rejects candidate Lagnas that
are 1st, 5th, 7th or 9th inclusively from that traveller's Janma Lagna, and a
candidate Lagna matching the traveller's Janma Rashi is one tie-break
preference when the match persists across every sampled state. A prohibited
personal Lagna at any sample rejects the window. Samples cover the window
edges and both sides of every known interior Drik Lagna transition. The Drik chart post-screen
rejects Kuja in the 8th. The source asks for Guru or Shukra to be well placed
in Lagna; occupancy alone does not establish that qualitative condition, so it
does not earn an automated tie-break.

Guru/Shukra quality, waxing-Chandra, general fortification and the 7th-house
malefic judgment remain manual. Vishti rejection follows the separately cited general
Panchanga-Suddhi rule. Chara-Lagna and Tiryan-Mukha scoring remain separately
attributed project rules and do not inherit authority from this claim. The
chart and role screen is browser-only; Python/MCP keep the full manual wording.
See [Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).

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
