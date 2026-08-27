# GitHub Pages retention and rollback

Status: implementation ready in issue #153; no live history has been rewritten
and no generated file has been deleted. Activation requires merge approval and
a separately approved first deployment.

## Why history is bounded

`gh-pages` is a publication branch, not an audit archive. Its source inputs,
calculation rules and tests live on `master`; generated output can be reproduced.
Every Pages workflow therefore uses the pinned v4 deployment action with both
`keep_files: true` and `force_orphan: true`. Version 4 supports this combination:
the current live tree is preserved for layered deploys, while each successful
deployment replaces the prior publication commit with a new orphan commit.

## Measured baseline — 2026-08-27

The local repository reported a 96.38 MiB pack across all local refs. A clean,
aggressively packed rehearsal containing `master`, release tags and `gh-pages`
measured 77.79 MiB; the same repository without Pages history measured only
2.36 MiB.

`gh-pages` contained 112 unrelated deployment commits from 2026-06-10 through
2026-07-22. Its live tree contained 281 files and 89,082,209 bytes:

| Live category | Files | Bytes | Required retention |
|---|---:|---:|---|
| Panchangam feeds under `feeds/` | 220 | 84,606,415 | Keep every currently published ICS feed and current per-city Lagna JSON. The feed horizon is the product contract. |
| Built assets | 22 | 3,496,777 | Keep the current production build only. |
| Rasi Phalalu | 32 | 768,997 | The UI reads today only. Retain a short operational window; deleting older live files is a separate approval-gated change. |
| Root JSON | 1 | 23,081 | Keep the current Gochara snapshot only. |
| Other (`index.html`, `CNAME`, etc.) | 6 | 186,939 | Keep the complete current site shell and custom-domain files. |

Across historical Pages commits, 1,398 unique blobs occupied 812,145,432
uncompressed bytes. Panchangam feed history accounted for 801,319,230 bytes,
so repeated generated feeds—not source history—were the dominant cause.

## Rehearsal result

A bare clone containing only `master`, tags and `gh-pages` was used; the live
repository was untouched.

1. A complete backup bundle of the original Pages tip
   `c55ddf9cebea32aa9062eff331165f8a61dfbafb` was created and verified.
2. A parentless commit was created from the exact live tree
   `5968de561b00bc6f27137bbf11b7a3d2ac6d1fb5`.
3. `git diff` confirmed that the old and new commits had identical trees;
   `CNAME` still contained `panchangam.astrochaganti.com`.
4. After unreachable objects were pruned and repacked, pack size fell from
   77.79 MiB to 13.43 MiB, an 82.7% reduction.
5. Rollback from the 76 MiB backup bundle restored the exact original tip and
   tree, and `git fsck --full --no-dangling` passed.

The first live deployment may not immediately reduce GitHub-reported storage;
unreachable server objects are reclaimed on GitHub's schedule. New clones stop
requesting the old Pages history once the ref becomes orphaned.

## Live artifact checks

Before the rehearsal, each canonical URL returned HTTP 200:

- site root: `https://panchangam.astrochaganti.com/`
- Panchangam feed: `/feeds/hyderabad-drik.ics`
- Gochara: `/gochara.json`
- Lagna: `/feeds/hyderabad-lagna.json`
- Rasi Phalalu sample: `/rasi_phalalu/2026-07-22.json`

After the first approved live deployment, repeat those checks, confirm the
`CNAME` file and compare the published tree manifest before removing any local
backup.

## First activation

Run these steps only with explicit owner approval:

```bash
git fetch origin gh-pages
git branch backup/gh-pages-YYYYMMDD origin/gh-pages
git bundle create gh-pages-YYYYMMDD.bundle backup/gh-pages-YYYYMMDD
git bundle verify gh-pages-YYYYMMDD.bundle
git rev-parse origin/gh-pages origin/gh-pages^{tree}
git ls-tree -r --full-tree origin/gh-pages > gh-pages-YYYYMMDD.manifest
```

Store the backup bundle, tip/tree SHAs and manifest outside the repository.
Merge the approved workflow PR, manually run one deploy, then verify:

```bash
git fetch origin gh-pages
git rev-list --count origin/gh-pages
git show origin/gh-pages:CNAME
```

The commit count should be one. Verify the five live URLs above and inspect the
site before accepting the deployment.

## Rollback

If Pages content, feed URLs or the custom domain regress, restore from the
backup bundle. Substitute the recorded compacted tip for `<current-tip>`:

```bash
git fetch gh-pages-YYYYMMDD.bundle \
  refs/heads/backup/gh-pages-YYYYMMDD:refs/heads/restore-gh-pages
git push --force-with-lease=refs/heads/gh-pages:<current-tip> \
  origin refs/heads/restore-gh-pages:refs/heads/gh-pages
```

Then recheck the five URLs and `CNAME`. Do not delete the backup bundle until
the bounded-history deployment has completed a normal scheduled cycle.
