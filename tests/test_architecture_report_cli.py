"""The legacy script path and module entrypoint retain their CLI contracts."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/analyze_computation_architecture.py'


@pytest.mark.parametrize('module', [False, True])
def test_cli_help_preserves_options(module, tmp_path):
    entry = ['-m', 'tools.analyze_computation_architecture'] if module else [str(SCRIPT)]
    result = subprocess.run([sys.executable, *entry, '--help'],
                            cwd=ROOT if module else tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert '--ref REF' in result.stdout
    assert '--commits COMMITS' in result.stdout
    assert '--summary' in result.stdout
    assert result.stderr == ''


@pytest.mark.parametrize(('args', 'code', 'message'), [
    (['--ref=--help'], 1, "ValueError: unsupported Git ref: '--help'"),
    (['--ref', 'HEAD..master'], 1, "ValueError: unsupported Git ref: 'HEAD..master'"),
    (['--commits', '0'], 1, 'ValueError: commit_limit must be between 1 and 10000'),
    (['--commits', '10001'], 1, 'ValueError: commit_limit must be between 1 and 10000'),
    (['--commits', 'abc'], 2, "invalid int value: 'abc'"),
])
def test_cli_errors_do_not_emit_a_partial_report(args, code, message, tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), *args],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == code
    assert result.stdout == ''
    assert message in result.stderr
