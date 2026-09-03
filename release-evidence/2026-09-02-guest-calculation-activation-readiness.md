# Production activation evidence: guest birth profiles and election charts

Assessment status: **complete; activation readiness incomplete**
Assessment completed: `2026-09-02T23:54:32+05:30` (`Asia/Kolkata`)
Evidence checked: 2026-09-01 and 2026-09-02
Repository baseline: `eec464e871afdce9268716233fed2eecc91ae17a`
Decision owner: repository owner
Legal note: this is an engineering release assessment, not legal advice.

This is a dated snapshot. Refresh the public probes, repository/PR heads,
environment-name inventories, CI and security check URLs, immutable deployment
IDs, and restore refs immediately before any Preview, merge, deployment, or
activation decision.

## Research question

What is live today, why are remote birth details and election-chart screening
not active on the public Panchangam site, and what is the smallest safe sequence
to activate them without losing rollback points?

## Executive verdict

The public Panchangam contains the profile, natal-chart, and Muhurtam client
experience, but its two remote adapters are deliberately compiled inactive. The
production Astro deployment does not currently expose the new guest routes.
DashaFlow is live for older operations, while its new authenticated profile and
election contracts remain in an unmerged pull request.

The right action is **not** to turn on a flag. Five gate groups remain:

1. choose and implement a Swiss Ephemeris/PySwissEph licensing posture;
2. enforce producer-side chart-contract invariants;
3. implement and approve managed geocoding, authenticated-profile migration,
   shared caching, and fleet-wide abuse controls;
4. implement an exact pair-bound hosted Preview path; and
5. certify that exact three-service chain before any Production change.

The first gate needs an owner/legal decision. The other four can be developed
and tested while all public flags remain off.

## Confirmed live state

| Layer | Current public state | Evidence | Consequence |
|---|---|---|---|
| Panchangam static client | Live at `panchangam.astrochaganti.com`; baseline `eec464e` | HTTP 200 on 2026-09-02; repository production merge | Manual profiles, saved-profile reuse, and disabled-state UI are live. Remote calculation is not. |
| Birth client flag | Inactive in the public build | `VITE_BIRTH_PROFILE_API_ENABLED=true` was not used for the production build | Profiles default to manual astrology entry. |
| Election client flag | Inactive in the public build | `VITE_ELECTION_CHART_API_ENABLED=true` was not used for the production build | Muhurtam retains the conservative shortlist and does not claim chart screening. |
| Astro guest profile route | Not present in Production | GET probe returned 404 on 2026-09-02 | There is no public gateway endpoint to call even if the client flag changed. |
| Astro guest election route | Not present in Production | GET probe returned 404 on 2026-09-02 | Election-chart enrichment cannot run publicly. |
| Astro implementation | Open PR #161, head `77e9c356` against `development`; remediation has no final recorded commit | Dated GitHub/Preview checks existed at assessment time; refresh exact check and deployment IDs | Code exists, but is neither merged, certified, nor Production-configured. |
| DashaFlow service | Legacy service healthy | `/health` returned 200 on 2026-09-02 | Existing public operations are reachable; this expands the licensing audit beyond the guest feature. |
| DashaFlow v1 contracts | Candidate `97eece13` on top of PR #1 | Local 103-test suite passed; hosted check/deployment IDs are required and unrecorded | New authenticated profile/election endpoints are not the released baseline. |
| Preview credentials | Not configured across the complete chain | Environment-name audit only; no secret values inspected | An authenticated end-to-end Preview test is not yet possible. |

## Version and restore register

Production, candidate, and restore identifiers are deliberately separate.
Mutable aliases are not rollback evidence, and no missing Vercel deployment ID
is inferred from a branch or commit.

| Layer | Current Production commit | Candidate commit | Restore ref | Preview deployment ID | Production deployment ID |
|---|---|---|---|---|---|
| Panchangam | `eec464e871afdce9268716233fed2eecc91ae17a` | activation-readiness branch; final SHA unrecorded | `archive/release-2026-09-01-master-profile-muhurtam-eec464e` | required; unrecorded | required; unrecorded |
| Astro | `519d686` (`main` assessment baseline) | PR #161 `77e9c356` plus remediation; final SHA unrecorded | required; unrecorded | required; unrecorded | required; unrecorded |
| DashaFlow | `2c98ee8` (`master` assessment baseline) | `97eece13` | required; unrecorded | required; unrecorded | required; unrecorded |

## Intended boundary

