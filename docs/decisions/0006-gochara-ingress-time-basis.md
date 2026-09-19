# Gochara next-ingress date basis

## Decision (#180)

Retain `graha_positions().rasi_until` as a calendar date in IST
(`Asia/Kolkata`, UTC+05:30), independent of the requested city. `next_rasi`
continues to name the destination sign. No existing response field is renamed,
removed, or converted into an instant. A location determines the sunrise instant
at which positions are requested; it does not redefine this date convention.
The MCP tool description, package documentation and interpretive prompt now state
that convention explicitly. Release 1.18.18 carries the MCP description change.

The website previously ignored `rasi_until`: its generated rows retained only
Hyderabad-sunrise sign indices, and the browser scanned forward to the first
changed row. This can be the next IST day after an ingress. For example, the
existing engine puts the July 2026 Surya ingress after Hyderabad sunrise on July
16; the old scan displayed July 17. This is engine-contract evidence, not a new
independent ephemeris validation.

## Additive static-data projection

`gochara.json` retains `start`, `grahas`, `rasis`, `days` and `retro` unchanged.
It adds `ingressTimeBasis: "Asia/Kolkata"` and `ingresses`: one row per existing
day, one entry per graha, containing `[rasi_until, next_rasi_index]` or `null`.
The generator already computes these values; projection adds no ingress searches.
The browser displays the exact projected date with `(IST)` in both chart tooltips
and upcoming moves. Legacy cached data remains readable, but its fallback is
labelled `(Hyderabad sunrise sample)` rather than presented as an exact ingress.
A present exact-date row with a null entry does not silently invent a fallback.

The site's date index still selects the daily Hyderabad-sunrise snapshot; this
change does not make it a live intraday ephemeris. Dates are formatted as calendar
labels without conversion to the device timezone. Cached files remain usable
offline under the existing fetch/cache behavior; no new service is introduced.

## Consumer inventory and verification

- MCP `get_graha_positions`, `get_gochara`, and `get_rasi_phalalu` consume the same
  Python owner; the latter two use its positions for interpretation/rules.
- `scripts/build_gochara_json.py` exports the date/sign pairs directly.
- `scripts/generate_llm_phalalu.py` and `personal/llm_phalalu.py` retain the same
  positional data; prompt text labels any ingress date as IST.
- The website's chart tooltip and upcoming-move list share the same lookup.
- Library callers retain the original dictionary shape and `rasi_until` meaning.

New York and Sydney fixtures exercise ingress events whose local dates differ
from IST, and confirm that the location-aware MCP result preserves IST. Generated
rows are checked against the public Python owner, including the July 16 versus
July 17 sunrise discrepancy. Browser tests cover exact and legacy payloads.
Frozen engines and existing behavioral assertions remain unchanged.
