"""Contract tests for the generated browser Muhurtam activity catalogue."""
import json
from pathlib import Path
import subprocess
import sys

from telugu_panchangam.personal.activity_catalog import BROWSER_ACTIVITIES
from telugu_panchangam.personal.activity_rules import ACTIVITY_RULES


ROOT = Path(__file__).parents[1]
GENERATED = ROOT / 'src' / 'data' / 'activity-rules.generated.json'


def test_generated_activity_rules_are_current():
    result = subprocess.run(
        [sys.executable, 'tools/export_activity_rules.py', '--check'],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_browser_catalogue_is_ordered_unique_subset_of_backend():
    assert len(BROWSER_ACTIVITIES) == len(set(BROWSER_ACTIVITIES))
    assert set(BROWSER_ACTIVITIES) <= set(ACTIVITY_RULES)

    generated = json.loads(GENERATED.read_text(encoding='utf-8'))
    assert tuple(generated['rules']) == BROWSER_ACTIVITIES
    for key, rule in generated['rules'].items():
        assert rule['label'] == ACTIVITY_RULES[key]['label']

