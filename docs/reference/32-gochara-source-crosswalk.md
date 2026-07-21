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

## Layers not supported by that citation

| Layer | Claim | State | Boundary |
|---|---|---|---|
| Vedha table and exemptions | `gochara.vedha_tables` | `needs_locator` | Chapter 104 does not provide the configured obstruction map or father-son exemptions |
| Rahu/Ketu treatment | `gochara.nodes` | `needs_locator` | Stanza 4 addresses the seven classical Grahas; it does not authorize copying Shani's houses or disabling node Vedha |
| Named Shani conditions | `gochara.named_shani_conditions` | `needs_locator` | Chapter 104 describes house effects but does not name the configured Sade Sati phases, Ashtama Shani or Ardhastama Shani |

The MCP response publishes all four claim IDs and explains the split. Product
copy must not describe the entire verdict system as “the Brihat Samhita table.”

## Engineering consequence

No calculation changed in this audit. The change removes authority laundering:
one verified table can no longer make adjacent conventional rules appear
verified. Future evidence work can promote each layer independently without
rewriting the calculation contract.
