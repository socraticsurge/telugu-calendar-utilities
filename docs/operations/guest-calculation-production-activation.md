# Guest calculation production activation

Status: **Production backend verified; paired public client activation approved**
Assessment timestamp: `2026-09-04T15:50:00+05:30` (`Asia/Kolkata`)
Release refresh: `2026-09-04` (`Asia/Kolkata`)
Panchangam pre-activation baseline: `99629ada`
Epic: [#234](https://github.com/socraticsurge/telugu-calendar-utilities/issues/234)

This is the operator runbook and release record for guest birth-profile
calculation and Muhurtam election-chart screening. The owner approved the
AGPL-compatible public-source path and paired public activation on 2026-09-04
after the exact Production backend passed the bounded probes below. The
evidence and rollback checks still apply to every release and rollback step.

Refresh this record immediately before any Preview, merge, deployment, or
activation approval. Reconfirm branch heads, CI/security check URLs, exact
Vercel deployment IDs, environment-name inventories, public probes, and restore
refs; the values below are a dated assessment, not perpetual release evidence.

## Current state

| Component | State |
|---|---|
| Panchangam profile/Muhurtam UI | The reviewed production build sets both remote client flags to exact `true`; PR #452 is the paired client activation and requires a manual `Deploy Landing Page` dispatch because `.env.production` is outside the workflow's push paths. |
| Astro guest routes | Production deployment `dpl_G49CJ75b1YsLCR872fbaptpEiGPe` is Ready at exact public commit `4106f097`; health, birth, election-chart, and governed place-search probes passed. |
| DashaFlow authenticated contracts | Production deployment `dpl_DmZ3sEMEvtCMo7EGpY7zRtEP2ySJ` at public commit `c84fd856` served the authenticated synthetic birth and election-chart derivations through Astro. The browser never receives the sidecar credential. |
| Panchangam release posture | PR #456 merged normally at `99629ada`; tag `v1.14.0` publishes the reviewed AGPL/source package and release evidence. |
| Licensing | The relevant repositories are public and the reviewed TCU source/package posture is AGPL-3.0-or-later with direct PySwissEph and Swiss Ephemeris notices. |
| Production geocoder/shared controls | Keyless public Nominatim is active on the shared governed path. A bounded Hyderabad search returned 200. In a 65-attempt `/api/guest/` probe from one client, 60 were admitted and the subsequent five returned edge 429 without creating an application draft. |
| Rollback | Preserve the exact pre-activation TCU master archive created from `99629ada` and the existing Pages archive `archive/pre-public-activation-2026-09-04-gh-pages-79c907d`. |

## Cleared activation evidence

- The owner selected and approved the public AGPL-compatible source posture,
  Production backend, and paired birth/election client activation.
- Astro Production is Ready at exact public source `4106f097` and immutable
  deployment `dpl_G49CJ75b1YsLCR872fbaptpEiGPe`.
- A Hyderabad Production place search returned 200 with the governed Nominatim
  provider. The WAF probe admitted 60 requests from one client, then the next
  five returned edge 429 without creating an application draft.
- Synthetic birth derivation returned 200 with Jyeshtha Padam 4, Vrischika and
  Simha; synthetic election-chart derivation returned 200.
- TCU schema-v1 compatibility was restored by #458 before the versioned
  release, and #456 passed the full Python 3.10-3.13/security gates before its
  normal merge.
- The paired client activation is pinned by
  `tests/test_production_activation_flags.py`; both exact production flags,
  the deploy run, the resulting `gh-pages` tip, and live browser/API probes
  must be recorded on #452 and epic #234.

## Version record

Fill this table without secret values.

Do not reuse one value for production, candidate, or rollback. Record immutable
deployment IDs rather than mutable aliases.

| Layer | Current Production commit | Candidate runtime/code commit | Restore ref | Preview deployment ID | Production deployment ID | CI/security evidence |
|---|---|---|---|---|---|---|
| Panchangam | `99629ada` before client activation | PR #452, both production client flags exact `true` | New immutable archive at exact `99629ada`; existing Pages archive `archive/pre-public-activation-2026-09-04-gh-pages-79c907d` | Local production build and fixture-backed browser review | Manual `Deploy Landing Page` run from exact merged #452 revision | PR #456: full local suite 1,466 passed/1 skipped, full build/docs passed, and required Python 3.10-3.13, CodeQL, pip-audit and Sonar checks passed; #452 requires the same final-head gates. |
| Astro | `4106f097` | same exact Production source revision | Repository/archive and Vercel instant rollback retained by the Astro release record | Earlier protected pair remains recorded in #448 | `dpl_G49CJ75b1YsLCR872fbaptpEiGPe` (Ready) | Health 200; governed Hyderabad search 200; synthetic birth and election charts 200; WAF admitted 60 requests before five subsequent edge 429 responses. |
| DashaFlow | `c84fd856` | same exact released Production source revision | Retained by the DashaFlow/Astro release record | Exact-token protected Preview evidence remains in #448 | `dpl_DmZ3sEMEvtCMo7EGpY7zRtEP2ySJ` (Ready) | Synthetic birth and election calls passed through the Production gateway with DashaFlow 1.1.0 and disclosed Moshier ephemeris; no browser credential exists. |

## Environment names and implementation state

These are names only. Never record values here, in issues, or in browser code.

| Owner | Current implemented name | Current boundary |
|---|---|---|
| Panchangam build | `VITE_BIRTH_PROFILE_API_ENABLED` | exact `true`; exercise independently |
| Panchangam build | `VITE_ELECTION_CHART_API_ENABLED` | exact `true`; exercise independently |
| Panchangam build | `VITE_BIRTH_PROFILE_API_BASE` | implemented, but a deployed build accepts only the canonical Production Astro base; it cannot target a hosted Preview today |
| Panchangam build | `VITE_ELECTION_CHART_API_BASE` | same deployed-host restriction; it cannot target a hosted Preview today |
| Astro | `GUEST_BIRTH_PROFILE_ENABLED` | exact `true`; deployed/ambiguous runtimes otherwise fail closed |
| Astro | `GUEST_ELECTION_CHART_ENABLED` | exact `true`; deployed/ambiguous runtimes otherwise fail closed |
| Astro | `DASHAFLOW_SIDECAR_URL` | approved HTTPS service only when deployed |
| Astro | `DASHAFLOW_SIDECAR_TOKEN` | server-only credential sent by Astro |
| DashaFlow | `DASHAFLOW_API_TOKEN` | server-only verifier; its value must match Astro's differently named token |
| Astro | `GEOCODER_PROVIDER` | Fixed to `nominatim-public` in Production after owner approval. Preview and real local development reject it and use fixtures. |
| Astro | `GEOCODER_API_KEY` | Must be absent for `nominatim-public`; a key is needed only if a dormant commercial adapter is selected in a later reviewed release. |
| Astro | `GEOCODER_DAILY_REQUEST_LIMIT` | Set a canonical value no greater than `1000` for public Nominatim. Guest and managed signed-in cache misses share the same Production provider row. |
| Astro | `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED` | Exact `true` in Production so signed-in and guest calls share one governed path. Preview remains fixture-only. |
| Astro | `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | Existing database used for pseudonymous client/user/fleet counters and one non-personal provider-budget/lease row. No place query or result is stored there. |
| Astro | `RATE_LIMIT_HMAC_SECRET` | Existing server-only HMAC secret for pseudonymous client/user/fleet counter keys. |
| Astro runtime | `VERCEL_ENV`, `VERCEL`, `NODE_ENV` | implementation classifies only consistent explicit local or deployed markers; missing, unknown, self-hosted-production, or contradictory markers fail closed |

The selected provider contract is live in Astro Production. Public
Nominatim is fixed and keyless; no LocationIQ, Geoapify, Upstash, or Redis
account is required. It is intentionally unavailable in Preview and real local
development, where provider behavior is fixture-tested. Production guest and
signed-in place search share one Turso-backed budget and send lease; missing or
inconsistent runtime/configuration signals still fail closed.

### Place-search retention and quota contract

| Boundary | Permitted data | Retention / verification gate |
|---|---|---|
| Panchangam browser request | Trimmed city/town query only; no profile name, cookie, birth date/time, or chart | Transient request state; browser network evidence required |
| Astro process state | Ephemeral HMAC client pseudonym; SHA-256 request key; at most five normalized provider rows | Bounded 256-entry process cache with a 24-hour TTL; no shared result cache |
| Turso limiter tables | Environment-scoped HMAC client/user/fleet keys plus one provider-family hash and integer count/timing fields | Window/day rollover and bounded cleanup; no raw query, result, IP, user ID, birth detail, coordinate, or credential |
| Public Nominatim | Deliberately submitted city/town query and Astro's server egress metadata; no profile name, birth date/time, or provider credential | Provider-controlled under the linked Nominatim and OSMF policies; one bounded Production smoke query only after approval |
| Sentry / application analytics | No request bodies, raw place query, provider URL query/key, birth payload, or chart | Verify configuration and inspect Preview events before activation |

The geocoder fleet ceiling is 30 calls per minute, shared by guest place search
and the activated signed-in migration. The managed signed-in path also applies
a ten-call-per-user minute limit. Public Nominatim adds a code-capped
1,000-attempt UTC-day budget and one exclusive 12,500 ms crash-recovery lease;
normal completion establishes a fenced 1,100 ms cooldown before the next
distributed send. When public Nominatim returns `429`, a bounded numeric or
HTTP-date `Retry-After` replaces that normal cooldown fleet-wide through the
same exact-fence update, up to 24 hours. Missing, malformed, past, or zero-delay
guidance becomes 60 seconds. Guest place search applies a durable 50-request
allowance of valid managed-provider cache misses per client and anchored
24-hour window. It runs after the five-per-minute guard, validation, cache
lookup, and duplicate coalescing and has its own bounded two-second storage
deadline. Malformed requests and reusable results do not spend it, though
malformed requests may already spend the earlier route capacity, fleet, and
minute guards. Fifty is nominally 5% of the configured pool and prevents one
client identity from exhausting the provider's UTC-day allowance. Because the
client window is anchored rather than UTC-aligned, a boundary overlap can reach
100 upstream attempts in one UTC day. Warm-process cache hits and coalesced
duplicate callers spend no provider slot. These controls implement the public
service's absolute one-request/second application ceiling; they are not a
purchased quota or availability guarantee.

For Turso capacity planning, a successful guest place cache miss uses five
admission-path row mutations: the capacity, fleet, minute-client, anchored
daily-client, and provider-reservation rows. The conditional exact-fence
completion update is accounted separately. Any four-write guest-place estimate
predates the anchored daily-client guard and is no longer valid.

## Production evidence sequence

The protected Astro/DashaFlow pair first passed exact-token contracts against
an isolated staging Turso database. The owner then approved and verified the
exact Production backend before the paired public client release. Public
Nominatim remains intentionally unavailable outside Production; do not weaken
CORS, expose a protection credential to browser JavaScript, or point a hosted
Preview browser at Production.

1. Astro Production deployment `dpl_G49CJ75b1YsLCR872fbaptpEiGPe` at public
   source `4106f097` reported Ready and health returned 200.
2. The governed Production Nominatim path returned a bounded Hyderabad result
   with attribution. The perimeter probe admitted 60 requests from one client;
   the subsequent five returned edge 429 without an application draft.
3. Synthetic Production birth and election requests both returned 200; the
   birth fixture resolved to Jyeshtha Padam 4, Vrischika and Simha.
4. TCU `v1.14.0` publishes the reviewed source/licence posture from exact
   pre-activation master `99629ada`.
5. PR #452 sets both client flags together, pins them in a release-contract
   test, preserves the pre-activation master and Pages refs, and requires a
   manual landing-page deployment plus live browser verification.

## Failure matrix

| Failure | Expected behavior |
|---|---|
| Client flag absent/malformed | No remote call; manual profile entry or conservative unscreened Muhurtam result |
| Astro route flag off | Fixed 503; no geocoder/sidecar call |
| Shared Turso limiter missing/unavailable in Preview/Production | Fixed 503; no expensive calculation/provider call |
| Production geocoder configuration missing/unavailable | Place search 503; no arbitrary or commercial fallback |
| Guest client exceeds 50 valid managed-provider place-search misses in its anchored 24-hour window | Sanitized 429 with durable client-window retry guidance; no provider call |
| Public Nominatim returns 429 | Sanitized 429; bounded upstream retry guidance is persisted fleet-wide through exact-fence completion. Missing, malformed, past, or zero-delay guidance becomes 60 seconds; the maximum is 24 hours |
| Authenticated migration flag absent/false | Production preserves its old unbudgeted signed-in Nominatim path; Preview fails closed. Never use this as a Nominatim incident rollback. |
| Authenticated migration exact `true`, provider/limit unavailable | Signed-in place-changing operation fails closed; no legacy or commercial fallback and no profile mutation |
| Sidecar token missing/bad | Fixed gateway error; no upstream diagnostic or token in response |
| Sidecar timeout/transient error | Up to two bounded attempts within the browser deadline, with one retry only for 502/503/504, then a fixed unavailable result |
| Malformed/inconsistent chart | 502/invalid response; never save or score as verified |
| Unsupported or ambiguous civil time | 422; offer manual entry |

## Merge and Production sequence

Backend readiness and paired activation have separate evidence, even though the
owner approved both public client capabilities in the same release.

1. Keep Astro at the exact verified Production revision and keep both routes
   independently fail-closed when their server configuration is absent.
2. Publish and verify TCU `v1.14.0` from exact merge `99629ada` before the
   client activation merge.
3. Create an immutable archive at `99629ada`, retain the existing `gh-pages`
   archive at `79c907d`, then merge #452 normally only after its final-head
   Python 3.10-3.13 and security checks pass.
4. Manually dispatch `Deploy Landing Page` on the merged #452 master revision;
   the production environment file is deliberately outside the push path
   filters.
5. Record the resulting workflow run and `gh-pages` tip, then verify the public
   page, visible OpenStreetMap attribution, synthetic birth derivation and
   election-chart screening from a cache-busted browser session.

Publishing uses the existing manual `Deploy Landing Page` workflow dispatch
because the production environment and documentation files are outside its
push path filters. `.github/workflows/` remains unchanged and frozen.

## Rollback

Record distinct current-Production, candidate, and restore identifiers before
each mutation. A mutable branch name, alias, or “previous deployment” label is
not sufficient.

- **Feature kill:** first set the matching Astro server flag false and redeploy,
  then publish a Panchangam build with the corresponding `VITE_*` flag absent or
  false. During token rollback, keep both routes off until old/new credentials
  have completed an approved overlap or coordinated cutover.
- **Panchangam code:** restore exact pre-activation commit `99629ada` through
  immutable branch
  `archive/pre-public-activation-2026-09-04-tcu-master-99629ad`. Resolve and
  record the full commit ID again immediately before release.
- **Astro/DashaFlow:** restore the separately recorded immutable deployment IDs
  and commits. Do not assume a Vercel alias still points to the reviewed build.
- **Provider/control failure:** turn both guest server flags off first, but keep
  `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED=true` while Production can reach
  public Nominatim. Turning it off restores the old unbudgeted signed-in path.
  To stop Nominatim completely, leave that migration flag true and remove the
  provider selection so signed-in and guest place lookups fail closed together.
- **Browser data:** preserve the profile schema and stored records; disabling
  remote calculation must not make existing profiles unreadable.
- **GitHub Pages:** preserve and compare the complete published `gh-pages` tip
  and tree, not only `index.html`. The rollback manifest must include `CNAME`,
  all current feeds and per-city Lagna JSON, the Gochara snapshot, the retained
  Rasi Phalalu tree, built assets, and the site shell. Follow
  [GitHub Pages retention and rollback](gh-pages-retention.md); do not repeat a
  partial orphan deployment that drops layered artifacts.

## Decision links

- [Public Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- [OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright)
- [Licensing gate #231](https://github.com/socraticsurge/telugu-calendar-utilities/issues/231)
- [Existing-distribution audit #444](https://github.com/socraticsurge/telugu-calendar-utilities/issues/444)
- [License-posture implementation #445](https://github.com/socraticsurge/telugu-calendar-utilities/issues/445)
- [PySwissEph rights or replacement #449](https://github.com/socraticsurge/telugu-calendar-utilities/issues/449)
- [Geocoder gate #233](https://github.com/socraticsurge/telugu-calendar-utilities/issues/233)
- [Producer invariants #443](https://github.com/socraticsurge/telugu-calendar-utilities/issues/443)
- [Managed geocoder/shared controls #446](https://github.com/socraticsurge/telugu-calendar-utilities/issues/446)
- [Authenticated geocoder migration #447](https://github.com/socraticsurge/telugu-calendar-utilities/issues/447)
- [Preview certification #448](https://github.com/socraticsurge/telugu-calendar-utilities/issues/448)
