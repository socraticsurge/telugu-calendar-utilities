# AGPL public-source release alignment

Assessment date: 2026-09-04 (Asia/Kolkata)

This record captures the engineering release posture selected for the
Panchangam guest-calculation stack. It is not legal advice.

## Decision and authoritative basis

The owner selected the AGPL-compatible public-source route for today's release.

- Astrodienst states that a developer using any part of Swiss Ephemeris must
  choose either the AGPL or a Professional License before distributing
  software or activating a public service, and describes the AGPL path as
  applying AGPL or a compatible licence to the whole project:
  <https://www.astro.com/swisseph/swisseph.htm>
- PySwissEph identifies itself as AGPL-3.0 and describes Swiss Ephemeris as
  dual licensed: <https://github.com/astrorigin/pyswisseph>
- GNU AGPL section 13 requires a modified network program to give remote users
  a prominent opportunity to receive the corresponding source:
  <https://www.gnu.org/licenses/agpl-3.0.html#section13>

## Release candidates

| Component | Required posture | Candidate evidence |
|---|---|---|
| Telugu Calendar Utilities / MCP package | AGPL-3.0-or-later metadata, full license, PySwissEph and Swiss notices, public source link | `codex/agpl-release-alignment`; version `1.14.0`; calculation behavior unchanged |
| DashaFlow calculation sidecar | AGPL-3.0-or-later, preserved third-party notices, public exact-revision source offer | [DashaFlow PR #3](https://github.com/socraticsurge/dashaflow-sidecar/pull/3), head `00f8fe26444cd8e63511af5d0d54ae41d15c419a` at assessment time |
| Astro Chaganti gateway | AGPL-3.0-or-later, visible source link, guest/health exact-revision source offer | `codex/agpl-release-alignment` from Astro `development` |

Earlier TCU and Astro copies retain the licence grants conveyed with those
copies. The change governs the current release; it does not revoke an earlier
grant.

## Candidate verification

- TCU: `python -m pytest tests/` — 1,467 passed, including the real-browser
  suite.
- TCU: `npm run build` — Vite site, VitePress documentation, and output
  contract all passed.
- TCU: `python3 -m build` — sdist and wheel built successfully; wheel metadata
  reports `License-Expression: AGPL-3.0-or-later` and includes both `LICENSE`
  and `THIRD_PARTY_NOTICES.md`.
- TCU: the desktop source-offer screenshot is retained at
  `release-evidence/screenshots/agpl-source-offer-desktop.png`.
- Astro: 840 Vitest tests, lint, palette check, route check, and the production
  Next.js build passed on the candidate branch.

## Non-negotiable activation gates

1. Merge reviewed release candidates without squashing away the revision used
   in each deployment record.
2. Make the Astro and DashaFlow source repositories publicly readable before
   enabling any public calculation route.
3. Deploy exact commits and verify both health/source offers resolve without
   authentication to those exact public revisions and their licence files.
4. Publish TCU version `1.14.0` only from the reviewed source revision, then
   verify the PyPI project page presents the AGPL metadata and source link.
5. Record the final PR, commit, repository-visibility, deployment, health, and
   PyPI evidence in issues #231, #445, and #449 before closing them.
6. Keep guest calculation flags off until the separate provider, limiter,
   Preview, and rollback gates in the production-activation runbook pass.

## Scope boundary

This alignment changes licensing, notices, disclosure, and release metadata.
It does not change the frozen computation engines, ICS contract, calculation
results, secrets, Vercel settings, repository visibility, or production flags.
