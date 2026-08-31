import json
from pathlib import Path

from scripts.generate_llm_phalalu import write_outputs


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
