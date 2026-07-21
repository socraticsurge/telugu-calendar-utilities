# Gochara Source Crosswalk

## Verified layer

The seven classical Grahas' favourable transit houses are verified against
Varahamihira's *Brihat Samhita*, Chapter 104, stanza 4, in the N. Chidambaram
Iyer translation (1884). The stanza lists each Graha's favourable houses from
Janma Chandra and concludes that every Graha is favourable in the 11th.

| Graha | Implemented favourable houses | How stanza 4 supports the set |
|---|---|---|
| Surya | 3, 6, 10, 11 | 3, 6 and 10 listed; 11 supplied by the concluding rule |
| Chandra | 1, 3, 6, 7, 10, 11 | 1, 3, 6, 7 and 10 listed; 11 supplied by the concluding rule |
| Mangala | 3, 6, 11 | 3 and 6 listed; 11 supplied by the concluding rule |
| Budha | 2, 4, 6, 8, 10, 11 | 2, 4, 6, 8 and 10 listed; 11 supplied by the concluding rule |
| Guru | 2, 5, 7, 9, 11 | 2, 5, 7 and 9 listed; 11 supplied by the concluding rule |
| Shukra | 1, 2, 3, 4, 5, 8, 9, 11, 12 | 6, 7 and 10 called malefic; 11 supplied by the concluding rule |
| Shani | 3, 6, 11 | 3 and 6 listed; 11 supplied by the concluding rule |

The ledger claim is `gochara.favourable_houses`. This verifies the table, not
every interpretive sentence produced from it.

## Verified Vedha layer

Mantreswara's *Phaladeepika*, Adhyaya XXVI, slokas 3–8, states the favourable
houses and their corresponding Vedha houses planet by planet. The same passage
explicitly exempts Shani from obstructing Surya, Surya from obstructing Shani,
Budha from obstructing Chandra, and Chandra from obstructing Budha. The
consolidated table and father–son explanation also appear in *Jataka Parijata*,
Volume III, Adhyaya XIII, note to sloka 60, printed pages 833–834.

| Graha | Implemented favourable → Vedha pairs | Phaladeepika locator |
|---|---|---|
| Surya | 3→9, 6→12, 10→4, 11→5 | XXVI.3 |
| Chandra | 1→5, 3→9, 6→12, 7→2, 10→4, 11→8 | XXVI.4 |
| Kuja | 3→12, 6→9, 11→5 | XXVI.5 |
| Budha | 2→5, 4→3, 6→9, 8→1, 10→8, 11→12 | XXVI.6 |
| Guru | 2→12, 5→4, 7→3, 9→10, 11→8 | XXVI.7 |
| Shukra | 1→8, 2→7, 3→1, 4→10, 5→9, 8→5, 9→11, 11→6, 12→3 | XXVI.8 |
| Shani | 3→12, 6→9, 11→5 | XXVI.5 |

The ledger claim is `gochara.vedha_tables`. This verification stops at the
seven classical Grahas; it does not silently authorize the project's node
policy.

## Known node conflict

*Phaladeepika* XXVI.2 concludes that Rahu and Ketu are to be treated like
Surya. That makes houses 3, 6, 10 and 11 favourable. The implementation instead
copies Shani's set, 3, 6 and 11, so it incorrectly marks a node in the 10th as
adverse under this cited authority. The `gochara.nodes` claim is therefore
`contradicted`, not merely unsupported.

This locator does not say whether Rahu or Ketu causes or receives Vedha. The
current no-node-Vedha behavior remains an unverified sub-rule and must not be
presented as disproven by XXVI.2.

Changing the node calculation would alter an existing tested assertion. Under
the frozen-contract working agreement, this audit records the conflict and
leaves behavior unchanged pending explicit owner approval.

## Layer still requiring a locator

| Layer | Claim | State | Boundary |
|---|---|---|---|
| Named Shani conditions | `gochara.named_shani_conditions` | `needs_locator` | Chapter 104 describes house effects but does not name the configured Sade Sati phases, Ashtama Shani or Ardhastama Shani |

The MCP response publishes all four claim IDs and explains the split. Product
copy must not describe the entire verdict system as “the Brihat Samhita table,”
or imply that verified Vedha evidence also settles the two open layers.

## Engineering consequence

No calculation changed in this audit. Exact table tests bind the classical
source crosswalk to the implementation, while each adjacent conventional layer
retains its own status and can be promoted without rewriting the calculation
contract.