```text
Panchangam browser
  | place query only
  v
Astro guest geocoder route ----> owner-approved provider (selection pending)
  |
  | date, time, coordinates, timezone; no profile name/cookies
  v
Astro guest calculation route --Bearer--> DashaFlow projection
  |
  v
documented narrow natal-chart result --> browser-local profile storage
```

The browser request contains no profile name or cookies. The response is
expected to contain the documented narrow natal-chart result; it must not echo
birth inputs, raw IPs, provider credentials, bearer credentials, or raw
upstream diagnostics. Logs, analytics, and server/shared caches must contain no
profile name, birth payload, natal chart, raw IP, provider key, or bearer token.

The browser stores the profile. Astro remains stateless for birth profiles.
DashaFlow calculates positions but does not select an activity or issue an
auspiciousness verdict. The TCU browser validates the contract and applies its
documented rules.

## Release-blocking findings

### 1. Swiss Ephemeris and PySwissEph are separate licensing decisions

Astrodienst offers Swiss Ephemeris under AGPL or a Professional License and
requires the choice before distribution or public service activation. The June
2026 professional contract covers browser-accessed server software and clients
that request calculations from a server.

The current stack also directly depends on PySwissEph. PySwissEph is published
as AGPL-3.0-only. In the still-open upstream issue #92, the Swiss Ephemeris
author explains that a Swiss Professional License does not by itself provide a
closed-source license for this separate wrapper. Therefore:

| Owner posture | Smallest technically credible path |
|---|---|
| Source disclosure is acceptable | Confirm the affected combined-work/network scope, then adopt an AGPL-compatible posture with corresponding deployed source and build/run instructions. |
| Source must remain private | Obtain both an applicable Swiss Professional License and separate PySwissEph wrapper rights, or replace the binding with one whose proprietary-use rights are clear. |

Using Moshier return flags does not avoid this boundary: the service still
imports and executes the Swiss Ephemeris wrapper. Changing to Swiss data files
would be a separate versioned computation change and parity exercise.

The audit must include the already published MIT PyPI package and existing live
DashaFlow operations, not only the proposed guest routes. This assessment does
not declare noncompliance; it identifies the scope that needs a written
owner/legal conclusion.

Tracked by #231 and the required children #444, #445, and #449.

### 2. DashaFlow's mock success contracts contradict the consumer

The real engine currently emits coherent values, but PR #1 validates only field
ranges at its output boundary. Its profile success fixture contains
Moon/Nakshatra, Whole Sign house, and node contradictions; its election fixture
uses non-opposite nodes. TCU correctly rejects those responses.

Before merge, the producer must validate the same cross-field invariants and
replace its mock happy paths with contracts the actual browser accepts. This is
a release-blocking contract/test gap, not a demonstrated exploitable security
vulnerability. Work is tracked by #443.

### 3. Shared controls remain candidate work, not release evidence

Astro PR #161 gives every guest route a small in-process limiter. In that
reviewed head, only election charts add a fail-closed Redis-backed fleet limit
in Vercel Preview and Production. An unauthenticated caller can therefore
spread place or birth requests across functions and IP addresses; CORS/Origin
checks do not establish caller identity.

The local remediation candidate expands shared guest rate limiting, but it is
not yet a recorded commit, merged release, hosted verification, or operational
certification. It must pass review and failure-mode probes before the report can
describe the controls as active.

Place search also uses a bounded, time-limited in-process cache and provider
queue. Those controls are not a shared cache and do not enforce a global
provider quota across a serverless fleet. The code and documentation must agree
that hashed query keys/normalized provider rows are temporarily cached while birth
payloads and natal charts are not.

Tracked by #233 and #446.

### 4. The geocoder is not production-ready

Public Nominatim permits modest end-user-triggered use only under its policy:
application-wide maximum one request per second, identifying headers,
attribution, caching, no client autocomplete, switchability, and no personal or
confidential submissions. That makes it suitable for bounded local development,
not the default public serverless fleet.

The current candidate implements `GEOCODER_BASE_URL` and
`GEOCODER_USER_AGENT`; it does not implement a named provider mode or a
`GEOCODER_API_KEY` contract. The original reviewed PR accepted a configured
HTTPS base without the complete production destination/redirect controls. Some
containment is being added on the remediation branch, but provider selection,
credential handling, shared caching, provider-specific attribution, hosted
verification, and operational terms remain unresolved. This is a deployment
containment and policy gap, not evidence that a managed provider is approved.

