# Rise/set convention research and solar decision (#177)

Date: 2026-09-19. Decision: retain the existing astronomical upper-limb,
atmospheric-refraction convention for the product's Drik Panchang comparison
target. No frozen calculation code or published timing changes.

## Evidence and scope

[Drik Panchang's own definition](https://www.drikpanchang.com/panchang/sunrise/panchang-sunrise.html)
identifies its default as the upper edge with refraction; elevation is disabled
by default. [Swiss Ephemeris](https://www.astro.com/swisseph/swephprg.htm),
sections 8.12 and 8.12.1, distinguishes that default from `BIT_HINDU_RISING`
(disc centre, no refraction, geocentric, without ecliptic latitude).
The latter is a different convention, not a universal requirement for every
Panchangam product.

Four independently revisited rendered day pages cover Hyderabad on January 1
and March 13, and New York on January 1 and May 4, 2026. New York includes
standard and daylight-saving time. The minute-precision values and exact URLs
are in `tests/fixtures/rise_set_convention_oracle.json`.

| City/date | Published rise/set | Current rise/set | Alternate Hindu rise/set |
|---|---|---|---|
| Hyderabad 2026-01-01 | 06:46 / 17:53 | 06:46:10 / 17:52:54 | 06:49:58 / 17:49:06 |
| Hyderabad 2026-03-13 | 06:26 / 18:26 | 06:25:53 / 18:25:25 | 06:29:21 / 18:21:57 |
| New York 2026-01-01 | 07:20 / 16:39 | 07:20:06 / 16:39:24 | 07:25:11 / 16:34:19 |
| New York 2026-05-04 | 05:51 / 19:55 | 05:50:53 / 19:55:18 | 05:55:32 / 19:50:37 |

Current maximum absolute difference is 35 seconds across these eight points;
the test allows 120 seconds because published times have minute precision and
the repository and source city coordinates differ. This is a solar comparison,
not an all-location certification.

## Moon comparison: a separate correction remains open

The same four rendered day pages were separately inspected for their Moon
events, including explicit next-day suffixes. The source's solar definition
must not be assumed to describe its Moon calculation. These eight labeled
Moon events differ from the current default by 231–381 seconds. A controlled
Swiss comparison using `BIT_DISC_CENTER | BIT_NO_REFRACTION`, retaining
topocentric position and lunar ecliptic latitude, agrees within 33 seconds.

| Page city/date | Published Moon rise/set | Current default | Disc centre, no refraction |
|---|---|---|---|
| Hyderabad 2026-01-01 | 15:43 / 05:26 Jan 2 | 15:38:57 / 05:29:51 Jan 2 | 15:43:07 / 05:25:38 Jan 2 |
| Hyderabad 2026-03-13 | 03:02 Mar 14 / 13:13 | 02:57:56 Mar 14 / 13:17:17 | 03:01:53 Mar 14 / 13:13:17 |
| New York 2026-01-01 | 14:39 / 06:47 Jan 2 | 14:32:39 / 06:52:48 Jan 2 | 14:38:27 / 06:46:57 Jan 2 |
| New York 2026-05-04 | 23:24 / 07:03 | 23:18:25 / 07:08:34 | 23:24:05 / 07:03:01 |

This is an empirical candidate convention, not a claim that Drik Panchang
publishes its internal lunar flags. Applying the full `BIT_HINDU_RISING`
combination instead also changes parallax and ecliptic-latitude treatment;
it differs by as much as 32 minutes 16 seconds in these samples. The Swiss
section 8.12.1 Hindu discussion is specifically about the Sun.

`tests/fixtures/moon_rise_set_convention_oracle.json` and
`tests/test_moon_rise_set_convention.py` preserve the independent values and
reproduce all three mode comparisons. They search from midnight of each
**printed event's civil date**. A Panchang page may select a next-day event
before sunrise, whereas the current engine starts its Moon search at the
requested civil midnight. This fixture does not certify that day-assignment
policy or silently change it.

Keep #177 open for an owner-reviewed lunar convention decision and frozen-core
correction. All three engines consume the shared Moon helpers; Moonrise also
determines Sankashti's deciding instant. A future patch must review boundary
date impacts, the protected helper-flag assertions and generated calendar
corpus, then receive explicit approval and a versioned release. Moonset has
no festival caller. Eclipse visibility uses a separate altitude calculation
and must not be conflated with this change.

## Observer and error experiments

Swiss Ephemeris 2.10.03 tests retain the existing fixed 1013.25 hPa, 15 C,
zero-altitude input policy. Hyderabad altitude 531 m alone changes these solar
events by less than one second at fixed pressure. Automatic pressure at that
altitude changes them by about ten seconds; zero-degree air changes them by
about fourteen seconds. These are controlled sensitivity experiments, not
proof of actual weather or a general altitude-correction model.

At Tromso on both solstices, solar rise/set return status `-2` and a zero
placeholder, not a usable instant. An invalid body raises `swisseph.Error`.
The frozen helper ignores status today; polar no-event handling remains
unsupported and must not be advertised as solved. The new tests exercise the
Swiss contract directly rather than pinning the helper's unsafe placeholder
as correct behavior. A future guard requires explicit frozen-core approval.

## Verification and decision boundary

Run `python -m pytest tests/test_rise_set_convention.py` to reproduce the oracle,
alternative-mode, atmosphere and status experiments without a network request.
The fixture records independent source values; expected values are not generated
from the implementation. No PyPI bump is needed for this research-only change.
Keep the broad provenance claim `partially_verified`: the solar default is
decided, while the lunar discrepancy and polar output safety remain unresolved.
