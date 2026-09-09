import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.generate_llm_phalalu import write_outputs

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'rasi_phalalu.yml'


def test_workflow_runs_generator_as_repository_module():
    workflow = WORKFLOW.read_text(encoding='utf-8')

    assert (
        'uv run --no-sync --no-build python -m scripts.generate_llm_phalalu'
        in workflow
    )
    assert 'python scripts/generate_llm_phalalu.py' not in workflow


def test_module_entrypoint_resolves_repository_package():
    env = os.environ.copy()
    env.pop('rasiphalalu', None)

    result = subprocess.run(
        [sys.executable, '-m', 'scripts.generate_llm_phalalu'],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert result.stderr == 'Error: rasiphalalu environment variable not set.\n'


def test_runtime_latest_artifact_is_not_owned_by_the_source_checkout():
    runtime_latest = REPO_ROOT / 'public' / 'rasi_phalalu' / 'latest.json'

    assert not runtime_latest.exists()
    assert 'public/' in (REPO_ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()


def test_generator_writes_dated_and_stable_browser_artifacts(tmp_path):
    payload = {
        'date': '2026-08-29',
        'rashis': {'Mesha': {'text': 'Example interpretation'}},
    }

    paths = write_outputs(payload, payload['date'], tmp_path)

    assert [Path(path).name for path in paths] == [
        '2026-08-29.json',
        'latest.json',
    ]
    assert json.loads((tmp_path / '2026-08-29.json').read_text()) == payload
    assert json.loads((tmp_path / 'latest.json').read_text()) == payload
