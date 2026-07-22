# Panchangam Provenance Disclosure

The daily Panchangam mixes astronomical events, calendar conventions,
traditional time windows, festival rules and derived classifications. A green
calculation test for one layer cannot grant authority to the others.

`tool_get_panchangam`, `tool_get_panchangam_range` and the compact
`tool_get_muhurta` therefore return a `provenance` object whose
`coverage_groups` cover every non-identity output category. Each group names a
ledger claim, its current state and a plain-language limitation.

## Current evidence map

| Group | Drik state | Surya Siddhanta / Vakya state | Main limitation |
|---|---|---|---|
| Pancha Anga and sky events | Partially verified | Engine-pinned | Representative comparisons are not exhaustive; non-Drik systems lack an external fixture |
| Calendar metadata | Needs locator | Needs locator | Naming and rollover conventions need criterion-level and regional sources |
| Mixed daily windows | Partially verified | Partially verified | Varjyam and Durmuhurtham have inspected passages; several regional component tables still need criterion-level evidence |
| Bhadra Mukha / Puchha | Verified | Verified | Muhurta Chintamani 44 supplies the Tithi-specific quarters and nominal widths |
| Sankramana avoidance | Verified | Verified | Raman explicitly rejects 16 Ghatis on either side of solar ingress |
| Festivals and special-day labels | Partially verified | Partially verified | The forward fixture has 1 independently checked cell and 29 engine-pinned cells |
| Eclipse events | Engine-pinned | Engine-pinned | No independent event-by-event comparison fixture is registered |
| Panchaka Rahita | Verified | Verified | Raman supplies the four-factor modulo-nine rule, result names and activity exceptions |
| Other derived classifications | Needs locator | Needs locator | Each Yoga, Dosha and classification needs its own table crosswalk |

## Why this matters

“Computed” means that an engine produced a value. “Engine-pinned” means tests
will detect output drift. Neither means a traditional interpretation has an
inspected scriptural locator, nor that an external Panchangam agrees for all
locations and dates. Consumers can now preserve those distinctions instead of
presenting the whole response as uniformly verified.

## Enforcement

Tests flatten `coverage_groups.fields` and require exact coverage of every
non-identity response key. They also resolve every `claim_id` against
`provenance.json` and require the declared state to match the ledger. Adding a
new Panchangam response category without assigning an evidence state fails the
contract test.

The remaining evidence work should resolve one component at a time, starting
with calendar semantics and the high-visibility Rahu Kalam, Gulika,
Yamagandam and Choghadiya tables. A mixed response container remains only
`partially_verified` until every component is independently supported; an
inspected passage for one member never upgrades the whole bundle.
