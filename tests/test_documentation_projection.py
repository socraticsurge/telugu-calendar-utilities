"""The local documentation projection must preserve its publication boundary."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_combined_build_composes_docs_after_the_landing_site():
    package = json.loads(_read('package.json'))

    assert package['scripts']['build'] == (
        'npm run build:site && npm run build:docs && npm run docs:check-output'
    )
    assert package['scripts']['build:docs'].endswith(
        'vitepress build . && node tools/compose-docs-data.mjs'
    )
    assert package['scripts']['build:docs'].startswith(
        'node tools/generate-docs-computations.mjs'
    )
    assert package['devDependencies']['vitepress'] == '1.6.4'
    assert package['devDependencies']['mermaid'] == '11.17.2'
    assert package['overrides']['vitepress']['vite'] == '6.4.3'


def test_projection_uses_stable_same_site_paths_and_local_search():
    config = _read('.vitepress/config.ts')

    assert "base: '/docs/'" in config
    assert "outDir: './dist/docs'" in config
    assert "srcDir: './docs'" in config
    assert "provider: 'local'" in config
    assert "cleanUrls: true" in config
    assert "publicDir: './docs/public'" in config


def test_projection_excludes_archives_runtime_data_and_ignored_output():
    config = _read('.vitepress/config.ts')

    for excluded in (
        "'plans/**'",
        "'screenshots/**'",
        "'specs/**'",
        "'tracking/**'",
        "'feeds/**'",
        "'reference/README.md'",
        "'GUIDELINES.md'",
        "'NOW.md'",
    ):
        assert excluded in config

    assert "link: '/reference/README'" not in config


def test_every_computation_gets_a_registry_driven_searchable_route():
    generator = _read('tools/generate-docs-computations.mjs')
    config = _read('.vitepress/config.ts')

    assert "'docs', 'reference', 'computations.json'" in generator
    assert 'for (const record of registry.computations)' in generator
    assert "path.replace(/^_generated\\/computations\\//" in config
    assert 'engine_pinned' in generator
    assert 'Not independently verified' in generator


def test_generated_pages_show_real_methods_and_visible_method_gaps():
    subprocess.run(
        ['node', 'tools/generate-docs-computations.mjs'],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    abhijit = _read(
        'docs/_generated/computations/panchangam.abhijit-muhurta.md')
    assert '## Computation method' in abhijit
    assert 'D = T_set - T_rise' in abhijit
    assert 'end - start = D / 15' in abhijit
    assert 'Hyderabad, 2026-06-11, Drik Ganita' in abhijit
    assert '11:49:23–12:41:59 IST' in abhijit
    assert 'panchangam.abhijit_muhurta_method' in abhijit
    assert '[**Abhijit Muhurat**](https://www.drikpanchang.com/' in abhijit

    tithi = _read('docs/_generated/computations/panchangam.tithi.md')
    assert 'E = (M - S) mod 360' in tithi
    assert 'Krishna Ekadashi' in tithi

    festivals = _read(
        'docs/_generated/computations/panchangam.festivals.md')
    assert 'Evaluate maintained Telugu festival rules' in festivals
    assert 'Ugadi' in festivals

    vakya = _read(
        'docs/_generated/computations/astronomy.vakya-longitudes.md')
    assert 'M_vakya = (M_SS + correction[i]) mod 360' in vakya
    assert 'provisional nine-value project offset' in vakya

    panchaka = _read(
        'docs/_generated/computations/derived.panchaka-rahita.md')
    assert 'r = (T + V + N + L) mod 9' in panchaka
    assert 'Remainder: 7' in panchaka

    shuddhi = _read(
        'docs/_generated/computations/derived.panchanga-shuddhi.md')
    assert 'Grade each sunrise Panchangam limb' in shuddhi
    assert 'Verdict: Sarva Shuddha' in shuddhi

    incomplete = _read(
        'docs/_generated/computations/calendar.combustion-periods.md')
    assert 'Method documentation incomplete' in incomplete
    assert 'Incomplete — the contract is inventoried' in incomplete


def test_projection_adds_no_competing_pages_workflow_or_cname():
    workflow_names = {
        path.name for path in (ROOT / '.github' / 'workflows').glob('*.yml')
    }

    assert 'docs.yml' not in workflow_names
    assert 'deploy-docs.yml' not in workflow_names
    assert not (ROOT / 'docs' / 'public' / 'CNAME').exists()
