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
| Traditional windows | Needs locator | Needs locator | The response combines formulas from different traditions; no umbrella citation is valid |
| Festivals and special-day labels | Partially verified | Partially verified | The forward fixture has 1 independently checked cell and 29 engine-pinned cells |
| Eclipse events | Engine-pinned | Engine-pinned | No independent event-by-event comparison fixture is registered |
| Derived classifications | Needs locator | Needs locator | Each Yoga, Dosha and classification needs its own table crosswalk |

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

The next evidence work should resolve one group at a time, starting with the
Pancha Anga/calendar semantics and the high-visibility Rahu Kalam, Varjyam and
Durmuhurtham tables. Exact locators and independent city/date comparisons must
precede any upgrade to `verified`.