| Option | Engineering fit | Operational/legal work | Current recommendation |
|---|---|---|---|
| LocationIQ | Nominatim-compatible response may reduce adapter work | Owner review of current terms, privacy, attribution, service level, and plan; credential transport must be designed | Research candidate only. No approval or adapter exists. |
| Geoapify | Explicit forward-geocoding JSON contract | Owner review of current terms, privacy, attribution, service level, and plan; a different response adapter is required | Research candidate only. No approval or adapter exists. |
| Public Nominatim | No purchase; current local adapter works | Strict global 1 r/s and policy constraints; no confidential input | Keep for local development only. |
| Self-hosted Nominatim | Full control | Large database, storage, updates, monitoring, abuse and uptime ownership | Disproportionate for current demand. |

Fixed provider modes can be evaluated in #446, but neither commercial adapter
is implemented or approved. No provider privacy, retention, or SLA conclusion
has been established. Production must remain fail closed until one provider,
its contract, credential transport, attribution, caching, quotas, and failure
behavior are owner-approved and verified.

### 5. Hosted Preview cannot exercise the real chain yet

TCU's deployed clients accept only the canonical Production Astro API (their
`VITE_*_API_BASE` settings cannot select an arbitrary hosted Preview), while
Astro accepts only the Production Panchangam origin and HTTP loopback. A Vercel
Preview Panchangam origin is therefore rejected and cannot call an Astro
Preview. Preview support must be exact and environment-bound; it must not
become a wildcard `*.vercel.app` rule.

Vercel Preview deployment protection also prevents anonymous probing. Earlier
authenticated CLI probing was found to create an automation-bypass token as a
side effect; the exact generated token was revoked and the project was verified
to have no remaining protection-bypass entry. Future certification must use an
explicitly approved Preview-access mechanism rather than silently mutating
deployment protection.

The server-to-server clients also lack an approved way to traverse protected
Preview deployments. #448 is therefore **blocked**, not merely pending test
execution, until an owner-approved mechanism binds one immutable Panchangam
Preview to one immutable Astro Preview and one immutable DashaFlow Preview,
supports their protection/authentication boundary without exposing a browser
credential, and rejects cross-pair calls. Tracked by #448, which cannot close
until #443, #445, #446, #447, and #449 are complete.

## Security review disposition

The DashaFlow PR's completed diff scan found no P0/P1 and no reportable security
vulnerability. It recorded the contract-invariant gap, external fleet-limit
dependency, and non-atomic single-token rotation as release concerns.

The Astro review produced a local remediation candidate for stricter runtime
classification, shared guest limits, destination/redirect controls, bounded
cache/queue behavior, and error redaction. That work is not yet a recorded
release or hosted evidence. Managed-provider selection, shared geocoder cache,
authenticated-profile migration, exact Preview pairing, and explicit
log/retention verification remain open. The existing sidecar bearer clients are
strict, bounded, server-only, and sanitize upstream errors.

## Environment matrix (names only)

| Layer | Variable | Preview requirement | Production requirement |
|---|---|---|---|
| Panchangam build | `VITE_BIRTH_PROFILE_API_ENABLED` | exact `true` only after a pair-bound Preview mechanism exists | exact `true` only after activation approval |
| Panchangam build | `VITE_ELECTION_CHART_API_ENABLED` | independently exercised after birth-only observation | independently approved |
| Panchangam build | `VITE_BIRTH_PROFILE_API_BASE` | implemented, but current deployed validation cannot target hosted Preview | canonical Production Astro base only today |
| Panchangam build | `VITE_ELECTION_CHART_API_BASE` | implemented, but current deployed validation cannot target hosted Preview | canonical Production Astro base only today |
| Astro | `GUEST_BIRTH_PROFILE_ENABLED` | exact `true` for the test window | exact `true` only after all gates |
| Astro | `GUEST_ELECTION_CHART_ENABLED` | independently exercised | independently approved |
| Astro | `DASHAFLOW_SIDECAR_URL` | pinned approved Preview sidecar | pinned released sidecar |
| Astro | `DASHAFLOW_SIDECAR_TOKEN` | Astro sender credential | same, with approved rotation runbook |
| DashaFlow | `DASHAFLOW_API_TOKEN` | verifier; value matches Astro token | verifier; value matches Astro token |
| Astro | `GEOCODER_BASE_URL` | current adapter name; provider not approved | same current name unless #446 deliberately replaces it |
| Astro | `GEOCODER_USER_AGENT` | current non-secret provider identity | same current name unless #446 deliberately replaces it |
| Astro | `UPSTASH_REDIS_REST_URL` | candidate shared guest limiter dependency | required only after candidate verification/approval |
| Astro | `UPSTASH_REDIS_REST_TOKEN` | candidate server-only limiter credential | required only after candidate verification/approval |

