# Maintenance Runbook

The "what do I actually do" reference for running this project.
Read this when you sit down after weeks away and don't remember the
muscle memory.

> See also: [`ARCHITECTURE.md`](ARCHITECTURE.md) for the layer cake,
> [`AGENTS.md`](AGENTS.md) for the working agreement,
> [`docs/reference/06-roadmap-and-backlog.md`](docs/reference/06-roadmap-and-backlog.md)
> for architectural roadmap context. The live work queue is the
> [GitHub Project](https://github.com/users/socraticsurge/projects/2), backed by
> [repository Issues](https://github.com/socraticsurge/telugu-calendar-utilities/issues).
> The older improvement plan is retained as a historical decision log and
> contains intentionally stale phase-era detail.

## Table of contents

1. [Release a new version](#release-a-new-version)
2. [The monthly cron map](#the-monthly-cron-map)
3. [The CI event model](#the-ci-event-model)
4. [Add a city](#add-a-city)
5. [Add a festival](#add-a-festival)
6. [Compare Drik calculations against Drik Panchang](#compare-drik-calculations-against-drik-panchang)
7. [Respond to a Dependabot PR](#respond-to-a-dependabot-pr)
8. [Respond to a pip-audit CVE finding](#respond-to-a-pip-audit-cve-finding)
9. [Fix a broken deploy](#fix-a-broken-deploy)
10. [Open emergencies](#open-emergencies)

---

## Release a new version

A version bump on a development branch does not publish a package.
Publication starts when a release tag is pushed and the publish workflow passes.
For the current recorded development and published versions, see
[`CHANGELOG.md`](CHANGELOG.md).

### Pre-flight

1. Prepare the release on a feature branch from current `master`; follow
   [`CONTRIBUTING.md`](CONTRIBUTING.md) for the locked development environment.
2. Promote `[Unreleased]` to `[<version>]` in `CHANGELOG.md`, adding the date
   (yyyy-mm-dd) and PR links for traceability; leave a new empty `[Unreleased]`
   section above it.
3. Set `project.version` in `pyproject.toml` and both `version` and
   `packages[0].version` in `server.json` to the release version.
   Run `uv lock` and include the root-package version change in `uv.lock`.
4. Run `uv run python tools/verify_project.py`; every gate must pass.
   This includes the required full `python -m pytest tests/` suite, frontend
   coverage, lint, documentation checks and the production build.
5. Review the manifest, lockfile and changelog diff, then open a PR and merge
   only after the required checks pass; do not commit directly to `master`.

### Tag and publish

After the release PR is merged and its `master` checks pass, fetch the merged
revision and verify its version and changelog before tagging it:

```bash
git fetch origin master
git tag vX.Y.Z origin/master
git push origin refs/tags/vX.Y.Z
```

Push only the intended release tag. `.github/workflows/publish.yml` will:

1. Verify the tag shape is `vMAJOR.MINOR.PATCH`.
2. Check that the tag matches all three manifest version fields.
3. Extract a nonempty `## [<version>]` section from `CHANGELOG.md`.
4. Install locked dependencies and run `pytest tests/`.
5. Build the wheel and sdist, then run `tools/verify_release_artifacts.py`.
6. Publish `mcp-server-panchangam` to PyPI using OIDC.
7. Create a GitHub Release with the changelog section and distribution files.

Confirm the workflow succeeded and both PyPI and GitHub show the intended
version; a pushed tag alone is not publication evidence.

### If a gate fails

- **Version mismatch or missing changelog** — correct the source on a feature
  branch, rerun verification, and merge the fix before attempting publication.
- **Tests or artifact verification fail** — reproduce the failing step locally
  and correct it through the same review path.
- **Publication partially succeeds** — inspect PyPI and the GitHub Release before
  retrying; an uploaded PyPI version cannot be replaced.
- Do not delete or move an existing release tag as routine recovery.
  Use a new patch version for corrected published artifacts; an unchanged
  workflow may be rerun for a transient failure after checking what succeeded.

### Patch vs minor vs major

Project follows [SemVer](https://semver.org/). For this project:

| Change | Bump |
|---|---|
| Engine output changes by more than DP-verification tolerance for any anga / window / festival | **MAJOR** |
| New engine method, new MCP tool, new generator, new festival rule | **MINOR** |
| Bug fix in an engine that brings output closer to DP, doc update, dependency bump, refactor with no behaviour change | **PATCH** |

When in doubt, MINOR. The cost of an unwarranted major is small; the
cost of an unwarranted patch that breaks subscribers' assumptions is
the painful one.

---

## The monthly cron map

Three workflows run on the 1st of every month, staggered to avoid
collisions on the gh-pages branch. They share a `gh-pages-deploy`
concurrency group so they queue cleanly if one runs long.

| UTC time | Workflow | What it does |
|---|---|---|
| 02:00 | `generate.yml` | Generates 18 months of `.ics` feeds for 22 cities × 3 systems (66 files) into `public/feeds/`. Rebuilds the landing page assets. Full deploy. |
| 02:30 | `gochara.yml` | Builds `gochara.json` (grahas + transit tables for the next ~30 days). Layered deploy (`keep_files: true`). |
| 02:45 | `lagna.yml` | Builds per-city `<city>-lagna.json` files with lagna transitions for the next ~30 days. Layered deploy. |

**Smoke test after a cron run:**

```bash
curl -sI https://panchangam.astrochaganti.com/feeds/hyderabad-drik.ics | head -1
curl -s  https://panchangam.astrochaganti.com/gochara.json | jq '.computed_at'
curl -s  https://panchangam.astrochaganti.com/feeds/hyderabad-lagna.json | jq '.[0]'
```

Each should return 200 with content dated within the last few days.

**If a cron fails** — most common cause is a flaky dep resolution.
Re-run the workflow from the Actions tab; if it fails twice, look at
the log. The pre-deploy `pytest tests/` step catches most regressions
before the deploy step runs.

---

## The CI event model

CI listens to feature-branch and `master` pushes plus pull requests. A push
therefore validates a new branch before a PR exists, and the merge commit is
validated again on `master`. Once a PR is open, GitHub can emit both push and
pull-request events for the same commit. Push and pull-request events use
separate concurrency groups. A successful `CI scope` job checks whether a
pushed commit is already associated with an open PR. If so, the branch suite is
skipped and the pull-request suite owns that commit. This avoids both duplicated
matrices and canceled checks on active PRs. Branch-push jobs are additionally
named `branch test (3.10)` through `branch test (3.13)` and
`branch frontend-and-browser`; pull-request jobs retain the protected names
below.

The matrix job names remain `test (3.10)` through `test (3.13)`, so the four
backend compatibility contexts are unchanged. Node, the production Vite build,
Vitest, Chromium, and the browser smoke suite run once in the separate required
`frontend-and-browser` context. Security supplies the other required contexts:
`CodeQL (Python)` and `pip-audit (requirements.txt)`. The protected quality
gates also include CodeScene, `Sonar analysis`, and the SonarCloud gate; consult
the current branch-protection settings for their exact context names.

When introducing or renaming a job, push the branch and wait for the new check
to pass before adding its exact name to branch protection. Do not merge while a
new coverage-bearing job is not yet required.

If duplicate matrices both complete for a commit that was pushed after its PR
opened, inspect the `CI scope` output and the commit-to-pulls API response. The
push event should complete only the scope job, with its branch jobs skipped;
the pull-request event should complete the protected suite.

---

## Add a city

1. Find the canonical city name, latitude, longitude, timezone.
   Cross-reference with Wikipedia / Google for accuracy.
2. Add a `Location` entry to `CITIES` in `telugu_panchangam/cities.py`.
3. Add the city to `CITY_GROUPS` and its coordinates/timezone to `CITY_LOCATIONS`
   in `src/data/cities.ts`; preserve parity with the Python table.
4. Add a test using `engine.calculate(date, location)` with that `Location`.
   Cross-check at least sunrise/sunset on several dates and more than one city
   against [drikpanchang.com](https://drikpanchang.com) for that
   city + date.
5. Confirm the next monthly cron will pick it up (it iterates the
   `CITIES` table — if the entry shape is right, no further wiring
   needed).
6. Open a PR. The CI matrix runs on 3.10–3.13, plus the deploy-drift
   guard.

---

## Add a festival

The festival rules live in `telugu_panchangam/engines/base.py:_festivals()`.
The pattern is:

```python
# Inside _festivals(), find the deciding-moment list that fits.
# Five moments are supported today (Phase 6 plans more):
_SUNRISE     = [...]   # festival fires on tithi at sunrise
_MADHYAHNA   = [...]   # midday
_APARAHNA    = [...]   # afternoon (~13:30–16:30)
_PRADOSHA    = [...]   # twilight
_NISHITA     = [...]   # midnight
```

1. Identify which moment determines the festival. Drik Panchang's
   reference text usually states this (e.g. "Varalakshmi Vratam is
   observed on the Friday before the Pournami in Shravana — aparahna
   determines"). If your festival needs a moment not in the
   vocabulary, **stop and propose adding the moment** — that's an
   engine surface change requiring more care.
2. Add the festival to the matching list with the exact name as it
   should appear in ICS / panchangam output.
3. Add a test in `tests/test_festivals.py` with at least one
   DP-verified date for at least one Indian city. Format follows the
   existing pattern; verify against
   [drikpanchang.com/festivals](https://www.drikpanchang.com) day
   pages.
4. Add to `CHANGELOG.md` under `[Unreleased]` -> Added.
5. Open PR. Engine changes pass through the same CI matrix.

---

## Compare Drik calculations against Drik Panchang

Drik Panchang ([drikpanchang.com](https://drikpanchang.com)) is the
project's external comparison reference for the **Drik calculation system**.
It does not establish scriptural provenance for interpretive or Muhurtam
rules, and it is not the comparator for intentionally distinct Surya
Siddhanta or Vakya outputs. Record exact city, date, values, tolerance and URL;
resolve discrepancies by inspecting both implementations rather than treating
a website label as textual authority.

### Manual cross-check

1. Pick a city and date. The day-page URL pattern is roughly
   `drikpanchang.com/?date=YYYY-MM-DD&city=<city>`. Hyderabad is a
   reliable default.
2. Note the values displayed: Tithi, Nakshatra, Yoga, Karana,
   Sunrise/Sunset, Rahu/Yama/Gulika, festivals, eclipse data.
3. Run our engine: in a Python shell,

   ```python
   from datetime import date
   from telugu_panchangam.cities import CITIES
   from telugu_panchangam.engines.drik import DrikGanitaEngine
   hyderabad = next(city for city in CITIES if city.name == 'Hyderabad')
   day = DrikGanitaEngine().calculate(date(2026, 6, 15), hyderabad)
   print(day.tithi.name, day.tithi.end)
   print(day.nakshatra.name, day.nakshatra.end)
   ```

4. Compare. Tolerances:
   - **Sunrise / sunset**: < 1 minute
   - **Tithi / nakshatra / yoga end time**: < 2 minutes
   - **Rahu Kalam / Abhijit / Yamagandam**: < 2 minutes
   - **Festival dates**: exact match (any mismatch is a bug)

### When DP and we disagree

- If it's a timing difference within tolerance — log it, no action.
- If it's a timing difference > tolerance — first check whether DP
  uses a different ayanamsa (Phase 6 makes this a parameter). If
  ayanamsa is the cause, document it.
- If it's a festival date — open a `festival-mismatch` issue with the
  date, city, our output, DP's output, and the DP day-page URL.

---

## Respond to a Dependabot PR

Dependabot opens PRs weekly (Monday 06:00 IST) for Python, npm, and GitHub
Actions dependencies. The flow:

1. **Read the PR title** — it says what's bumping and from where to
   where. Major bumps need more care than patch/minor.
2. **Read the changelog link** — Dependabot includes one. Look for
   breaking changes mentioned.
3. **Check all required checks** — Python 3.10–3.13, frontend/browser,
   CodeQL, pip-audit, Sonar and CodeScene must pass. Check lockfile consistency
   and coupled dependencies, such as Vitest and its coverage provider.
4. If CI is green and the changelog reads clean, **merge with
   squash**. Dependabot auto-deletes its branch (the
   `delete-branch-on-merge` setting handles it).
5. If CI fails — read the failure. For Python updates, adjust the bound in
   `pyproject.toml` and regenerate `uv.lock`; for npm, update `package.json`
   and `package-lock.json` together. Otherwise fix the affected call site.

### For GitHub Actions bumps specifically

Actions are pinned to SHAs with the tag in a comment (see PR #84).
Dependabot bumps both the SHA and the comment together. Review compatibility
and required checks; workflow changes still require explicit owner approval
under `AGENTS.md`.

---

## Respond to a pip-audit CVE finding

`pip-audit` runs on every PR + push to master + weekly Monday 09:00 UTC.
A failure means a CVE was disclosed in our dependency closure.

1. Read the CVE — pip-audit links to the advisory. Understand the
   attack surface (is it network-facing? Does our usage trigger it?).
2. Check if a fixed version exists. If yes:
   - Bump the dep in `pyproject.toml` (the `>=` floor goes up to the
     fixed version).
   - Refresh the authoritative resolution:
     `uv lock --upgrade-package <distribution-name>`.
   - Reproduce the CI audit from a disposable environment:
     `uv sync --locked --only-group audit --no-install-project --no-build`,
     then `uv export --quiet --locked --no-dev --no-emit-project --output-file .audit-requirements.txt`,
     then `uv run --no-sync pip-audit --strict --disable-pip --require-hashes -r .audit-requirements.txt`.
     Delete the generated `.audit-requirements.txt` after the check; it is a
     transient view of `uv.lock`, not another lockfile.
   - PR + merge.
3. If no fixed version exists yet:
   - Assess severity. Most CVEs in non-network-facing libs (timezone
     data, etc.) are low-severity for us.
   - If low — document in `SECURITY.md` and `--ignore-vuln <id>` in
     the workflow until upstream patches.
   - If high — vendor a patch or swap the dep.
4. Follow the SECURITY.md 72h ack promise — even if the fix lands the
   same day, file the incident note.

---

## Fix a broken deploy

The site hasn't loaded / the feeds are stale. Diagnostic order:

1. **Is the cron failing?** Check the Actions tab. If the last
   `generate.yml` run failed, that's the source.
2. **Is the deploy-drift guard catching anything?** `pytest tests/test_deploy_drift.py -v`
   locally. If yes, follow its remediation in the assertion message.
3. **Did the CNAME drop?** `pytest tests/test_deploy_drift.py::test_deploy_workflow_pins_cname`.
   If any workflow lost the `cname:` line, restore it before any other
   deploy fires.
4. **Is gh-pages itself corrupted?** Last-resort recovery: trigger
   `generate.yml` manually from the Actions tab with
   `workflow_dispatch`. This does a full rewrite of `public/feeds/` +
   landing page assets and pushes.

---

## Open emergencies

| If... | Then... |
|---|---|
| The public site shows 404 / wrong CNAME | First check `tests/test_deploy_drift.py` locally. If the cname was dropped in a recent merge, revert that merge and let the next deploy republish. Worst case: manually create a `CNAME` file with `panchangam.astrochaganti.com` and push to gh-pages directly. |
| PyPI shows the wrong version | The publish workflow's version-sync gate prevents this if you tagged via the workflow. If somehow a bad version landed: yank the bad release on PyPI (`pip-keepers` allows yanking; not deleting), bump the version, re-release. |
| A festival is reported on the wrong date | This is a real engine bug. Reproduce locally, cross-check DP, write a regression test pinning the correct date, fix the rule in `base.py`, ship a PATCH release. |
| Subscriber webcal URLs stop resolving | Check DNS for `panchangam.astrochaganti.com`, then check gh-pages branch has the `CNAME` file. If CNAME file is missing, the `cname:` line in the deploy workflow regenerates it on next deploy. |
| The MCP server fails to start on `uvx mcp-server-panchangam` | Reproduce locally. Most common cause: a new transitive dep doesn't install on a fresh env. Fix and PATCH-release. |

---

## See also

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — module layering, engine API contract
- [`AGENTS.md`](AGENTS.md) — working agreement
- [`SECURITY.md`](SECURITY.md) — vulnerability disclosure policy
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution flow
- [`docs/tracking/improvement-plan.md`](docs/tracking/improvement-plan.md) — phased roadmap
