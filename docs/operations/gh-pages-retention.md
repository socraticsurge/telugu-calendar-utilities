# GitHub Pages retention and rollback

Status: the pre-activation backup and rollback were exercised on 2026-08-27.
The original action-based activation was rolled back after the live check found
that it removed layered artifacts. The corrected design compacts the complete
published tree in a dedicated workflow instead of orphaning partial deploys.

## Why history is bounded

`gh-pages` is a publication branch, not an audit archive. Its source inputs,
calculation rules and tests live on `master`; generated output can be reproduced.
The five content workflows remain layered deployments with `keep_files: true`
and no orphan option. A separate serialized compactor reads the current Pages
tip and tree through GitHub's Git data API, creates a parentless commit from the
exact same tree, rechecks that the branch did not move, and then updates only
`gh-pages`. This bounds history without asking a partial publisher to reconstruct
files owned by the other workflows.

## Measured baseline — 2026-08-27

The local repository reported a 96.58 MiB pack across all local refs. A clean,
aggressively packed rehearsal containing `master`, release tags and `gh-pages`
measured 77.96 MiB; the same repository without Pages history measured only
2.36 MiB.

`gh-pages` contained 148 deployment commits from 2026-06-10 through 2026-08-26.
Its live tip was `0c8242ed4818838cba60f2d8ef41493eb1e2cd1f`; the exact live tree
`af11e9b10c100e0ed8ea9036c203158727cca581` contained 317 files and
90,103,569 bytes:

| Live category | Files | Bytes | Required retention |
|---|---:|---:|---|
| Panchangam feeds under `feeds/` | 220 | 84,606,415 | Keep every currently published ICS feed and current per-city Lagna JSON. The feed horizon is the product contract. |
| Built assets | 22 | 3,496,777 | Keep the current production build only. |
| Rasi Phalalu | 68 | 1,790,357 | The UI reads today only. Retain a short operational window; deleting older live files is a separate approval-gated change. |
| Root JSON | 1 | 23,081 | Keep the current Gochara snapshot only. |
| Other (`index.html`, `CNAME`, etc.) | 6 | 186,939 | Keep the complete current site shell and custom-domain files. |

Across historical Pages commits, 1,434 unique blobs occupied 813,166,792
uncompressed bytes. Panchangam feed history accounted for 801,319,230 bytes,
so repeated generated feeds—not source history—were the dominant cause.

## Rehearsal result

A bare clone containing only `master`, tags and `gh-pages` was used; the live
repository was untouched.

1. A complete backup bundle of the original Pages tip
   `0c8242ed4818838cba60f2d8ef41493eb1e2cd1f` was created and verified.
2. A parentless commit was created from the exact live tree
   `af11e9b10c100e0ed8ea9036c203158727cca581`.
3. `git diff` confirmed that the old and new commits had identical trees;
   `CNAME` still contained `panchangam.astrochaganti.com`.
4. After unreachable objects were pruned and repacked, pack size fell from
   77.96 MiB to 15.38 MiB, an 80.3% reduction.
5. Rollback from the 76 MiB backup bundle restored the exact original tip and
   tree, and `git fsck --full --no-dangling` passed.

## Live activation finding and correction

The first approved deployment tested the pinned `peaceiris/actions-gh-pages`
v4.1.0 combination of `keep_files: true` and `force_orphan: true`. The workflow
completed successfully, but the resulting root commit contained only the
landing build: existing feeds, Gochara, Lagna and Rasi Phalalu files were absent.
The live check caught the loss immediately and the verified bundle restored the
exact original tip `0c8242ed4818838cba60f2d8ef41493eb1e2cd1f` and tree
`af11e9b10c100e0ed8ea9036c203158727cca581`.

The action's force-orphan path creates a new repository and copies only the
current `publish_dir`; it does not clone the publication branch first. The
corrected workflow therefore performs compaction independently, after all
layered content deployments, and refuses to update the ref if the live tip or
tree validation changes.

The first live deployment may not immediately reduce GitHub-reported storage;
unreachable server objects are reclaimed on GitHub's schedule. New clones stop
requesting the old Pages history once the ref becomes orphaned.

## Live artifact checks

Before the rehearsal, each canonical URL returned HTTP 200:

- site root: `https://panchangam.astrochaganti.com/`
- Panchangam feed: `/feeds/hyderabad-drik.ics`
- Gochara: `/gochara.json`
- Lagna: `/feeds/hyderabad-lagna.json`
- Rasi Phalalu sample: `/rasi_phalalu/2026-08-27.json`

After the first approved live deployment, repeat those checks, confirm the
`CNAME` file and compare the published tree manifest before removing any local
backup.

## Activation

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
Merge the approved workflow change, manually run **Compact GitHub Pages
History**, then verify:

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
