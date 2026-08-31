import json
from pathlib import Path

from scripts.generate_llm_phalalu import write_outputs

REPO_ROOT = Path(__file__).resolve().parents[1]


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
