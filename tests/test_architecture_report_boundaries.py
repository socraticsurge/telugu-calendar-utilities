"""Focused contracts for the architecture reporter's internal boundaries."""
from types import SimpleNamespace

import pytest

from tools.architecture_report import parsing, repository
from tools.architecture_report.contracts import symbol_pattern
from tools.architecture_report.history import parse_history
from tools.architecture_report.report import _scope_evidence


def test_python_imports_keep_walk_order_and_engine_attribute_evidence():
    imports, attributes = parsing._python_imports(
        'import alpha, beta\n'
        'from pkg.child import public, _hidden\n'
        'from . import ignored\n'
        'engine._one\n'
        'myEngine._two\n'
        'other._ignored\n'
        'engine.public\n'
        'holder.engine._nested\n'
    )
    assert imports == [('alpha', []), ('beta', []), ('pkg.child', ['public', '_hidden'])]
    assert attributes == [
        {'line': 4, 'expression': 'engine._one'},
        {'line': 5, 'expression': 'myEngine._two'},
    ]


def test_typescript_imports_retain_the_existing_line_oriented_contract():
    source = (
        'import thing from "./one";\n'
        'export { other } from "./two";\n'
        'import "./side-effect";\n'
        'const dynamic = import("./dynamic");\n'
        '// import ignored from "./comment";\n'
        'import {\n  multiline\n} from "./multiline";\n'
    )
    assert parsing._typescript_imports(source) == ['./one', './two', './side-effect']


@pytest.mark.parametrize(('source', 'imported', 'expected'), [
    ('src/file.ts', './peer', 'src/peer.ts'),
    ('src/file.ts', './folder', 'src/folder/index.ts'),
    ('src/file.ts', './data', 'src/data.json'),
    ('src/file.ts', 'package', None),
    ('file.ts', '../outside', None),
    ('src/nested/file.ts', '../peer', None),
])
def test_typescript_resolution_preserves_current_path_rules(source, imported, expected):
    paths = {'src/peer.ts', 'src/folder/index.ts', 'src/data.json'}
    assert parsing._resolve_ts_import(source, imported, paths) == expected


def test_python_resolution_uses_the_nearest_known_module():
    paths = {'pkg': 'pkg/__init__.py', 'pkg.child': 'pkg/child.py'}
    assert parsing._resolve_python_import('pkg.child.deep', paths) == 'pkg/child.py'
    assert parsing._resolve_python_import('pkg.other', paths) == 'pkg/__init__.py'
    assert parsing._resolve_python_import('external', paths) is None


def test_definition_metrics_include_nested_python_definitions():
    source = 'class A:\n    def method(self):\n        def nested():\n            pass\n'
    assert parsing._definition_metrics('example.py', source) == (3, 4)
    assert parsing._definition_metrics('empty.py', '') == (0, 0)
    assert parsing._definition_metrics('example.ts', 'export const x = 1;\n') == (1, 0)


def test_malformed_python_remains_an_error():
    with pytest.raises(SyntaxError):
        parsing._python_imports('def broken(')


def test_history_deduplicates_commit_touches_but_not_churn():
    output = '\n'.join([
        'COMMIT\tnew', '2\t1\tsrc/a.ts', '3\t0\tsrc/a.ts',
        '-\t-\tsrc/b.ts', 'bad', '1\t2\tignored.py',
        'COMMIT\told', '0\t4\tsrc/b.ts', '1\t0\tsrc/a.ts',
    ])
    rows, window = parse_history(output, {'src/a.ts', 'src/b.ts'})
    assert rows == [
        {'path': 'src/a.ts', 'commits': 2, 'added': 6, 'deleted': 1, 'churn': 7},
        {'path': 'src/b.ts', 'commits': 1, 'added': 0, 'deleted': 4, 'churn': 4},
    ]
    assert window == {'commit_count': 2, 'first_commit': 'old', 'last_commit': 'new'}


def test_history_empty_and_equal_rank_ordering():
    assert parse_history('', set()) == (
        [], {'commit_count': 0, 'first_commit': '', 'last_commit': ''},
    )
    rows, _ = parse_history('COMMIT\tx\n1\t0\tz.py\n1\t0\ta.py', {'a.py', 'z.py'})
    assert [item['path'] for item in rows] == ['a.py', 'z.py']


@pytest.mark.parametrize('args', [(), ('status',), ('show', 'a\0b'),
                                  ('log', 'a\nb'), ('ls-tree', 'a\rb')])
def test_repository_rejects_unsupported_commands_before_execution(tmp_path, monkeypatch, args):
    calls = []
    monkeypatch.setattr(repository.subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    with pytest.raises(ValueError):
        repository.GitRepository(tmp_path).git(*args)
    assert calls == []


def test_repository_pins_ref_without_shell_and_reads_that_revision(tmp_path, monkeypatch):
    calls = []
    commit = 'a' * 40

    def run(command, **options):
        calls.append((command, options))
        return SimpleNamespace(stdout=commit + '\n')

    monkeypatch.setattr(repository.subprocess, 'run', run)
    repo = repository.GitRepository(tmp_path)
    assert repo.resolve_ref('release/example') == commit
    snapshot = repository.SourceSnapshot(repo, commit)
    assert snapshot.read('src/file.ts') == commit + '\n'
    assert calls[0][0] == ['git', 'rev-parse', '--verify', '--end-of-options',
                          'release/example^{commit}']
    assert calls[1][0] == ['git', 'show', commit + ':src/file.ts']
    assert calls[0][1] == {'cwd': tmp_path, 'check': True, 'text': True, 'capture_output': True}


@pytest.mark.parametrize('ref', ['--help', 'a..b', 'HEAD^{tree}', '../HEAD',
                                 'branch.', 'branch/', 'a\nb', ''])
def test_repository_rejects_unsafe_refs_before_execution(tmp_path, monkeypatch, ref):
    calls = []
    monkeypatch.setattr(repository.subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    with pytest.raises(ValueError, match='unsupported Git ref'):
        repository.GitRepository(tmp_path).resolve_ref(ref)
    assert calls == []


def test_repository_rejects_a_non_commit_resolution(tmp_path, monkeypatch):
    monkeypatch.setattr(repository.subprocess, 'run',
                        lambda *a, **kw: SimpleNamespace(stdout='not-a-sha\n'))
    with pytest.raises(ValueError, match='did not resolve to a commit'):
        repository.GitRepository(tmp_path).resolve_ref('HEAD')


@pytest.mark.parametrize(('symbol', 'line'), [
    ('TABLE', 'export const TABLE = [];'), ('TABLE', 'TABLE: list = []'),
    ('name', 'def name():'), ('name', 'export function name() {}'),
    ('"rules"', '  "rules": {}'),
])
def test_contract_symbol_locators_keep_declaration_and_literal_rules(symbol, line):
    assert symbol_pattern(symbol).search(line)


def test_contract_symbol_locator_does_not_match_a_longer_name():
    assert symbol_pattern('TABLE').search('TABLE_EXTRA = []') is None


def test_scope_field_order_remains_compatible_for_imported_callers():
    scope = _scope_evidence(['src/example.ts'], [], {'computations': []}, {
        'commit_count': 1, 'first_commit': 'first', 'last_commit': 'last',
        'history_requested_non_merge_commits': 20,
    })
    assert list(scope) == [
        'source_files', 'established_source_files', 'additive_feature_source_files',
        'total_source_files', 'test_files', 'computation_records',
        'history_requested_non_merge_commits', 'commit_count', 'first_commit', 'last_commit',
    ]
