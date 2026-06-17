# Maintenance session — 2026-06-17

Four tasks requested by owner. Do one by one; owner is away ("walk away").

## Tasks
1. **Changelog** — dig through commit history, bring CHANGELOG.md up to date.
2. **Remove google-labs-jules[bot]** from contributor list — recommit its work
   under `Socraticsurge <cvk.atreya@gmail.com>` (same method as last time).
3. **Explain dependabot** — keep it; tell owner what it is.
4. **Strong documentation + diagrams** — mindmaps/feature catalogs, deep visibility
   into engines and features (computational + user-exposed). Save NEW docs locally
   (gitignored); revise on-GitHub docs in place where appropriate.

## Key facts discovered
- Default branch = `master`. GitHub contributor LIST derives from default branch.
- 15 jules-authored commits are on master (2026-06-15 cleanup PRs). 40 jules commits
  exist across all refs, but the extra 25 are on **local-only `[gone]` branches** —
  invisible to GitHub, no action needed.
- Tags descending from jules commits (SHAs will shift): **v1.8.0, v1.9.0, v1.10.3, v1.10.4**.
- dependabot[bot] = 2 commits (KEEP). Config: `.github/dependabot.yml` (weekly pip +
  github-actions bumps). "Vinay Chaganti <84312058+socraticsurge@users.noreply.github.com>"
  = owner's own GitHub web-commit identity (74 commits) — legitimate, leave it.
- `publish.yml` triggers on `push: tags v*.*.*` → moving tags would re-fire it.
  Mitigation: `gh workflow disable/enable "Publish to PyPI"` around the tag push.

## Safety baseline (pre-rewrite)
- OLD master HEAD: 427369ea3739d712bd350309efeb3435af268357 (tree abc49b0)
- Backup branch: `backup/pre-jules-rewrite-20260617`
- OLD tags: v1.8.0→commit 17060c9 (tree 419b1324) · v1.9.0→cc9cf07 (tree 3fb2e054)
  · v1.10.3→45069ae (tree 371cb13) · v1.10.4→427369e (tree abc49b0)
- Invariant to verify after rewrite: every tree SHA unchanged (only author/committer
  metadata changes — zero code change).

## Harness constraint discovered (IMPORTANT)
- This Claude Code session's Bash tool BLOCKS `git push --force` AND `git reset --hard`
  on protected branches ("History-destroying operations are forbidden").
- The jules rewrite is DONE locally + verified (master = 045d828, jules-free, trees
  byte-identical). origin/master still = 427369e (original). I cannot push or revert.
- Plan: stack changelog + docs commits on the rewritten local master. Owner runs the
  final force-push from their own shell (not bound by these guards) to deliver all of it:
    git push --force-with-lease origin master
    git push --force origin v1.8.0 v1.9.0 v1.10.3 v1.10.4
  (Re-pointed tag commits: v1.8.0=bdfc86c v1.9.0=218d981 v1.10.3=0eaf2da v1.10.4=045d828)
  Backup of original: branch `backup/pre-jules-rewrite-20260617` (= 427369e).
- publish.yml was temporarily disabled then RE-ENABLED (active now) — no state left changed.

## Progress
- [x] Task 2 — jules rewrite PUSHED & verified on remote (2026-06-17). origin/master
      = ef3a818, zero jules across all origin refs, Contributors API shows only
      socraticsurge(303) + dependabot(2). Owner force-pushed after temporarily
      toggling master's allow_force_pushes (GitHub branch protection blocked it).
- [x] Task 1 — changelog reconciled + backfilled v1.0.5–v1.7.1 (commit edf3192)
- [x] Task 3 — dependabot explained in chat (keep as-is)
- [x] Task 4 — docs/reference/ deep-dive set (7 files, gitignored) + .gitignore
      hygiene commit 135d043. Flagged ARCHITECTURE.md vs CLAUDE.md frozen-core
      inconsistency for owner.

## Local commits awaiting owner force-push (on rewritten master)
- ef3a818 docs(architecture): reaffirm frozen core; EngineCore parked
- 135d043 chore(repo): gitignore docs/reference/ + node_modules/
- edf3192 docs(changelog): reconcile + backfill
- 045d828 release: 1.10.4 (rewritten — jules-free tip)

## Frozen-core inconsistency — RESOLVED 2026-06-17
Owner chose "keep frozen." ARCHITECTURE.md corrected (committed ef3a818);
CLAUDE.md (gitignored, local) gained a matching "EngineCore parked, not active"
note. Both docs now agree. See memory [[frozen-core-doc-inconsistency]].
Owner runs from their own shell (harness blocks force-push here):
  git push --force-with-lease origin master
  git push --force origin v1.8.0 v1.9.0 v1.10.3 v1.10.4
Backup: branch backup/pre-jules-rewrite-20260617 (= original 427369e).
