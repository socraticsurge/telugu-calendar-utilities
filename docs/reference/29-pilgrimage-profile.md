# Pilgrimage Source Profile

## Claim and authority

The `pilgrimage` activity is linked to `muhurta.pilgrimage`. Its authority is
B. V. Raman's *Muhurtha*, Chapter XIV, "Journeys" and "Pilgrimage," internal
printed pages 60-62 (physical PDF pages 64-66 in the inspected 2020 Chistabo
derivative). Raman is a modern
secondary authority, not scripture.

The pilgrimage paragraph explicitly says to follow the preceding journey
rules. It then adds two activity-specific conditions: Guru should occupy
Lagna or the 9th house, and months of Guru combustion should be avoided.

## Automated and manual criteria

The incorporated journey section says Chaturdashi and Full/New Chandra days
must be avoided, so the profile rejects Tithi numbers 14 and 15. It calls ten
Nakshatras the best for satisfactory completion and early return; these earn
a preference rather than becoming an exclusive admission list. Guru
combustion is a hard exclusion. Guru in Lagna or the 9th is a source-backed
tie-break preference in the Drik browser chart post-screen only when it passes
across every sampled state (the window edges and both sides of every known
interior Drik Lagna transition); its absence does not reject a slot. Python/MCP
retain this as a visible manual check because
they do not call the chart service. See
[Muhurtam election-chart screening](54-muhurtam-election-chart-screening.md).

The existing Vishti-Karana exclusion agrees with the separately cited general
Panchanga-Suddhi rule. The existing Chara-Lagna bonus remains a project
heuristic: Raman names six individual favorable journey Rasis rather than the
Chara class. This claim does not lend that bonus textual authority.

Python, MCP, and the generated browser contract publish the same claim ID,
automated constraints, Nakshatra preferences, and manual check. The browser
enforces Guru combustion from the per-city Lagna sidecar and fails closed when
that screening datum is unavailable.
