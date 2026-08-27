# Maintenance Runbook

The "what do I actually do" reference for running this project.
Read this when you sit down after weeks away and don't remember the
muscle memory.

> See also: [`ARCHITECTURE.md`](ARCHITECTURE.md) for the layer cake,
> [`CLAUDE.md`](CLAUDE.md) for the working agreement,
> [`docs/reference/06-roadmap-and-backlog.md`](docs/reference/06-roadmap-and-backlog.md)
> for the current roadmap. The older improvement plan is retained as a
> historical decision log and contains intentionally stale phase-era detail.

## Table of contents

1. [Release a new version](#release-a-new-version)
2. [The monthly cron map](#the-monthly-cron-map)
3. [Add a city](#add-a-city)
4. [Add a festival](#add-a-festival)
5. [Verify against Drik Panchang](#verify-against-drik-panchang)
6. [Respond to a Dependabot PR](#respond-to-a-dependabot-pr)
7. [Respond to a pip-audit CVE finding](#respond-to-a-pip-audit-cve-finding)
8. [Fix a broken deploy](#fix-a-broken-deploy)
9. [Open emergencies](#open-emergencies)

---

## Release a new version

The publish workflow is **automated end-to-end from a tag push**, with
two gates that fail fast if anything is out of sync. You only need to
bump three files and push a tag.

### Pre-flight (~5 minutes)

1. **Promote `[Unreleased]` -> `[<version>]` in `CHANGELOG.md`**, adding
   the date (yyyy-mm-dd). The Keep-a-Changelog sections (Added /
   Changed / Fixed / Performance / Security) should all carry PR links
   for traceability. Reset `[Unreleased]` to empty above it.
2. **Bump `pyproject.toml:7` `version`** to the new value.
3. **Bump `server.json`** — both `version` (top-level, line 9) AND
   `packages[0].version` (line 15). They must match.
4. Run the suite locally: `python -m pytest tests/ -q`. Must be green.
5. Commit all three on master (or via PR if you want a review trail).

### Tag and push

```bash
git tag vX.Y.Z
git push origin master --tags
```

That triggers `.github/workflows/publish.yml`. The workflow will:

1. Verify the tag shape is `vMAJOR.MINOR.PATCH`.
2. Assert `pyproject.toml.version == server.json.version == server.json.packages[0].version == tag (stripped of "v")`.
3. Extract the `## [<version>]` section from `CHANGELOG.md` (fails if
   missing or empty).
4. Run `pytest tests/`.
5. `python -m build` (creates `dist/*.whl` + `dist/*.tar.gz`).
6. OIDC-publish to PyPI as `mcp-server-panchangam`.
7. Create a GitHub Release with the CHANGELOG section as the body and
   the wheel + sdist attached.

### If a gate fails

- **Version mismatch** — fix the offending manifest, commit, re-tag:
  `git tag -d vX.Y.Z; git push --delete origin vX.Y.Z; <fix>; git tag vX.Y.Z; git push --tags`.
- **CHANGELOG missing/empty** — promote `[Unreleased]` -> the version,
  commit, re-tag.
- **Tests fail** — the most likely culprit is something that wasn't
  exercised locally (Playwright smoke). Reproduce locally, fix, re-tag.

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

## Add a city

1. Find the canonical city name, latitude, longitude, timezone.
   Cross-reference with Wikipedia / Google for accuracy.
2. Add an entry to the `CITIES` table (search `cities.py` or
   `telugu_panchangam/mcp/cities.py` — whichever holds the 22-city
   list).
3. Add an entry to `CITY_GROUPS` in `src/main.ts` so it appears in
   the city selector and the Subscribe card.
4. Add a test: pick the city, run `engine.calculate(date, city)` for a
   recent date, eyeball the output. Cross-check at least sunrise/sunset
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
   from telugu_panchangam.engines import DrikGanitaEngine
   day = DrikGanitaEngine().calculate(date(2026, 6, 15), 'Hyderabad')
   print(day.tithi.name, day.tithi.end_time)
   print(day.nakshatra.name, day.nakshatra.end_time)
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

Dependabot opens PRs weekly (Monday 06:00 IST) for `pip` deps and
GitHub Actions. The flow:

1. **Read the PR title** — it says what's bumping and from where to
   where. Major bumps need more care than patch/minor.
2. **Read the changelog link** — Dependabot includes one. Look for
   breaking changes mentioned.
3. **Check CI** — the matrix runs on 3.10–3.13. CodeQL + pip-audit
   also run.
4. If CI is green and the changelog reads clean, **merge with
   squash**. Dependabot auto-deletes its branch (the
   `delete-branch-on-merge` setting handles it).
5. If CI fails — read the failure. Most common cause: API change in a
   transitive. Either pin to the prior version with an explicit ceiling
   in `pyproject.toml`, or fix the call site.

### For GitHub Actions bumps specifically

Actions are pinned to SHAs with the tag in a comment (see PR #84).
Dependabot bumps both the SHA and the comment together. Just merge.

---

## Respond to a pip-audit CVE finding

`pip-audit` runs on every PR + push to master + weekly Monday 09:00 UTC.
A failure means a CVE was disclosed in our dependency closure.

1. Read the CVE — pip-audit links to the advisory. Understand the
   attack surface (is it network-facing? Does our usage trigger it?).
2. Check if a fixed version exists. If yes:
   - Bump the dep in `pyproject.toml` (the `>=` floor goes up to the
     fixed version).
   - Install `requirements.txt`, uninstall only the unpublished local project
     distribution (`pip uninstall --yes mcp-server-panchangam`), then audit the
     remaining dependency environment exactly as CI does:
     `pip-audit --local --strict`.
   - Refresh the Python 3.11 reproducibility snapshot (it is not the
     security gate):
     `uv pip compile pyproject.toml --extra test --python-version 3.11 --upgrade --generate-hashes -o requirements.lock`.
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
- [`CLAUDE.md`](CLAUDE.md) — working agreement
- [`SECURITY.md`](SECURITY.md) — vulnerability disclosure policy
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution flow
- [`docs/tracking/improvement-plan.md`](docs/tracking/improvement-plan.md) — phased roadmap