`GEOCODER_PROVIDER` and `GEOCODER_API_KEY` are proposed design names, not
implemented configuration. The Upstash candidate is a shared rate limiter, not
evidence of a shared geocoder cache.

No value belongs in source control, issue comments, browser variables, or this
report.

## Safe release sequence

1. Preserve and record distinct Production commits/deployment IDs, candidate
   commits/deployment IDs, and named restore refs for all three layers.
2. Complete #443, #445, #446, #447, and #449 and attach their test/review
   evidence. Parent decisions #231 and #233 must also be resolved.
3. Implement and review the exact pair-bound hosted Preview mechanism. Until
   then, #448 is blocked and no end-to-end Preview claim is possible.
4. With a separate Preview-configuration approval, deploy DashaFlow Preview,
   then Astro Preview with both guest flags off, then the bound Panchangam
   Preview. Record immutable deployment and check IDs.
5. Exercise birth only and observe it for a recorded interval while election
   remains off. Review logs, cache keys, browser requests/responses, provider
   behavior, screenshots, and rollback evidence.
6. Exercise election separately, then both capabilities together. Complete #448
   only after negative pair-binding tests and rollback rehearsal pass.
7. Obtain a separate merge approval. Merge DashaFlow before Astro; a merge does
   not authorize deployment.
8. Obtain a separate Production deployment/configuration approval. Deploy
   DashaFlow, then Astro with both guest flags off.
9. Obtain a distinct birth activation approval, publish birth only, and observe.
   Keep election off during that Production observation window.
10. Only after review, obtain a distinct election activation approval and
    publish election screening.

The Panchangam deployment workflows are frozen and their path filters do not
make this documentation branch an activation mechanism. Any required workflow
change needs explicit owner approval and a separately reviewed branch.

## Rollback

- **Feature kill:** turn the matching Astro server flag off first, then rebuild
  the client with the affected `VITE_*` flag absent/false. Existing
  browser profiles remain readable and manual entry stays available.
- **Token rollback:** keep both guest flags off while old/new credentials use an
  approved overlap or coordinated cutover; never strand one side on a different
  value.
- **Astro/DashaFlow:** restore separately recorded immutable deployment IDs and
  commits; do not rely on mutable aliases.
- **Geocoder/Redis:** server flags stay false if either dependency is unavailable;
  do not fall back to public Nominatim in Preview/Production.
- **Code:** the known Panchangam restore branch is
  `archive/release-2026-09-01-master-profile-muhurtam-eec464e` for baseline
  `eec464e`. Record Astro/DashaFlow restore refs before mutation. Do not rely on
  a tag that can trigger publication workflows.
- **GitHub Pages:** preserve and compare the entire published tip and tree:
  `CNAME`, the site shell/assets, all current ICS feeds and per-city Lagna JSON,
  the Gochara snapshot, and the retained Rasi Phalalu tree. Follow
  `docs/operations/gh-pages-retention.md`; restoring only the landing build is
  an incomplete rollback.

## Owner decisions still required

1. Is an AGPL-compatible/source-disclosed service acceptable, or must the
   affected service remain private?
2. Which managed geocoder and plan may process submitted city/town queries?
3. Which exact pair-bound hosted Preview mechanism may be implemented, including
   deployment protection, exact origins, and server-to-server access?
4. After evidence is complete: separate approvals for PR merges, Production
   configuration/deployment, and each public client flag.

## Source register

| Source | What it establishes | Accessed |
|---|---|---|
| https://www.astro.com/swisseph/swisseph.htm | Swiss Ephemeris dual-license choice and timing | 2026-09-01 |
| https://www.astro.com/swisseph/secont_e.pdf | June 2026 Professional License scope and terms | 2026-09-01 |
| https://www.astro.com/swisseph/swephprice_e.htm | Current unlimited-license price | 2026-09-01 |
| https://github.com/astrorigin/pyswisseph | PySwissEph source and AGPL declaration | 2026-09-01 |
| https://github.com/astrorigin/pyswisseph/issues/92 | Unresolved wrapper/professional-license distinction | 2026-09-01 |
| https://operations.osmfoundation.org/policies/nominatim/ | Public Nominatim usage policy | 2026-09-01 |
| https://docs.locationiq.com/docs/search-forward-geocoding | LocationIQ endpoint, key, compatibility, and response | 2026-09-02 |
| https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/ | Geoapify endpoint, key, JSON response, and provider attribution | 2026-09-02 |
| https://vercel.com/docs/environment-variables/system-environment-variables | `VERCEL_ENV` and exact deployment hostname variables | 2026-09-02 |
| DashaFlow PR #1 diff and completed security scan | Contract, authentication, tests, and release findings | 2026-09-01 |
| Astro PR #161 diff and security scan | Gateway, provider, abuse-control, and privacy boundaries | 2026-09-02 |

