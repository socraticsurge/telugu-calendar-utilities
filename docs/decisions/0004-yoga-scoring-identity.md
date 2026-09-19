# Yoga scoring identity and display compatibility

Date: 2026-09-19. Scope: issue #183.

## Decision

The scoring boundary uses Python's canonical identity for all 27 Yoga indices.
The browser's existing Priti, Shula and Variyana display/input aliases remain valid.
They map respectively to Preeti, Shoola and Variyan before policy lookup.

This explicitly chooses semantic identity after canonicalization instead of
renaming the raw browser facts; #183's original exact raw-name criterion is
replaced by exact canonical-name/index parity at the policy boundary.
Existing raw-name assertions and display contracts remain unchanged.

The existing generated schema1 artifact gains an additive `canonicalYogaNames`
array from `panchangam_names.YOGA_NAMES`; its ordered `browserYogaNames` array
is unchanged. The exporter owns both projections and its drift guard remains
in the full Python gate. Removing or reordering indices would require a
separate incompatible-contract decision.

## Behavior

Preeti/Priti receives the existing auspicious +1 policy.
Shoola/Shula receives the existing -1 policy through the inclusive 120-minute
partial-dosha boundary; the next minute is neutral.
Canonical and alias feed names identify the same Yoga start.
A genuinely different current feed Yoga uses its end as the next Yoga start.
Explicit activity exclusions accept either spelling.
Variyan/Variyana remains neutral.
Reasons retain the input display spelling; calendar labels and arithmetic do not change.

The shared all-27 fixture is checked against Python's existing slot scorer and
against both browser spellings. It is regression/parity evidence, not a new
independent validation of the traditional disposition rules or slot astronomy.
The selected-system approximation issue #182 remains separate.

## Boundaries

No engine, ICS, MCP, persisted profile or existing assertion changes.
No new Yoga interpretation, score weight, partial-window duration or rule.
Only previously missed alias lookups change their score/exclusion outcome.
