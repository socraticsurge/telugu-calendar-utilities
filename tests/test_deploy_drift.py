"""Guards against the v1.8.0 hotfix regression class.

The deployed static site is served from gh-pages by two paths:

  1. `.github/workflows/deploy-landing.yml` — copies docs files into
     public/ on every push that touches them, then publishes.
  2. `scripts/build_landing_page.py` — invoked by the monthly
     `generate.yml` regeneration; copies the same docs files
     alongside the freshly built ICS feeds.

If `docs/index.html` references a sidecar via `<script src=…>` but
either deploy path forgets to copy it, the deployed page 404s on
the sidecar and every helper call from the inline script throws
ReferenceError. That's exactly what happened with
`muhurta-scorer.js` between PR 65 (added) and the v1.8.0 hotfix
(staged). These tests fail loudly when a new sidecar is missed in
either deploy path.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / 'docs' / 'index.html'
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

# Search-engine static assets at docs/ root. Unlike .js sidecars,
# these are never referenced from <script src=...> in index.html —
# search engines pick them up by convention (robots.txt at /, then
# sitemap.xml as declared in robots.txt). Dropping either from the
# deploy steps silently de-indexes the site over time.
SEO_STATIC_ASSETS = ['sitemap.xml', 'robots.txt']

# Matches <script src="…"> / <script src='…'> with a relative path
# (no http://, no leading slash — those are external resources, not
# files we need to stage).
SCRIPT_SRC_RE = re.compile(
    r"""<script\s+[^>]*\bsrc=["']([^"'/][^"']*?\.js)["']""",
    re.IGNORECASE,
)


def _sidecars_in_index() -> list[str]:
    """List relative .js paths referenced by docs/index.html."""
    html = INDEX_HTML.read_text(encoding='utf-8')
    return sorted(set(SCRIPT_SRC_RE.findall(html)))


def test_index_html_has_at_least_one_sidecar():
    """If this fails the regex has stopped matching — fix the regex
    before relaxing this assertion."""
    sidecars = _sidecars_in_index()
    assert sidecars, (
        'No relative <script src="*.js"> references found in '
        'docs/index.html. The drift guard regex may have broken.'
    )


@pytest.mark.parametrize('sidecar', _sidecars_in_index())
def test_sidecar_file_exists_in_repo(sidecar: str):
    """The referenced file must exist next to docs/index.html. If
    you renamed it, update both the <script src=…> and your deploy
    paths together."""
    path = (REPO_ROOT / 'docs' / sidecar)
    assert path.is_file(), (
        f'docs/index.html references {sidecar!r} but '
        f'{path} does not exist.'
    )


@pytest.mark.parametrize('sidecar', _sidecars_in_index())
def test_sidecar_listed_in_deploy_landing_workflow(sidecar: str):
    """deploy-landing.yml must (a) include the sidecar in its push
    `paths:` filter so saves redeploy automatically, and (b) include
    it in the staging cp so it actually lands on gh-pages."""
    yml = DEPLOY_WORKFLOW.read_text(encoding='utf-8')
    # path trigger — present anywhere in the file is enough; the
    # nuance of which trigger block doesn't matter for this guard.
    assert f"docs/{sidecar}" in yml, (
        f'.github/workflows/deploy-landing.yml does not mention '
        f'"docs/{sidecar}". Saves to that file will not redeploy '
        f'the site. Add it to the paths filter AND the cp step.'
    )


@pytest.mark.parametrize('sidecar', _sidecars_in_index())
def test_sidecar_listed_in_build_landing_page_script(sidecar: str):
    """build_landing_page.py is invoked by the monthly generate.yml
    regeneration. If it doesn't shutil.copy the sidecar, the next
    monthly cron will silently 404 it back."""
    src = BUILD_SCRIPT.read_text(encoding='utf-8')
    assert f"docs/{sidecar}" in src, (
        f'scripts/build_landing_page.py does not copy '
        f'docs/{sidecar}. The next monthly generate.yml run will '
        f'remove it from gh-pages.'
    )


@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_exists_in_repo(asset: str):
    """docs/sitemap.xml and docs/robots.txt must exist on disk.
    They're the search-engine surface; dropping either de-indexes
    the site over time."""
    path = REPO_ROOT / 'docs' / asset
    assert path.is_file(), (
        f'docs/{asset} is missing. The SEO surface depends on it; '
        f'restore it before any other deploy fires.'
    )


@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_staged_in_deploy_landing_workflow(asset: str):
    """deploy-landing.yml must include the SEO asset in both the
    push `paths:` filter and the staging cp."""
    yml = DEPLOY_WORKFLOW.read_text(encoding='utf-8')
    assert f"docs/{asset}" in yml, (
        f'.github/workflows/deploy-landing.yml does not mention '
        f'docs/{asset}. Saves to that file will not redeploy the '
        f'SEO surface. Add it to the paths filter AND the cp step.'
    )


@pytest.mark.parametrize('asset', SEO_STATIC_ASSETS)
def test_seo_asset_staged_in_build_landing_page_script(asset: str):
    """build_landing_page.py (invoked monthly by generate.yml) must
    copy the SEO asset alongside the other landing assets — else
    the monthly cron wipes it from gh-pages."""
    src = BUILD_SCRIPT.read_text(encoding='utf-8')
    assert f"docs/{asset}" in src, (
        f'scripts/build_landing_page.py does not copy '
        f'docs/{asset}. The next monthly generate.yml run will '
        f'wipe it from gh-pages.'
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
