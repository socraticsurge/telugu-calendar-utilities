# Guest calculation production activation

Status: **assessment complete; activation readiness incomplete**  
Assessment timestamp: `2026-09-02T23:54:32+05:30` (`Asia/Kolkata`)  
Panchangam production baseline: `eec464e871afdce9268716233fed2eecc91ae17a`  
Epic: [#234](https://github.com/socraticsurge/telugu-calendar-utilities/issues/234)

This is the operator runbook for activating guest birth-profile calculation and
Muhurtam election-chart screening. It records sequence and evidence; it is not
authorization to merge, add credentials, deploy, relicense, or enable a public
flag.

Refresh this record immediately before any Preview, merge, deployment, or
activation approval. Reconfirm branch heads, CI/security check URLs, exact
Vercel deployment IDs, environment-name inventories, public probes, and restore
refs; the values below are a dated assessment, not perpetual release evidence.

## Current state

| Component | State |
|---|---|
| Panchangam profile/Muhurtam UI | Live with both remote client flags off |
| Astro guest routes | Open PR #161; absent from Production |
| DashaFlow authenticated contracts | Candidate commit `97eece13`; not the released baseline |
| Licensing | Blocked by #231 and its children |
| Production geocoder/shared controls | Blocked by #233 and its children |
| Authenticated three-service Preview | **Blocked:** no exact pair-bound hosted Preview path exists yet |

## Hard gates

All boxes must be supported by links to evidence.

- [ ] #231 records the approved Swiss Ephemeris **and PySwissEph wrapper** posture.
- [ ] #444 audits existing PyPI and live-service exposure.
- [ ] #445 implements and verifies the selected licensing posture.
- [ ] #449 records wrapper rights or completes and verifies an approved replacement.
- [ ] #443's DashaFlow producer invariants pass against the TCU consumers.
- [ ] #233 records the provider, retention, cache, attribution, and abuse posture.
- [ ] #446 implements and verifies the owner-approved geocoder and shared,
      fail-closed guest abuse controls. Candidate code is not certification.
- [ ] #447 migrates and regression-tests the authenticated profile geocoder so
      guest activation does not leave a second ungoverned provider path.
- [ ] An exact, owner-approved, pair-bound hosted Preview mechanism is
      implemented for all three services and their protected deployments.
- [ ] Logs, analytics, and server/shared cache contain no profile name, birth
      payload, natal chart, raw IP, provider key, or bearer token.
- [ ] Browser requests contain no profile name or cookies. Calculation
      responses may contain the documented narrow natal- or election-chart
      results, but must not echo birth inputs, raw IPs, provider credentials,
      bearer credentials, or raw upstream diagnostics.
- [ ] #448 records exact deployment/check IDs, probes, privacy evidence,
      screenshots, and rollback rehearsal **after** #443, #445, #446, #447,
      and #449 are complete.
- [ ] Owner approvals are recorded independently for Preview configuration,
      each merge, each Production deployment/configuration change, and each
      public client-flag activation.

## Version record

Fill this table without secret values.

Do not reuse one value for production, candidate, or rollback. Record immutable
deployment IDs rather than mutable aliases.

| Layer | Current Production commit | Candidate commit | Restore ref | Preview deployment ID | Production deployment ID | CI/security evidence |
|---|---|---|---|---|---|---|
| Panchangam | `eec464e871afdce9268716233fed2eecc91ae17a` | activation-readiness branch; final SHA unrecorded | `archive/release-2026-09-01-master-profile-muhurtam-eec464e` | required; unrecorded | required; unrecorded | required; unrecorded |
| Astro | `519d686` (`main` assessment baseline) | PR #161 `77e9c356` plus remediation; final SHA unrecorded | required; unrecorded | required; unrecorded | required; unrecorded | required; unrecorded |
| DashaFlow | `2c98ee8` (`master` assessment baseline) | `97eece13` | required; unrecorded | required; unrecorded | required; unrecorded | local: 103 tests passed; hosted checks required and unrecorded |

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
| Astro | `GEOCODER_BASE_URL` | current guest adapter configuration; Production provider is not yet selected or approved |
| Astro | `GEOCODER_USER_AGENT` | current non-secret provider identity; not a provider credential |
| Astro | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | candidate shared guest rate-limit dependency; not a certified shared geocoder cache |

`GEOCODER_PROVIDER` and `GEOCODER_API_KEY` describe a possible future
provider-adapter design only; they are **not implemented environment names** in
the current candidate. Likewise, no current environment variable makes the
TCU/Astro/DashaFlow hosted Preview chain safe or reachable. Any such variables
must be added only as part of the reviewed pair-bound mechanism.

## Hosted Preview blocker and future sequence

**Stop: #448 is not executable with the current clients and deployments.** A
deployed Panchangam build accepts only the canonical Production Astro API,
Astro CORS accepts only the Production Panchangam origin (plus loopback), and
the server-to-server clients do not carry an approved Vercel deployment-
protection credential. A protected Vercel Preview therefore cannot certify the
real browser-to-Astro-to-DashaFlow chain. Do not point a Preview browser at
Production, add a wildcard `*.vercel.app` origin, disable Preview protection,
or create an automation-bypass token as an undocumented side effect.

Before the sequence below becomes executable, implement and approve a mechanism
that binds one immutable Panchangam Preview deployment to one immutable Astro
Preview deployment and one immutable DashaFlow Preview deployment. It must
allowlist only the exact browser origin, restrict each client to the exact next
service, support the approved protection/authentication path without exposing a
credential to browser JavaScript, and have negative cross-pair tests.

After that prerequisite and all hard gates are complete:

1. Record the three candidate commits, immutable Preview deployment IDs, exact
   pair bindings, check URLs, and named restore refs.
2. Verify DashaFlow locally, including coherent 1-chart and 24-chart contracts,
   then deploy only its Preview.
3. Configure the distinct Astro/DashaFlow token names with one approved
   Preview-only value; verify missing/bad credentials and sanitized errors.
4. Configure the owner-approved geocoder and shared controls at Astro. Keep both
   guest flags off while dependencies and destination restrictions are probed.
5. Enable the Astro birth route only, then build the bound Panchangam Preview
   with only the birth flag. Verify place search, calculation, save, reload,
   profile detail, and Daily Horoscope reuse.
6. Keep election-chart flags off during a defined birth-only observation
   window; record duration, traffic/errors, provider/limit behavior, and privacy
   inspection results.
7. Disable birth or preserve its verified state, then exercise election alone:
   verify 1/24-chart batches, rating evidence, unknown/failure behavior, and
   Muhurtam reuse.
8. Only after both isolated observations, test both capabilities together.
9. Attach browser network evidence, screenshots, application/platform/provider
   log checks, cache-key inspection, and negative cross-pair tests to #448.
10. Rehearse rollback at every layer before requesting any merge approval.

## Failure matrix

| Failure | Expected behavior |
|---|---|
| Client flag absent/malformed | No remote call; manual profile entry or conservative unscreened Muhurtam result |
| Astro route flag off | Fixed 503; no geocoder/sidecar call |
| Shared limiter missing/unavailable in Preview/Production | Fixed 503; no expensive calculation/provider call |
| Geocoder missing/unavailable | Place search 503; no fallback to public Nominatim |
| Sidecar token missing/bad | Fixed gateway error; no upstream diagnostic or token in response |
| Sidecar timeout/transient error | One bounded attempt within the browser deadline, then a fixed unavailable result; no undocumented retry |
| Malformed/inconsistent chart | 502/invalid response; never save or score as verified |
| Unsupported or ambiguous civil time | 422; offer manual entry |

## Merge and Production sequence

Production starts only after every hard gate above is complete: parent decisions
#231 and #233, audit #444, implementation gates #443, #445, #446, #447, and
#449, then exact-chain certification #448. The owner must still approve merges.
Preview approval, merge approval, Production deployment/configuration approval,
and feature activation approval are separate decisions.

1. With explicit merge approval, merge DashaFlow first, then Astro. Do not deploy
   either merely because its PR merged.
2. With separate deployment approval, deploy the exact recorded DashaFlow commit
   with both new consumers still inactive; smoke the authenticated v1 routes.
3. Deploy the exact recorded Astro commit with both guest route flags off;
   verify fixed disabled responses and all dependencies without public traffic.
4. With a distinct activation approval, enable Astro birth only and publish the
   Panchangam build with only `VITE_BIRTH_PROFILE_API_ENABLED=true`.
5. Smoke and observe birth profiles for the recorded window. Keep both election
   flags off throughout that observation period.
6. After evidence review and a separate election activation approval, enable
   the Astro election route and publish the election-enabled client build.
7. Record immutable Production deployment IDs, timestamps, probes, privacy/log
   checks, feature-flag states, and restore refs after every step.

Publishing the Panchangam build may require a workflow/configuration change.
`.github/workflows/` is frozen in this repository and its current path filters
do not make a docs-only commit a production activation mechanism. Any workflow
change requires explicit owner approval and its own reviewed branch.

## Rollback

Record distinct current-Production, candidate, and restore identifiers before
each mutation. A mutable branch name, alias, or “previous deployment” label is
not sufficient.

- **Feature kill:** first set the matching Astro server flag false and redeploy,
  then publish a Panchangam build with the corresponding `VITE_*` flag absent or
  false. During token rollback, keep both routes off until old/new credentials
  have completed an approved overlap or coordinated cutover.
- **Panchangam code:** restore the recorded Production commit. The known
  pre-activation restore branch is
  `archive/release-2026-09-01-master-profile-muhurtam-eec464e` at baseline
  `eec464e`; verify the ref again at release time.
- **Astro/DashaFlow:** restore the separately recorded immutable deployment IDs
  and commits. Do not assume a Vercel alias still points to the reviewed build.
- **Provider/control failure:** keep server flags off; do not fall back to public
  Nominatim when managed geocoding or shared controls fail.
- **Browser data:** preserve the profile schema and stored records; disabling
  remote calculation must not make existing profiles unreadable.
- **GitHub Pages:** preserve and compare the complete published `gh-pages` tip
  and tree, not only `index.html`. The rollback manifest must include `CNAME`,
  all current feeds and per-city Lagna JSON, the Gochara snapshot, the retained
  Rasi Phalalu tree, built assets, and the site shell. Follow
  [GitHub Pages retention and rollback](gh-pages-retention.md); do not repeat a
  partial orphan deployment that drops layered artifacts.

## Decision links

- [Licensing gate #231](https://github.com/socraticsurge/telugu-calendar-utilities/issues/231)
- [Existing-distribution audit #444](https://github.com/socraticsurge/telugu-calendar-utilities/issues/444)
- [License-posture implementation #445](https://github.com/socraticsurge/telugu-calendar-utilities/issues/445)
- [PySwissEph rights or replacement #449](https://github.com/socraticsurge/telugu-calendar-utilities/issues/449)
- [Geocoder gate #233](https://github.com/socraticsurge/telugu-calendar-utilities/issues/233)
- [Producer invariants #443](https://github.com/socraticsurge/telugu-calendar-utilities/issues/443)
- [Managed geocoder/shared controls #446](https://github.com/socraticsurge/telugu-calendar-utilities/issues/446)
- [Authenticated geocoder migration #447](https://github.com/socraticsurge/telugu-calendar-utilities/issues/447)
- [Preview certification #448](https://github.com/socraticsurge/telugu-calendar-utilities/issues/448)
