# Decisions

## 2026-07-22 — Keep the Vercel function dependency closure runtime-only

- **Decision:** This supersedes the optional-adapter dependency decision below.
  FastAPI is a direct package dependency because the HTTP adapter is
  now a supported runtime surface. Vercel's project-level install and frontend
  build are disabled for the separate API project; the Python function builder
  installs the direct runtime dependencies from `pyproject.toml`. The existing
  `requirements.txt` remains the CI/local shim for `.[test]`.
- **Why:** Vercel otherwise performs a project install (including test extras), a
  Vite build, and a second Python-function install. That duplicated dependency
  closure exceeded the platform's function bundle limit and shipped tools that
  the API cannot use at runtime.
- **Safety:** The calendar engines, generators, workflows, and existing static
  deployment remain unchanged. Local/CI installs still include pytest, while the
  staging API bundle includes only declared runtime packages.
- **Revisit when:** Vercel adds first-class selection of Python optional extras
  for function builds, or the HTTP adapter becomes a separately packaged service.

The adapter uses Vercel's framework-level `app.py` entrypoint. A file under
`api/index.py` is a file-based function whose externally routable path includes
that location; the root entrypoint preserves the adapter's versioned `/v1/*`
contract without rewrites or duplicate route aliases.

Append-only. Deviations, scope additions, override usages, with rationale.

## 2026-06-10 — `sync_tracker_on_task.py` always passes `tests_passed=True`

The PostToolUse hook for `TaskUpdate(completed)` cannot independently verify
that a task's tests passed — Claude Code does not pass test results through
the `TaskUpdate` tool input, and the hook has no project-specific knowledge of
how to run tests. As a v1 simplification, `sync_tracker_on_task.py` calls
`sync_task_completion(..., tests_passed=True)` unconditionally, so a story
rolls up to `done` whenever all its tasks are marked `completed`.

This is a deviation from spec section 5 ("Status `done` requires underlying
tasks' tests to pass — not on self-report"). The TDD discipline enforced by
`superpowers:subagent-driven-development` (tests written and run by the
implementer subagent, then re-verified by an independent reviewer subagent
before `TaskUpdate(completed)` is called) is the actual enforcement
mechanism in practice. A future improvement could have the sync hook shell
out to a project-configured test command before rolling up story status, but
that is out of scope for this template.

## 2026-07-22 — FastAPI is an optional adapter dependency

Astro Chaganti needs an interactive, authenticated computation boundary while
the static GitHub Pages site, calendar feeds, Actions, and MCP/PyPI consumers
remain independently releasable. `fastapi>=0.117.1,<1.0` is therefore added as
the `api` optional extra and installed by the repository development
requirements. The HTTP code lives only in new `api/` and
`telugu_panchangam/api/` modules that consume existing MCP-tool functions; no
frozen engine or ICS module is modified. `httpx>=0.28` is made explicit in the
test extra because FastAPI's contract tests use an in-process HTTP client.

The adapter is server-to-server only: bearer authentication, no browser CORS,
bounded Pydantic models, private/no-store responses, redacted errors, and
request-local participant labels are part of contract v1 rather than deferred
hardening.

## 2026-07-22 — Reserve production API capacity without activating it

The Vercel project `telugu-calendar-api-production` is reserved during Gate 9
preparation, but it has no deployment, secret or traffic. This separates project
provisioning from release authority: the reviewed API can later receive a fresh
service token and be tested on an isolated deployment before Astro production
references it. GitHub Pages, feeds and Actions remain the active publishers, and
only an explicit Gate 9 go/no-go may authorize the consumer cutover.

## 2026-07-22 — Activate the isolated API, not the Astro consumer

The reviewed contract is deployed to `telugu-calendar-api-production` as
`dpl_2WpDHW73JjfAc6ENG3L88vdYNL92` with a fresh sensitive production token.
The same token and stable API URL are configured server-side for a future Astro
production build. Live health, auth, catalog, Panchangam, Rasi Phalalu,
Tarabalam and participant-aware Muhurtam checks pass. This activates only the
isolated dependency: Astro's release switch and aliases are unchanged, and
GitHub Pages, feeds and Actions remain the public service until explicit Gate 9
go/no-go approval.
