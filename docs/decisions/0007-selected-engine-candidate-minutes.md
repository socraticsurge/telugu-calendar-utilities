# Selected-engine candidate-minute data: producer stage

## Decision (#182)

Generate a static table of selected-engine facts for **every UTC minute** in the
feed window, then losslessly run-length encode consecutive identical values.
The producer queries the existing public `PanchangamEngine.facts_at` owner for
Nakshatra, Tithi, Yoga, Karana and lunar Rashi. The existing additive
`personal.homa.solar_nakshatra_at` supplies the selected-engine solar Nakshatra.
No frozen engine is modified and no new astronomical formula is introduced.

The six facts are geocentric in the current engines, so one table serves all
cities. The placeholder location and Vaaram supplied during generation do not
enter these six outputs; consumer-day Vaaram and special Yogas will be handled by
the later browser adapter. Tests compare public results from Hyderabad and New
York for every minute of two explicit dates and three reproducibly sampled
dates across the 550-day horizon for all three engines.

## Discrete contract

The table represents `[startMinute, endMinute)` in integer Unix UTC minutes.
Every represented minute is evaluated. Rows contain the offset from the start and
the six names in the declared `fields` order; a row applies until the next row.
`schemaVersion: 1`, `stepSeconds: 60`, and the Python system identity are explicit.
Bounds must be aware whole-minute instants; accepted non-UTC bounds are normalized
to UTC before stepping, including across DST folds/gaps.

This is not a sparse transition solver or interpolation of continuous event
instants. In particular, the model's Vakya discontinuity at 2027-08-05 18:56:55 UTC
is handled by independently querying both adjacent candidate minutes. Tests
protect those minutes. Subminute queries are outside the proposed browser
contract and must be rejected, never rounded. Evidence limitations of the selected
engine remain unchanged, including provisional Vakya historical calibration.
Fixtures prove engine consumption parity, not independent ephemeris accuracy.

## Generation, delivery and staged activation

Generation writes one `<system>.slot-facts-v1.json` before each system's city loop.
The range extends from UTC midnight one day before the first feed date through
two days after the last date. Existing city feeds and ICS bytes remain unchanged.
The existing landing-build copier stages the new suffix. Workflows, security
settings and CNAME remain unchanged.

This PR is producer-only: the browser continues its existing behavior. After it
merges, run the existing `generate.yml` workflow on master and verify all three
hosted tables, their identities/ranges and unchanged existing feed retention.
Only then may the separate browser-consumer PR be published. The producer alone
does not complete #182.

A local 550-day measurement evaluated 792,000 minutes for each system, including
solar Nakshatra. Drik took 28.67s, Surya Siddhanta 7.33s and Vakya 7.24s; combined
output was 581,885 bytes raw and 65,720 bytes gzip. Each table has about 2,465 rows.
These are measured local costs, not a CI guarantee. There is no per-city multiplier.
The later consumer can reuse one selected-system table and existing browser HTTP
caching; uncached offline use must fail clearly instead of substituting approximate
facts. Existing chart-screening frame disclosures remain unchanged.
