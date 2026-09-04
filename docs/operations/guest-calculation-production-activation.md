# Guest calculation production activation

Status: **AGPL path approved; activation readiness incomplete**
Assessment timestamp: `2026-09-02T23:54:32+05:30` (`Asia/Kolkata`)
Release refresh: `2026-09-03` (`Asia/Kolkata`)
Panchangam production baseline: `eec464e871afdce9268716233fed2eecc91ae17a`
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
| Astro guest routes | [PR #161](https://github.com/socraticsurge/astro-unified-core/pull/161) is green at `e7fb3fe6`; Preview is Ready; routes remain absent from Production |
| DashaFlow authenticated contracts | [PR #3](https://github.com/socraticsurge/dashaflow-sidecar/pull/3) is green at `00f8fe2`; it adds AGPL/source disclosure and remains unmerged |
| Panchangam activation-readiness work | [PR #451](https://github.com/socraticsurge/telugu-calendar-utilities/pull/451) is merged at `571b805`; both public client flags remain off |
| Licensing | Owner selected the AGPL-compatible public-source path on 2026-09-04. TCU `1.14.0`, DashaFlow PR #3, and the Astro AGPL release candidate must all merge and expose public exact-revision source before activation |
| Production geocoder/shared controls | Fixed adapters, shared cache, privacy controls, guest budgets, and gated authenticated migration exist at `e7fb3fe6`; provider/Redis terms, credentials, Preview certification, and owner approval remain blocked by #233 and its children |
| Authenticated three-service Preview | **Blocked:** no exact pair-bound hosted Preview path exists yet |

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
- [ ] An exact, owner-approved, pair-bound hosted Preview mechanism is
      implemented for all three services and their protected deployments.
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

| Layer | Current Production commit | Candidate commit | Restore ref | Preview deployment ID | Production deployment ID | CI/security evidence |
|---|---|---|---|---|---|---|
| Panchangam | `eec464e871afdce9268716233fed2eecc91ae17a` | `3bcc0da839b34b28a8000a2e993d06f7a0d70473` | `archive/guest-activation-readiness-2026-09-03-3bcc0da`; Production baseline `archive/release-2026-09-01-master-profile-muhurtam-eec464e` | blocked; no exact pair-bound hosted Preview | `gh-pages` tip `d456da46a29998ec8b49d9b35d63443fec3b6ca7`, tree `248cb16b391e9a36e99cf11116c9316dfcf6e93b` | local: 406 frontend and 1,464 Python tests, both TypeScript configurations, production/docs build, 62 computation routes, 11 Mermaid diagrams, and 3 landing artifacts passed; PR #451 checks are green at `3bcc0da`, and this refresh commit requires its own checks |
| Astro | `519d686486a91d694de652f4a393174a52c346fc` | `e7fb3fe6e8e05f47f04aaa1b19ce9447d92ad315` | `archive/astro-managed-geocoder-controls-2026-09-03-e7fb3fe`; deployment `dpl_F6yWeNZ2Mx9fzdjwMnan19cM9HdY` | `dpl_CA16AEiMt52qsywcVBnjK857ZcDd` (Ready, protected) | `dpl_F6yWeNZ2Mx9fzdjwMnan19cM9HdY` | GitHub tests and Vercel Preview green; local 683 tests, TypeScript, lint (one inherited warning), palette, routes, production build, and independent no-P0/P1/P2 review passed |
| DashaFlow | `2c98ee8ef0c4a261686c507d9732f7834bc6b4f8` | `97eece13f524cc70bf995ae27620068a7d6aad44` | `archive/dashaflow-contract-remediation-2026-09-03-97eece1`; deployment `dpl_8Aoh11sqvj3yHPESkXRYRj8L4VHA` | `dpl_HetXHkbuH4BdKn8vnmGfpWanx6bX` (Ready, protected) | `dpl_8Aoh11sqvj3yHPESkXRYRj8L4VHA` | GitHub tests and both Vercel Preview checks green; local 103 tests and compileall passed |

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
| Astro | `GEOCODER_PROVIDER`, `GEOCODER_API_KEY` | implemented fixed-adapter pair; one owner-approved provider and server-only key are required when deployed; no provider/key is selected or configured |
| Astro | `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED` | separate exact-`true` migration gate; omission/false preserves the existing signed-in profile path while guest work is reviewed; activation requires its own Preview and owner approval |
| Astro | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | preferred complete pair for shared guest limits, activated authenticated per-user/fleet limits, and 24-hour normalized geocoder cache |
| Astro | `KV_REST_API_URL`, `KV_REST_API_TOKEN` | complete compatibility pair only; never combine a URL/token across namespaces |
| Astro runtime | `VERCEL_ENV`, `VERCEL`, `NODE_ENV` | implementation classifies only consistent explicit local or deployed markers; missing, unknown, self-hosted-production, or contradictory markers fail closed |

The named provider and shared-cache contracts are implemented in local Astro
candidate `e7fb3fe6`, but provider selection, terms, quota/billing posture,
credentials, and hosted certification remain unapproved. Existing signed-in
profiles remain isolated from that migration unless its separate flag is exact
`true`. No current environment variable makes the TCU/Astro/DashaFlow hosted
Preview chain safe or reachable. Any such variables must be added only as part
of the reviewed pair-bound mechanism.

### Place-search retention and quota contract

| Boundary | Permitted data | Retention / verification gate |
|---|---|---|
| Panchangam browser request | Trimmed city/town query only; no profile name, cookie, birth date/time, or chart | Transient request state; browser network evidence required |
| Astro process state | Ephemeral HMAC client pseudonym; SHA-256 request key; normalized provider rows while pending | Per-process limiter window or bounded process lifetime; raw query/IP inspection required |
| Redis REST | HMAC cache/rate-limit key; at most five normalized provider rows | Geocoder rows expire after 24 hours; rate limits after one minute; GET/SET response and value are bounded |
| Managed geocoder | Submitted city/town query, provider credential, and Astro's server egress metadata | Provider-controlled; select the exact plan/region only after terms, privacy, attribution, and deletion/retention review |
| Sentry / application analytics | No request bodies, raw place query, provider URL query/key, birth payload, or chart | Verify configuration and inspect Preview events before activation |

The current geocoder fleet ceiling is 60 calls per minute, shared by guest
place search and the separately activated authenticated migration. The managed
authenticated path also applies a 10-call-per-user minute limit. In the worst
case of unique cache misses, the shared fleet ceiling permits 86,400 provider
calls in 24 hours. Provider approval must either select a plan that safely
covers this bound or lower/add a daily fleet budget; the minute limiter alone
must not be mistaken for a purchased-plan quota.

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
   guest flags and `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED` off while
   dependencies and destination restrictions are probed.
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
9. Separately test signed-in profile create/edit while the authenticated
   migration flag is off, then on in Preview. Verify the per-user/shared fleet
   limits and restore it off before completing the guest-only evidence.
10. Attach browser network evidence, screenshots, application/platform/provider
   log checks, cache-key inspection, and negative cross-pair tests to #448.
11. Rehearse rollback at every layer before requesting any merge approval.

## Failure matrix

| Failure | Expected behavior |
|---|---|
| Client flag absent/malformed | No remote call; manual profile entry or conservative unscreened Muhurtam result |
| Astro route flag off | Fixed 503; no geocoder/sidecar call |
| Shared limiter missing/unavailable in Preview/Production | Fixed 503; no expensive calculation/provider call |
| Geocoder missing/unavailable | Place search 503; no fallback to public Nominatim |
| Authenticated migration flag absent/false | Existing signed-in Nominatim path remains available; managed adapter and Redis are not consulted |
| Authenticated migration exact `true`, dependency/limit unavailable | Signed-in place-changing operation fails closed; no public-Nominatim fallback and no DB mutation |
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

1. With explicit merge approval, merge DashaFlow first, then Astro. Do not deploy
   either merely because its PR merged.
2. With separate deployment approval, deploy the exact recorded DashaFlow commit
   with both new consumers still inactive; smoke the authenticated v1 routes.
3. Deploy the exact recorded Astro commit with both guest route flags and the
   authenticated migration flag off; verify fixed disabled guest responses and
   unchanged signed-in profile create/edit before dependency probes.
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
- **Provider/control failure:** keep guest server flags and the authenticated
  migration flag off. Guest search and an activated authenticated migration do
  not fall back to public Nominatim; the explicitly disabled authenticated
  migration preserves only the pre-existing signed-in path.
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