## Tracking map

- Epic: #234
- Licensing gate and children: #231, #444, #445, #449
- Geocoder gate and children: #233, #446, #447
- DashaFlow invariant remediation: #443
- Preview certification/runbook: #448
- Existing contract implementation: #238
- Existing client activation gates: #438

## 2026-09-03 remediation addendum

This addendum preserves the 2026-09-02 assessment above as a dated record. It
does not rewrite its then-current observations. The following local immutable
checkpoints now close several engineering findings, while Production remains
unchanged and every approval gate remains in force.

| Layer | Local checkpoint | What changed | Verification |
|---|---|---|---|
| DashaFlow | `97eece13f524cc70bf995ae27620068a7d6aad44`; restore `archive/dashaflow-contract-remediation-2026-09-03-97eece1` | Producer success fixtures and response validation now enforce the cross-field profile/election invariants required by the consumers. | 103 tests and compileall passed; pushed to PR #1; GitHub tests and both Vercel Preview checks are green; not merged or released. |
| Astro | `e7fb3fe6e8e05f47f04aaa1b19ce9447d92ad315`; restore `archive/astro-managed-geocoder-controls-2026-09-03-e7fb3fe` | Tri-state deployment gates, fixed LocationIQ/Geoapify adapters, structured attribution, bounded provider work, fail-closed shared guest limits/cache, Sentry privacy controls, and a separately gated authenticated migration with per-user and shared geocoder-fleet limits. Missing/malformed auth-migration flags preserve the existing signed-in path. | 683 tests, TypeScript, palette, route checks, production build, and independent security re-review passed with no surviving P0/P1/P2; one inherited lint warning, zero errors; pushed to PR #161 with GitHub tests and Vercel Preview green; not merged or released. |
| Panchangam | `cbf7ea8476a8e0da123b405c269f351a91bbdc51`; restore `archive/guest-attribution-contract-2026-09-03-cbf7ea8` | The client requires allowlisted structured attribution and visibly renders safe provider/data links beside place results; runbook and reference documentation now match the hardened service boundary. | 406 frontend tests, both TypeScript configurations, 1,464 Python tests, and production/docs build passed: 62 computation routes, 11 Mermaid diagrams, and 3 landing artifacts. UI owner sign-off and hosted checks remain required. |
| Licensing audit | `dd90f8003af5df89689e65e24448f88cd6e8fae1`; restore `archive/licensing-audit-2026-09-03-dd90f80` | A technical inventory now records 25 TCU PyPI releases/50 artifacts, direct imports, current and separately reachable deployments, artifact hashes, notices, and unresolved counsel/rights-holder questions. | 1,464 Python tests passed. The report reaches no legal conclusion and is not pushed. |

The Astro checkpoint corrects two points that were open in the original
assessment: named provider adapters and a normalized shared geocoder cache now
exist in code. It also prevents guest rollout from silently breaking the
existing signed-in profile journey: authenticated managed geocoding requires
the independent exact value `AUTH_PROFILE_MANAGED_GEOCODER_ENABLED=true`.
When enabled, each managed signed-in lookup is counted against a distributed
ten-call-per-user limit and the same 60-call-per-minute fleet budget used by
guest place search. Upstash or the configured compatible Redis provider is now
explicitly disclosed as a processor of HMAC-pseudonymous keys and normalized
location results retained for at most 24 hours.

These are implementation checkpoints, not release clearance. Still open are
the Swiss/PySwissEph written posture and remediation decision (#231, #444,
#445, #449), managed provider/Redis selection and terms (#233), owner-approved
credentials and quota posture, exact pair-bound hosted Preview design and
certification (#448), PR review/merge approval, UI screenshot sign-off, and
separate Production deployment and activation approvals. No public flag,
environment value, deployment, alias, or branch was changed by this addendum.
