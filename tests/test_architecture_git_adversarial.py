"""Challenge all Git entrypoints and prove CLI rejection precedes Git execution."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.architecture_report.repository import GitRepository

COMMIT = 'a' * 40
COMMANDS = [
    ('rev-parse', '--verify', '--end-of-options', 'HEAD^{commit}'),
    ('show', f'{COMMIT}:src/sample.ts'),
    ('ls-tree', '-r', '--name-only', COMMIT),
    ('log', '--no-merges', '--max-count=1', '--format=COMMIT\t%H', '--numstat',
     COMMIT, '--', 'telugu_panchangam', 'scripts', 'src'),
]


@pytest.mark.parametrize('operation', [
    ('read_blob', ('src/sample.ts',)), ('list_paths', ()), ('read_history', (1,)),
])
@pytest.mark.parametrize('commit', ['HEAD', '--output=marker', 'A' * 40, None, 42])
def test_named_reads_reject_unpinned_commits_before_git(tmp_path, monkeypatch, operation, commit):
    method, args = operation
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    with pytest.raises(ValueError):
        getattr(GitRepository(tmp_path), method)(commit, *args)
    assert calls == []


@pytest.mark.parametrize('command', COMMANDS)
@pytest.mark.parametrize('option', ['--output=marker', '--ext-diff', '--textconv', '-c'])
def test_inserted_options_never_reach_git(tmp_path, monkeypatch, command, option):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    repo = GitRepository(tmp_path)
    for position in range(len(command) + 1):
        injected = (*command[:position], option, *command[position:])
        with pytest.raises(ValueError):
            repo.git(*injected)
    assert calls == []


@pytest.mark.parametrize('ref', ['--output=marker', 'HEAD;touch marker', 'HEAD$(touch marker)',
                               'HEAD`touch marker`', 'HEAD --help', 'HEAD\n--help',
                               'HEAD^{tree}', '%2d%2dhelp'])
def test_cli_rejects_hostile_refs_without_launching_git(tmp_path, ref):
    sentinel = tmp_path / 'git-was-started'
    git_stub = tmp_path / 'git'
    git_stub.write_text('#!/bin/sh\n: > "$GIT_TEST_SENTINEL"\nexit 97\n')
    git_stub.chmod(0o700)
    env = {**os.environ, 'PATH': str(tmp_path), 'GIT_TEST_SENTINEL': str(sentinel)}
    script = Path(__file__).resolve().parents[1] / 'tools/analyze_computation_architecture.py'
    result = subprocess.run([sys.executable, str(script), f'--ref={ref}', '--commits=1'],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert 'unsupported Git ref' in result.stderr
    assert result.stdout == ''
    assert not sentinel.exists()
    assert not (tmp_path / 'marker').exists()


def test_git_sentinel_detects_a_legitimate_cli_git_launch(tmp_path):
    sentinel = tmp_path / 'git-was-started'
    git_stub = tmp_path / 'git'
    git_stub.write_text('#!/bin/sh\n: > "$GIT_TEST_SENTINEL"\nexit 97\n')
    git_stub.chmod(0o700)
    env = {**os.environ, 'PATH': str(tmp_path), 'GIT_TEST_SENTINEL': str(sentinel)}
    script = Path(__file__).resolve().parents[1] / 'tools/analyze_computation_architecture.py'
    result = subprocess.run([sys.executable, str(script), '--ref=HEAD', '--commits=1'],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert sentinel.exists()
