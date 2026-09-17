"""Read-only Git operations reject option injection at their execution boundary."""
import subprocess
from pathlib import Path

import pytest

from tools.architecture_report.repository import (
    GitRepository,
    SourceSnapshot,
    validate_command,
)

COMMIT = 'a' * 40


@pytest.fixture
def git_fixture(tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', '/dev/null')
    subprocess.run(['git', 'init', '--quiet', str(tmp_path)], check=True)
    source = tmp_path / 'src' / 'sample.ts'
    source.parent.mkdir()
    source.write_text('export const sample = 1;\n')
    subprocess.run(['git', 'add', 'src/sample.ts'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=Socraticsurge',
                    '-c', 'user.email=cvk.atreya@gmail.com',
                    'commit', '--quiet', '-m', 'fixture'], cwd=tmp_path, check=True)
    return GitRepository(tmp_path)


def test_raw_git_cannot_reproduce_the_file_write(git_fixture, tmp_path):
    marker = tmp_path / 'unexpected-output'
    with pytest.raises(ValueError):
        git_fixture.git('show', '--no-patch', '--format=%H', f'--output={marker}', 'HEAD')
    assert not marker.exists()


@pytest.mark.parametrize('args', [
    ('show', '--output=marker', COMMIT),
    ('show', COMMIT, '--output', 'marker'),
    ('show', COMMIT, '--ext-diff'),
    ('show', COMMIT, '--textconv'),
    ('show', COMMIT),
    ('show', '--output=marker'),
    ('log', '--output=marker', COMMIT),
    ('log', '--no-merges', '--max-count=1', '--format=COMMIT\t%H', '--numstat',
     COMMIT, '--', '--output=marker'),
    ('ls-tree', '-r', '--name-only', '--output=marker'),
    ('rev-parse', '--verify', '--end-of-options', '--output=marker^{commit}'),
    ('rev-parse', '--verify', '--end-of-options', 'HEAD^{tree}'),
    ('rev-parse', '--verify', '--end-of-options', 'HEAD^{commit}', '--help'),
])
def test_complete_command_shapes_reject_extra_or_reinterpreted_options(args):
    with pytest.raises(ValueError):
        validate_command(args)


@pytest.mark.parametrize('commit', ['HEAD', '--output=marker', 'a' * 39, 'a' * 41,
                                  'A' * 40, COMMIT + ':src/sample.ts', 'a\0b'])
def test_snapshot_constructor_rejects_unpinned_revisions(tmp_path, commit):
    repo = GitRepository(tmp_path)
    with pytest.raises(ValueError):
        SourceSnapshot(repo, commit)


@pytest.mark.parametrize('path', ['', '/absolute', '../outside', 'src/../outside',
                                './src/sample.ts', 'src//sample.ts', 'src/a\nb',
                                'src/a\0b', 'src\\sample.ts'])
def test_blob_path_rejections_happen_before_execution(tmp_path, monkeypatch, path):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    repo = GitRepository(tmp_path)
    with pytest.raises(ValueError):
        repo.read_blob(COMMIT, path)
    assert calls == []


@pytest.mark.parametrize('limit', [0, -1, 10001, '--output=marker', 1.5, True])
def test_history_limit_rejections_happen_before_execution(tmp_path, monkeypatch, limit):
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    repo = GitRepository(tmp_path)
    with pytest.raises(ValueError):
        repo.read_history(COMMIT, limit)
    assert calls == []


def test_fixed_operations_preserve_real_git_reads(git_fixture):
    commit = git_fixture.resolve_ref('HEAD')
    assert git_fixture.read_blob(commit, 'src/sample.ts') == 'export const sample = 1;\n'
    assert git_fixture.list_paths(commit) == ['src/sample.ts']
    history = git_fixture.read_history(commit, 1)
    assert f'COMMIT\t{commit}' in history
    assert '1\t0\tsrc/sample.ts' in history


def test_blob_option_text_is_only_a_filename(git_fixture, tmp_path):
    commit = git_fixture.resolve_ref('HEAD')
    marker = tmp_path / 'marker'
    with pytest.raises(subprocess.CalledProcessError):
        git_fixture.read_blob(commit, '--output=marker')
    assert not marker.exists()


def test_snapshot_stays_pinned_when_head_moves(git_fixture, tmp_path):
    commit = git_fixture.resolve_ref('HEAD')
    snapshot = SourceSnapshot(git_fixture, commit)
    source = tmp_path / 'src' / 'sample.ts'
    source.write_text('export const sample = 2;\n')
    subprocess.run(['git', '-c', 'user.name=Socraticsurge',
                    '-c', 'user.email=cvk.atreya@gmail.com',
                    'commit', '--quiet', '-am', 'move head'], cwd=tmp_path, check=True)
    assert git_fixture.resolve_ref('HEAD') != commit
    assert snapshot.read('src/sample.ts') == 'export const sample = 1;\n'


@pytest.mark.parametrize('ref', ['--output=marker', 'HEAD;touch marker',
                               'HEAD$(touch marker)', 'HEAD`touch marker`',
                               'HEAD --help', 'HEAD\n--help', 'HEAD^{tree}', '%2d%2dhelp'])
def test_cli_hostile_refs_cannot_start_git(tmp_path, ref):
    script = Path(__file__).resolve().parents[1] / 'tools/analyze_computation_architecture.py'
    result = subprocess.run(['python3', str(script), f'--ref={ref}', '--commits=1'],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert 'unsupported Git ref' in result.stderr
    assert result.stdout == ''
    assert not (tmp_path / 'marker').exists()
