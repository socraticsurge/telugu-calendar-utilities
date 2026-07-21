# Roof-laying Source Profile

## Claim and authority

The `construction_roof` activity is linked to
`muhurta.construction_roof`. Its authority is B. V. Raman's *Muhurtha*,
Chapter XII, "Laying the Foundation," printed page 50 (PDF page 54 in the
registered edition). Raman is a modern secondary authority, not scripture.

The passage treats house construction as distinct stages and says that the
roofing should be done with Vrishabha or Tula rising. The implementation
therefore admits only those two Lagnas.

## Deliberate limits

This locator does not provide a roofing-specific weekday, Tithi, or Nakshatra
list. The profile does not borrow the adjacent foundation rules for those
dimensions. Its existing Panchaka-Nakshatra restriction comes from a separate
project rule and does not inherit authority from this claim.

This distinction matters: a page-level citation is not permission to combine
neighboring rules that the text assigns to different construction stages.

## Surfaces and enforcement

Python and MCP expose the stable claim ID and the same two-Lagna constraint.
Contract tests pin the rule, verify that the MCP payload publishes it, and
keep the provenance coverage report synchronized.
