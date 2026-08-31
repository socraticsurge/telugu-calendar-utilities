# Guest birth profiles and the D1 Rashi chart

This page explains the birth-details calculation used by guest Profiles. It is
for people checking what leaves the browser, how Nakshatra and the chart are
derived, and what “verified” does and does not mean.

> **Current assurance:** documented, traceable, and reproduced through a second
> formula path. The three fixture cells are not an independent published-chart
> comparison because both paths use Swiss Ephemeris. Public activation remains
> gated on the licensing and time-ambiguity items below.

> **Activation state:** the birth-details interface and network adapter are on
> by default only for loopback development. A public build must set
> `VITE_BIRTH_PROFILE_API_ENABLED=true`, where `true` is the exact,
> case-sensitive value; every other explicit value fails closed. When inactive,
> Profiles defaults to manual entry and keeps existing calculated profiles
> viewable without permitting recalculation or editing.

## Meaning

A birth profile turns an exact local date, time, and selected birthplace into:

- Janma Nakshatra and Padam;
- Janma Rashi;
- Lagna and its degree within the Rashi;
- the sidereal Rashi and Whole Sign house of Surya, Chandra, Kuja, Budha, Guru,
  Shukra, Shani, mean Rahu, and Ketu; and
- a South Indian D1 Rashi chart.

The profile reuses Nakshatra and Padam in Muhurtam and Daily Horoscope. The D1
chart is a positional reference only. This contract does not return Dasha,
Yoga, compatibility, predictions, or interpretive claims from DashaFlow.

## Inputs and privacy boundary

| Input | Where it goes | Why |
|---|---|---|
| Profile name | Browser storage only | A local label for recognizing the person; it is rejected by the calculation gateway. |
| Place search text | Astro Chaganti gateway, then the geocoder | Returns at most five selectable places. Use a city or town, not a street address. |
| Selected latitude, longitude, and IANA timezone | Astro Chaganti gateway and DashaFlow sidecar | Resolves the birth instant and location-dependent ascendant. |
| Local date and exact local time | Astro Chaganti gateway and DashaFlow sidecar | Resolves the UTC instant used by the ephemeris. |
| Calculated result and original inputs | Origin-scoped browser `localStorage` | Reuses the profile without an account or repeated calculation. |

When the capability is active, the browser calls the server only after
**Find place** or **Calculate details**.
Application code does not create an Astro Chaganti account, database row, or
analytics event from these values. Network and hosting providers necessarily
process requests in transit; do not interpret “browser-local profile” as “no
network calculation.” There is no cloud sync or recovery.

```mermaid
flowchart LR
  UI["Panchangam static UI"] -->|"place text only"| PLACE["Astro guest place route"]
  PLACE --> GEO["Nominatim search"]
  PLACE --> TZ["offline coordinate-to-timezone lookup"]
  UI -->|"date, time, coordinates, timezone; no name"| GATEWAY["Astro guest profile route"]
  GATEWAY -->|"server bearer credential"| SIDE["DashaFlow sidecar v1 contract"]
  SIDE --> CALC["DashaFlow 1.1.0 + PySwissEph"]
  CALC -->|"narrow result; no raw input echo"| UI
  UI --> STORE["browser profile storage"]
```

The Astro gateway permits the Panchangam production origin and HTTP localhost
origins, caps bodies at 4 KiB, rate-limits requests, and marks responses
`private, no-store`. Its DashaFlow bearer token is server-only and must never be
placed in browser code or a `VITE_*` variable.

The build flag is not authorization and contains no secret. A public page uses
only the canonical `https://astrochaganti.com/api/guest` HTTPS gateway; a
loopback or arbitrary configured base is rejected. Public activation requires
both the exact client flag and independently enabled server-side routes. The
server must remain disabled until the licensing and provider gates below are
resolved. A disabled browser adapter throws a typed `disabled` error before it
creates a timeout or calls `fetch`.

## Local storage transaction

Calculated profiles use a three-key browser transaction: the legacy-compatible
base profile array, a revision-bound birth-data envelope, and a commit marker.
The marker is written last and records both the revision and the exact base
payload. A reader attaches birth data only when all three values agree; base or
envelope events observed before the marker therefore load fail-closed without
attaching a mismatched chart.

