"""Guards against the v1.8.0 hotfix regression class, updated for Vite.

The deployed static site is served from gh-pages by two paths:

  1. `.github/workflows/deploy-landing.yml` — runs `npm run build`
     (Vite), then publishes dist/ to gh-pages.
  2. `scripts/build_landing_page.py` — invoked by the monthly
     `generate.yml` regeneration; copies the same docs files
     alongside the freshly built ICS feeds.

Pre-Vite: if `docs/index.html` referenced a sidecar via `<script src=…>`
but the deploy path forgot to copy it, the page would 404 on the sidecar.
Post-Vite: Vite bundles everything from src/ — no manually-staged sidecars.
The new regression class is: the workflow forgets to run `npm run build`,
or SEO assets are missing from public/ (Vite's static asset dir).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / 'index.html'
DEPLOY_WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'deploy-landing.yml'
BUILD_SCRIPT = REPO_ROOT / 'scripts' / 'build_landing_page.py'

# Every workflow that publishes to gh-pages MUST pin this CNAME — the
# custom domain panchangam.astrochaganti.com is load-bearing for
# subscribers (their webcal:// URLs point at it) and for SEO continuity
# from the old github.io URL. CLAUDE.md spells this out explicitly.
# If any of these workflows drops the cname line, the next deploy
# wipes the CNAME file from gh-pages and the domain stops resolving.
CNAME_VALUE = 'panchangam.astrochaganti.com'
CNAME_PINNED_WORKFLOWS = [
    '.github/workflows/deploy-landing.yml',
    '.github/workflows/generate.yml',
    '.github/workflows/gochara.yml',
    '.github/workflows/lagna.yml',
]

# Search-engine static assets. Pre-Vite these lived in docs/; now
# they live in public/ (Vite's static asset dir, copied verbatim to dist/).
# Dropping either from public/ means the Vite build won't include them,
# silently de-indexing the site over time.
SEO_STATIC_ASSETS = ['sitemap.xml', 'robots.txt']
SEO_ASSETS_DIR = REPO_ROOT / 'public'

# Matches <script type="module" src="…"> — the Vite entry point.
MODULE_ENTRY_RE = re.compile(
    r"""<script\s+[^>]*type=["']module["'][^>]*\bsrc=["']([^"']+)["']""",
    re.IGNORECASE,
)


def test_index_html_has_module_entry_point():
    """Root index.html must have a <script type="module" src="...">
    entry point. If this fails, Vite has nothing to bundle."""
    html = INDEX_HTML.read_text(encoding='utf-8')
    entries = MODULE_ENTRY_RE.findall(html)
    assert entries, (
        'No <script type="module" src="..."> found in index.html. '
        'Vite requires a module entry point to build the site.'
    )


def test_deploy_workflow_runs_vite_build():
    """deploy-landing.yml must run `npm run build` so the Vite
    bundle is produced before deploying. Without it, dist/ is
    missing or stale and the deployed site breaks."""
    yml = DEPLOY_WORKFLOW.read_text(encoding='utf-8')
    assert 'npm run build' in yml, (
        '.github/workflows/deploy-landing.yml does not contain '
        '"npm run build". The Vite bundle will not be produced '
        'before deploy — add the build step.'
    )


def test_deploy_workflow_deploys_dist():
    """deploy-landing.yml must deploy from dist/ (Vite output),
    not from public/ or docs/."""
    yml = DEPLOY_WORKFLOW.read_text(encoding='utf-8')
    assert 'publish_dir: ./dist' in yml, (
        '.github/workflows/deploy-landing.yml does not deploy from '
        './dist. After switching to Vite, dist/ is the built output.'
    )


@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_exists_in_repo(asset: str):
    """public/sitemap.xml and public/robots.txt must exist on disk.
    Vite copies public/ verbatim to dist/; dropping either means
    they won't appear in the built output and the site de-indexes."""
    path = SEO_ASSETS_DIR / asset
    assert path.is_file(), (
        f'public/{asset} is missing. Vite copies public/ to dist/ '
        f'verbatim — without it the SEO asset won\'t be deployed. '
        f'Restore it before any other deploy fires.'
    )


@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_staged_in_deploy_landing_workflow(asset: str):
    """deploy-landing.yml must include the SEO asset in the push
    `paths:` filter so saves redeploy automatically."""
    yml = DEPLOY_WORKFLOW.read_text(encoding='utf-8')
    assert f"public/{asset}" in yml, (
        f'.github/workflows/deploy-landing.yml does not mention '
        f'public/{asset}. Saves to that file will not trigger a '
        f'redeploy. Add it to the paths filter.'
    )


@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_staged_in_build_landing_page_script(asset: str):
    """build_landing_page.py runs `npm run build` which calls Vite.
    Vite copies public/ verbatim to dist/, so SEO assets in public/
    reach dist/ automatically — no explicit copy needed here."""
    src = BUILD_SCRIPT.read_text(encoding='utf-8')
    assert 'npm run build' in src, (
        f'scripts/build_landing_page.py does not run "npm run build". '
        f'Without the Vite build, {asset} will not reach dist/ and '
        f'the monthly generate.yml run will wipe it from gh-pages.'
    )


@pytest.mark.parametrize('workflow_path', CNAME_PINNED_WORKFLOWS)
def test_deploy_workflow_pins_cname(workflow_path: str):
    """Every workflow that publishes to gh-pages must include the
    `cname: panchangam.astrochaganti.com` line. Dropping it would
    erase the CNAME file from gh-pages on the next deploy and the
    custom domain stops resolving — subscribers' webcal:// URLs
    break silently. CLAUDE.md forbids removing this line; this
    test makes the rule machine-enforceable.

    The substring check is intentionally literal: no YAML parsing,
    no aliases, no quoting variants. The string must appear exactly
    as it does in every existing deploy workflow today.
    """
    yml = (REPO_ROOT / workflow_path).read_text(encoding='utf-8')
    needle = f'cname: {CNAME_VALUE}'
    assert needle in yml, (
        f'{workflow_path} does not contain {needle!r}. If you '
        f'intentionally removed the cname pin you also need to '
        f'plan a CNAME-file replacement on gh-pages, otherwise '
        f'{CNAME_VALUE} stops serving the site after the next '
        f'deploy. See CLAUDE.md.'
    )
