# Guest calculation production activation

Status: **AGPL path approved; activation readiness incomplete**
Assessment timestamp: `2026-09-02T23:54:32+05:30` (`Asia/Kolkata`)
Release refresh: `2026-09-04` (`Asia/Kolkata`)
Panchangam production baseline: `571b805`
Epic: [#234](https://github.com/socraticsurge/telugu-calendar-utilities/issues/234)

This is the operator runbook for activating guest birth-profile calculation and
Muhurtam election-chart screening. The owner approved the AGPL-compatible
public-source path and today-launch sequence on 2026-09-04. The evidence and
rollback checks below still apply to every executed release step.

Refresh this record immediately before any Preview, merge, deployment, or
activation approval. Reconfirm branch heads, CI/security check URLs, exact
Vercel deployment IDs, environment-name inventories, public probes, and restore
refs; the values below are a dated assessment, not perpetual release evidence.

## Current state

| Component | State |
|---|---|
| Panchangam profile/Muhurtam UI | Live with both remote client flags off |
| Astro guest routes | The gateway code is on Production `bc15eb6` with public flags off. [PR #168](https://github.com/socraticsurge/astro-unified-core/pull/168) supplies the AGPL source-release posture; stacked [PR #169](https://github.com/socraticsurge/astro-unified-core/pull/169) supplies governed Production-only public Nominatim. Both remain unmerged review candidates. |
| DashaFlow authenticated contracts | [PR #3](https://github.com/socraticsurge/dashaflow-sidecar/pull/3) is green at `00f8fe2`; it adds AGPL/source disclosure and remains unmerged |
| Panchangam activation-readiness work | [PR #451](https://github.com/socraticsurge/telugu-calendar-utilities/pull/451) is merged at `571b805`; both public client flags remain off |
| Licensing | Owner selected the AGPL-compatible public-source path on 2026-09-04. TCU `1.14.0`, DashaFlow PR #3, and the Astro AGPL release candidate must all merge and expose public exact-revision source before activation |
| Production geocoder/shared controls | PR #169 reuses fixed public Nominatim with the existing Turso database, no LocationIQ/Geoapify account, no API key, and no Upstash/Redis dependency. It is Production-only, submit-only, process-cached, attributed, guest/auth shared, code-capped at 1,000 attempts/day, and protected by an exclusive fenced send lease. Production configuration and owner approval remain pending. |
| Authenticated backend Preview | Astro `dpl_DJ9hcs2aPk5vHsjuZfVEzaVEJuoE` and DashaFlow `dpl_8jXdq9TWJXRsz41zgyfZUJ9gbVyy` passed exact-token birth/election contracts against an isolated staging database. Public Nominatim is deliberately fixture-only outside Production; the Panchangam owner review remains local. |

## Hard gates

All boxes must be supported by links to evidence.

- [ ] #231 is updated to record the owner-selected AGPL-compatible Swiss
      Ephemeris and PySwissEph posture plus the final release evidence.
- [x] #444 audits existing PyPI and live-service exposure.
- [ ] #445 implements and verifies the selected licensing posture.
- [ ] #449 is updated to record that the AGPL PySwissEph binding is retained
      under the selected AGPL-compatible posture; no proprietary wrapper grant
      or replacement is required for this path.
- [ ] #443's DashaFlow producer invariants pass against the TCU consumers.
- [ ] #233 records the provider, retention, cache, attribution, and abuse posture.
- [ ] #446 implements and verifies the owner-approved geocoder and shared,
      fail-closed guest abuse controls. Candidate code is not certification.
- [ ] #447 migrates and regression-tests the authenticated profile geocoder so
      guest activation does not leave a second ungoverned provider path.
- [x] The exact Astro/DashaFlow backend pair is certified in protected Preview
      with an isolated staging database and paired token. Public-Nominatim
      behavior is fixture-tested there and rejected before network dispatch.
- [ ] Logs, analytics, and application-controlled server/shared cache contain
      no profile name, birth payload, natal chart, raw place-search text, raw
      IP, provider key, or bearer token. Provider transit of the submitted
      city/town query is separately disclosed and governed by approved terms.
- [ ] Browser requests contain no profile name or cookies. Calculation
      responses may contain the documented narrow natal- or election-chart
      results, but must not echo birth inputs, raw IPs, provider credentials,
      bearer credentials, or raw upstream diagnostics.
- [ ] Place-search responses carry only allowlisted structured provider/data
      attribution links, and the Panchangam UI visibly renders those links
      beside returned results at desktop and mobile widths.
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

| Layer | Current Production commit | Candidate runtime/code commit | Restore ref | Preview deployment ID | Production deployment ID | CI/security evidence |
|---|---|---|---|---|---|---|
| Panchangam | `571b805` | `ffcfca4` in PR #456, plus this documentation-only follow-up | `origin/master` and `archive/guest-activation-readiness-2026-09-03-8b0bf74` | Local owner-review build only; the deployed client intentionally accepts the canonical Production API | Re-query the immutable `gh-pages` tip/tree immediately before publication | PR #456 was green at `ffcfca4`: 1,467 Python tests, frontend suite, Python 3.10–3.13, CodeQL, Sonar and pip-audit passed; rerun after this docs change |
| Astro | `bc15eb60e214b94a5668403b79dffbfcf5ae8e77` | `f8c810d` in PR #168, then `bb23e3d` in stacked PR #169 | `origin/archive/astro-main-pre-guest-release-2026-09-04-519d686`; pre-review Nominatim archive `a7e013c` | `dpl_DJ9hcs2aPk5vHsjuZfVEzaVEJuoE` (Ready, protected; provider fixture-only) | Re-query exact Ready deployment of `bc15eb6` before mutation | PR #168 checks passed; PR #169 local verification passed 859 tests, TypeScript, lint with one inherited warning, palette, routes, production build, and independent code review |
| DashaFlow | `d01c8db` | `00f8fe26444cd8e63511af5d0d54ae41d15c419a` in PR #3 | `origin/archive/dashaflow-master-pre-guest-release-2026-09-04-d01c8db` | `dpl_8jXdq9TWJXRsz41zgyfZUJ9gbVyy` (Ready, protected) | Re-query exact Ready deployment of `d01c8db` before mutation | 133 local tests and all PR checks passed; exact-token birth/election calls passed against the isolated Astro Preview |

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
| Astro | `GEOCODER_PROVIDER` | Set `nominatim-public` in Production only after owner approval. Preview and real local development reject it and use fixtures. |
| Astro | `GEOCODER_API_KEY` | Must be absent for `nominatim-public`; a key is needed only if a dormant commercial adapter is selected in a later reviewed release. |
| Astro | `GEOCODER_DAILY_REQUEST_LIMIT` | Set a canonical value no greater than `1000` for public Nominatim. Guest and managed signed-in cache misses share the same Production provider row. |
| Astro | `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED` | Set exact `true` together with Production public-Nominatim guest activation so signed-in and guest calls share one governed path. Preview remains fixture-only. |
| Astro | `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | Existing database used for pseudonymous client/user/fleet counters and one non-personal provider-budget/lease row. No place query or result is stored there. |
| Astro | `RATE_LIMIT_HMAC_SECRET` | Existing server-only HMAC secret for pseudonymous client/user/fleet counter keys. |
| Astro runtime | `VERCEL_ENV`, `VERCEL`, `NODE_ENV` | implementation classifies only consistent explicit local or deployed markers; missing, unknown, self-hosted-production, or contradictory markers fail closed |

The selected provider contract is implemented in Astro PR #169. Public
Nominatim is fixed and keyless; no LocationIQ, Geoapify, Upstash, or Redis
account is required. It is intentionally unavailable in Preview and real local
development, where provider behavior is fixture-tested. Production guest place
search remains fail-closed until the signed-in migration flag is also exact
`true`, ensuring both audiences share one Turso-backed budget and send lease.

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
completion establishes a fenced 1,100 ms cooldown before the next distributed
send. Warm-process cache hits and coalesced duplicate callers spend no provider
slot. These controls implement the public service's absolute one-request/second
application ceiling; they are not a purchased quota or availability guarantee.

## Isolated Preview and Production-only provider sequence

The protected Astro/DashaFlow backend pair has been certified with an exact
shared bearer credential and an isolated staging Turso database. Birth-profile
and election-chart contracts passed, including missing/wrong-token failures and
shared limiter behavior. The public Nominatim endpoint is intentionally not a
Preview dependency: code rejects it outside Production, while unit, route, and
browser fixtures verify request shape, attribution, failures, and result
handling. Do not weaken CORS, expose a protection credential to browser
JavaScript, or point a hosted Preview browser at Production.

Before Production activation:

1. Record the final TCU, Astro, and DashaFlow candidate commits, successful
   checks, immutable deployments, and named restore refs.
2. Complete the AGPL/public-source and PySwissEph rights gates; verify exact
   source links from the deployed revisions.
3. Merge and deploy the credentialed Astro callers with guest flags off, then
   deploy DashaFlow authentication and repeat all signed-in chart fixtures.
4. Provision and verify the limiter schema against the exact Production Turso
   database. Confirm quota headroom and that request paths perform no DDL.
5. Configure `GEOCODER_PROVIDER=nominatim-public`, no geocoder API key, a daily
   limit no greater than `1000`, and keep
   `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED=true`. With guest flags still off,
   verify signed-in profile create/edit and the shared provider row.
6. Publish and observe the reviewed WAF rule according to its separate approval
   gate. Verify an edge rejection does not invoke a function or Turso.
7. Complete the local Panchangam browser journey with fixtures: place search,
   linked attribution, calculation, save/reload, profile detail, Daily
   Horoscope reuse, Muhurtam reuse, and mobile/desktop screenshots.
8. After owner sign-off, enable only the birth guest route/client and perform
   one bounded Production place query plus one birth calculation. Inspect
   headers, logs, limiter row, privacy fields, and public source links.
9. Observe the birth-only release for the recorded window. Activate election
   charts separately only after its own owner review and smoke test.
10. Attach evidence and rollback results to #448 and the parent epic.

## Failure matrix

| Failure | Expected behavior |
|---|---|
| Client flag absent/malformed | No remote call; manual profile entry or conservative unscreened Muhurtam result |
| Astro route flag off | Fixed 503; no geocoder/sidecar call |
| Shared Turso limiter missing/unavailable in Preview/Production | Fixed 503; no expensive calculation/provider call |
| Production geocoder configuration missing/unavailable | Place search 503; no arbitrary or commercial fallback |
| Authenticated migration flag absent/false | Production preserves its old unbudgeted signed-in Nominatim path; Preview fails closed. Never use this as a Nominatim incident rollback. |
| Authenticated migration exact `true`, provider/limit unavailable | Signed-in place-changing operation fails closed; no legacy or commercial fallback and no profile mutation |
| Sidecar token missing/bad | Fixed gateway error; no upstream diagnostic or token in response |
| Sidecar timeout/transient error | Up to two bounded attempts within the browser deadline, with one retry only for 502/503/504, then a fixed unavailable result |
| Malformed/inconsistent chart | 502/invalid response; never save or score as verified |
| Unsupported or ambiguous civil time | 422; offer manual entry |

## Merge and Production sequence

Production starts only after every hard gate above is complete: parent decisions
#231 and #233, audit #444, implementation gates #443, #445, #446, #447, and
#449, then exact-chain certification #448. The owner must still approve merges.
Preview approval, merge approval, Production deployment/configuration approval,
and feature activation approval are separate decisions.

1. With explicit merge approval, merge the Astro caller/source/geocoder stack
   first with guest flags off, then DashaFlow. Do not deploy either merely
   because its PR merged.
2. With separate deployment approval, deploy the exact recorded Astro commit
   with both guest route flags off and verify all existing credentialed
   signed-in callers. Keep the authenticated geocoder migration off until the
   Production provider/Turso configuration is ready.
3. Deploy the exact recorded DashaFlow commit and smoke every authenticated
   calculation route before any guest activation.
4. With both guest routes still off, select `nominatim-public`, keep the API key
   absent, set the approved daily ceiling, enable the authenticated geocoder
   migration, and smoke signed-in profile create/edit. Confirm that the shared
   provider budget and lease are active before proceeding.
5. With a distinct activation approval, enable Astro birth only and publish the
   Panchangam build with only `VITE_BIRTH_PROFILE_API_ENABLED=true`.
6. Smoke and observe birth profiles for the recorded window. Keep both election
   flags off throughout that observation period.
7. After evidence review and a separate election activation approval, enable
   the Astro election route and publish the election-enabled client build.
8. Record immutable Production deployment IDs, timestamps, probes, privacy/log
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
  `archive/guest-activation-readiness-2026-09-03-8b0bf74`; `origin/master` is
  the current `571b805` Production baseline at this refresh. Resolve and record
  both full commit IDs again immediately before release.
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