If any write fails, the store does not automatically delete or roll back keys:
multi-key `localStorage` has no atomic fence that could prevent such cleanup
from overwriting a newer tab. Existing companion bytes remain untouched until
their own write step; an absent or mismatching marker keeps every partial new
base or envelope detached.

When the base key is absent, confirmed recovery is offered only when every
present companion exactly matches the store's current recognized format; when
both companions are present, their revision and base relationships must also
agree. This is conservative format recognition, not proof of which code wrote
the bytes. Unrecognized or future-format bytes remain read-only. A base-present
torn transaction can be replaced only by an explicit user reset or later
successful save. The failure points, cross-tab boundary, and orphan rules are
pinned in
[`src/__tests__/guest-profile-store.test.ts`](https://github.com/socraticsurge/telugu-calendar-utilities/blob/master/src/__tests__/guest-profile-store.test.ts).

## Calculation process

### 1. Resolve the birth instant

The exact `YYYY-MM-DD` date and `HH:MM` time are interpreted as local civil time
in the selected IANA timezone. DashaFlow converts that value to UTC and then to
a Universal-Time Julian day:

```text
local civil date/time + IANA timezone
  -> timezone-aware local instant
  -> UTC instant
  -> Julian day UT
```

The IANA identifier matters because a numeric offset alone cannot represent
historical daylight-saving and government rule changes.

### 2. Select the astronomical convention

DashaFlow explicitly selects Lahiri sidereal mode and uses:

```text
FLG_SIDEREAL | FLG_SPEED
```

for the graha positions. The positions are geocentric; this contract does not
set the topocentric flag. Swiss Ephemeris documentation requires the sidereal
flag and an explicit sidereal mode for a chosen ayanamsha.

The returned `engine.ephemeris` is read from the actual Swiss Ephemeris return
flags. It is `swiss`, `moshier`, or `unknown`. It is never inferred from the
requested flags or package name. Swiss Ephemeris can fall back to Moshier when
the requested data files are not present, which is why this disclosure is part
of every saved profile.

Technical reference: [Swiss Ephemeris Programmer's Documentation](https://www.astro.com/swisseph/swephprg.htm),
sections 3, 12, and 15.4.

### 3. Derive Nakshatra, Padam, and Janma Rashi

Let `M` be the normalized sidereal Moon longitude in `[0°, 360°)`.

```text
nakshatra_span = 360° / 27
pada_span       = 360° / 108

nakshatra_index = floor(M / nakshatra_span)
degree_in_star  = M - nakshatra_index * nakshatra_span
pada            = floor(degree_in_star / pada_span) + 1
janma_rashi     = floor(M / 30°)
```

Indices select the canonical 27-Nakshatra and 12-Rashi name tables. The sidecar
normalizes DashaFlow spellings such as `Ashwini` and `Dhanishta` to the existing
Panchangam vocabulary `Ashvini` and `Dhanishtha`.

### 4. Derive Lagna and Whole Sign houses

The ascendant is the first value in `ascmc` returned by:

```text
houses_ex(julian_day_ut, latitude, longitude, "W", sidereal_flags)
```

`W` is the Whole Sign house method. If `L` is the Lagna Rashi index and `P` is a
graha's Rashi index, the house number is:

```text
house = ((P - L) mod 12) + 1
```

The [Swiss house-function reference](https://www.astro.com/swisseph/swephprg.htm)
supports the UT, coordinate, sidereal-flag, and house-method API semantics. It
does not by itself establish a textual Jyotisha authority for choosing Lahiri
or Whole Sign houses; those are explicit product conventions.

### 5. Derive the nine displayed grahas

`calc_ut` supplies Surya, Chandra, Kuja, Budha, Guru, Shukra, Shani, and mean
Rahu. Ketu is placed exactly 180° from Rahu:

```text
ketu_longitude = (rahu_longitude + 180°) mod 360°
```

Surya and Chandra are always represented as direct. Rahu and Ketu are always
represented as retrograde. The other grahas are retrograde when their returned
longitudinal speed is negative. Degrees within a Rashi are rounded to two
decimal places for this contract.

## Reproduction fixture

The repository pins three synthetic cells across India, North America, and
Europe in [`tests/fixtures/birth_profile_reference.json`](../../tests/fixtures/birth_profile_reference.json).
For example:

| Input | Reproduced result |
|---|---|
| 1990-04-15 14:30, Hyderabad, `Asia/Kolkata` | Jyeshtha, Padam 4; Vrischika Janma Rashi; Simha Lagna 4.69°; Moshier |

`tests/test_birth_profile_reference.py` recomputes the narrow contract directly
with PySwissEph without importing DashaFlow. That protects the time conversion,
longitude partitions, Ketu rule, Whole Sign house rule, canonical names, and
two-decimal projection against drift.

Run:

```bash
.venv/bin/python -m pytest tests/test_birth_profile_reference.py -q
npm test
```

This is **reproduction checked**, not independently source-compared. A future
comparison must name the external chart, its exact input cell, ayanamsha, node,
house, ephemeris, and timezone conventions rather than comparing labels alone.

## Known limitations and release gates

1. **Swiss Ephemeris licensing:** Astrodienst requires a developer to choose
   AGPL-compatible licensing or a Professional License before distributing a
   derived application or activating a public service. Its current professional
   contract explicitly covers browser clients that request server-side
   calculations. Public activation is blocked until the owner records the
   applicable choice. See [Astrodienst's licensing page](https://www.astro.com/swisseph/swisseph.htm)
   and [Professional License contract](https://www.astro.com/swisseph/secont_e.pdf).
   The owner decision is tracked in
   [#231](https://github.com/socraticsurge/telugu-calendar-utilities/issues/231).
2. **Actual ephemeris:** current local fixture calls report Moshier because the
   deployed data-file posture has not been approved. Production must probe and
   disclose its own actual return flags; it must not promise Swiss data-file
   output merely because PySwissEph is installed.
3. **DST ambiguity:** DashaFlow 1.1.0 itself calls `pytz.localize` without the
   fail-closed `is_dst=None` option. The authenticated sidecar contract therefore
   validates the complete local civil time first and rejects repeated or skipped
   wall times instead of letting the library choose a side. Guests with one of
   these unusual recorded times must use manual profile entry until an explicit
   first/second-occurrence choice is supported. The
   [pytz documentation](https://pythonhosted.org/pytz/) describes this boundary.
4. **Historical timezones:** the IANA database itself warns that many pre-1970
   records represent only part of a region and are not authoritative everywhere.
   See [IANA timezone theory and limitations](https://www.iana.org/time-zones/theory).
5. **Place search policy:** the public Nominatim service prohibits client-side
   autocomplete and personal/confidential submissions. This UI uses an explicit
   submit action and asks for city/town only. Production usage must continue to
   follow the [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/)
   or move to an approved provider/self-hosted service. Provider and cache
   approval is tracked in
   [#233](https://github.com/socraticsurge/telugu-calendar-utilities/issues/233).
6. **Birth-time sensitivity:** a small time difference can change Lagna near a
   boundary. The current calculated path accepts exact recorded time only. An
   unknown or approximate time must use manual entry; no precise Lagna is
   fabricated.
7. **Storage scope:** browser data is visible to anyone using the same browser
   profile and origin. Clearing site data, changing domain/port, or using another
   device loses access. There is no recovery.

## Implementation ownership and review triggers

| Layer | Owner | Tests |
|---|---|---|
| Browser API validation | `src/lib/birth-profile-api.ts` | `src/__tests__/birth-profile-api.test.ts` |
| Public/local activation policy | `src/lib/remote-calculation-activation.ts` | `src/__tests__/remote-calculation-activation.test.ts` |
| Commit-bound fail-closed local storage | `src/lib/guest-profile-store.ts` | `src/__tests__/guest-profile-store.test.ts` |
| Profile form, review, and D1 chart | `src/panels/profiles.ts` | `src/__tests__/profiles-panel.test.ts`, browser smoke tests |
| Public stateless gateway | `astro-unified-core` guest API routes | route, CORS, rate-limit, body-cap, and contract tests in that repository |
| Authenticated calculation projection | `dashaflow-sidecar/api/profile.py` | sidecar profile-contract tests |

Review this page when any contract version, DashaFlow/PySwissEph version,
ayanamsha, node choice, house method, timezone package/data, place provider,
rounding rule, storage schema, actual ephemeris, or privacy boundary changes.
