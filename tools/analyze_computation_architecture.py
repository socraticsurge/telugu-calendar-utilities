#!/usr/bin/env python3
"""Produce reproducible computation-layer coupling and change-risk evidence.

The report is intentionally descriptive. It does not assign architecture
scores or recommend refactors from line counts alone; the accompanying
decision record combines these measurements with correctness and runtime
evidence.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORY_COMMITS = 200
MAX_HISTORY_COMMITS = 10_000

_GIT_REF_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$')
_TS_FROM_IMPORT_RE = re.compile(
    r"(?:import|export)\s+[^'\"\n]*\bfrom\s+['\"]([^'\"\n]+)['\"]"
)
_TS_SIDE_EFFECT_IMPORT_RE = re.compile(
    r"import\s+['\"]([^'\"\n]+)['\"]"
)
_TS_DEFINITION_RE = re.compile(
    r'^\s*(?:export\s+)?(?:async\s+)?'
    r'(?:function|class|interface|type|const|let|var)\s+[A-Za-z_$][\w$]*\b',
    re.MULTILINE,
)

_ACTIVITY_RULES_ARTIFACT = 'src/data/activity-rules.generated.json'
_PANCHANGAM_NAMES = 'telugu_panchangam/panchangam_names.py'
_TARABALAM_PANEL = 'src/panels/tarabalam.ts'

# Schema v1 keeps ``scope.source_files`` as the total production-source count.
# Feature-side helpers are additions around the established computation layer:
# they still appear in the module graph, history, and blast-radius evidence,
# while the two subsets are also reported explicitly.
_ADDITIVE_FEATURE_SOURCES = frozenset({
    'src/lib/birth-profile-api.ts',
    'src/lib/election-chart-api.ts',
    'src/lib/guest-profile-store.ts',
    'src/lib/profile-selection.ts',
    'src/lib/remote-calculation-activation.ts',
    'src/panels/profiles.ts',
    'src/scorer/election-assessors/primitives.ts',
    'src/scorer/election-chart-enrichment.ts',
    'src/scorer/election-chart-screening.ts',
    'src/scorer/personal-election-screening.ts',
    'telugu_panchangam/personal/activity_check_contract.py',
    'telugu_panchangam/personal/election_assessors/__init__.py',
    'telugu_panchangam/personal/election_assessors/conventions.py',
    'telugu_panchangam/personal/election_assessors/facts.py',
    'telugu_panchangam/personal/election_assessors/primitives.py',
    'telugu_panchangam/personal/election_chart.py',
    'telugu_panchangam/personal/election_chart_rules.py',
    'telugu_panchangam/personal/personal_election.py',
})


def source_scope_class(path: str) -> str:
    """Classify a production module without hiding it from report evidence."""
    return 'additive-feature' if path in _ADDITIVE_FEATURE_SOURCES else 'established'
_DUPLICATE_CONTRACTS = {
    'activity_profiles': {
        'strategy': 'generated-from-python',
        'locations': [
            ('telugu_panchangam/personal/activity_rules.py', 'ACTIVITY_RULES'),
            (_ACTIVITY_RULES_ARTIFACT, '"rules"'),
            (_TARABALAM_PANEL, 'MU_ACTIVITY'),
        ],
    },
    'rashi_vocabulary': {
        'strategy': 'manual-mirror',
        'locations': [
            (_PANCHANGAM_NAMES, 'RASHI_NAMES'),
            ('src/data/rasis.ts', 'RASI_NAMES'),
            ('src/muhurta-scorer.ts', 'MU_RASHI_NAMES'),
            ('src/panels/today.ts', 'RASHI_NAMES_JS'),
        ],
    },
    'nakshatra_vocabulary': {
        'strategy': 'manual-mirror',
        'locations': [
            (_PANCHANGAM_NAMES, 'NAKSHATRA_NAMES'),
            ('src/data/rasis.ts', 'NAKSHATRA_NAMES'),
        ],
    },
    'nitya_yoga_vocabulary_and_disposition': {
        'strategy': 'manual-mirror',
        'locations': [
            (_PANCHANGAM_NAMES, 'YOGA_NAMES'),
            ('telugu_panchangam/personal/nitya_yoga.py', 'NITYA_AUSPICIOUS'),
            (_TARABALAM_PANEL, 'MU_YOGA_NAMES_27'),
            (_TARABALAM_PANEL, 'MU_NITYA_AUSPICIOUS'),
        ],
    },
    'special_yoga_tables': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/special_yogas.py', '_SARVARTHA_SIDDHI'),
            (_TARABALAM_PANEL, 'MU_SARVARTHA'),
        ],
    },
    'hora_tables': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/personal/lagna_hora.py', '_HORA_LORDS'),
            ('src/panels/today.ts', 'HORA_LORDS'),
        ],
    },
    'homa_election': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/personal/homa.py', 'HOMAHUTI_GROUP_LORDS'),
            (_TARABALAM_PANEL, 'MU_HOMAHUTI_LORDS'),
        ],
    },
    'named_shani_conditions': {
        'strategy': 'manual-mirror',
        'locations': [
            ('telugu_panchangam/gochara/rules.py', 'named_conditions'),
            ('src/shani-conditions.ts', 'shaniConditionFromMoonHouse'),
        ],
    },
}


def _git(*args: str) -> str:
    if not args or args[0] not in {'log', 'ls-tree', 'rev-parse', 'show'}:
        raise ValueError('unsupported Git command')
    if any('\0' in argument or '\n' in argument or '\r' in argument for argument in args):
        raise ValueError('Git arguments must not contain control characters')
    # Every caller supplies a fixed subcommand. The only CLI-derived value is
    # validated by _resolve_ref before it reaches later Git commands.
    result = subprocess.run(
        ['git', *args], cwd=ROOT, check=True, text=True,
        capture_output=True,
    )  # NOSONAR -- fixed executable, no shell, validated command/arguments
    return result.stdout


def _resolve_ref(ref: str) -> str:
    if not _GIT_REF_RE.fullmatch(ref) or '..' in ref or ref.endswith(('.', '/')):
        raise ValueError(f'unsupported Git ref: {ref!r}')
    commit = _git(
        'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}',
    ).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError(f'Git ref did not resolve to a commit: {ref!r}')
    return commit


def _tree_paths(ref: str) -> list[str]:
    return sorted(_git('ls-tree', '-r', '--name-only', ref).splitlines())


def _read_at(ref: str, path: str) -> str:
    return _git('show', f'{ref}:{path}')


def _is_source(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if '__tests__' in parts or path.endswith('.d.ts'):
        return False
    return (
        path.startswith('telugu_panchangam/') and path.endswith('.py')
        or path.startswith('scripts/') and path.endswith('.py')
        or path.startswith('src/') and path.endswith('.ts')
    )


def _is_test(path: str) -> bool:
    return (
        path.startswith('tests/') and path.endswith('.py')
        or '__tests__' in PurePosixPath(path).parts and path.endswith('.ts')
    )


def _layer(path: str) -> str:
    if path.startswith('telugu_panchangam/models/'):
        return 'models'
    if path.startswith('telugu_panchangam/engines/'):
        return 'engines'
    if path.startswith('telugu_panchangam/personal/activity_'):
        return 'activity-rules'
    if path in {
        'telugu_panchangam/personal/muhurta.py',
        'telugu_panchangam/personal/slot_scorers.py',
    }:
        return 'scoring'
    if path.startswith('telugu_panchangam/personal/'):
        return 'personal'
    if path.startswith('telugu_panchangam/gochara/'):
        return 'gochara'
    if path.startswith('telugu_panchangam/mcp/'):
        return 'mcp'
    if path.startswith('telugu_panchangam/generators/'):
        return 'generators'
    if path == 'telugu_panchangam/generate.py' or path.startswith('scripts/'):
        return 'build'
    if path.startswith('telugu_panchangam/'):
        return 'derived-calendar'
    if path.startswith('src/data/'):
        return 'browser-data'
    if path.startswith('src/panels/'):
        return 'browser-panels'
    if path.startswith('src/'):
        return 'browser-core'
    return 'other'


def _module_name(path: str) -> str | None:
    if not path.endswith('.py'):
        return None
    module = path[:-3].replace('/', '.')
    return module.removesuffix('.__init__')


def _definition_metrics(path: str, content: str) -> tuple[int, int]:
    if path.endswith('.ts'):
        return len(_TS_DEFINITION_RE.findall(content)), 0
    tree = ast.parse(content, filename=path)
    definitions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    largest = max(
        (getattr(node, 'end_lineno', node.lineno) - node.lineno + 1
         for node in definitions),
        default=0,
    )
    return len(definitions), largest


def _python_imports(content: str) -> tuple[list[tuple[str, list[str]]], list[dict]]:
    tree = ast.parse(content)
    imports: list[tuple[str, list[str]]] = []
    private_attributes: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, []) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, [alias.name for alias in node.names]))
        elif (
            isinstance(node, ast.Attribute)
            and node.attr.startswith('_')
            and isinstance(node.value, ast.Name)
            and 'engine' in node.value.id.lower()
        ):
            private_attributes.append({
                'line': node.lineno,
                'expression': f'{node.value.id}.{node.attr}',
            })
    return imports, private_attributes


def _typescript_imports(content: str) -> list[str]:
    """Return static TypeScript imports without ambiguous regex backtracking."""
    return [
        *_TS_FROM_IMPORT_RE.findall(content),
        *_TS_SIDE_EFFECT_IMPORT_RE.findall(content),
    ]


def _resolve_python_import(
    imported: str, module_to_path: dict[str, str]
) -> str | None:
    candidate = imported
    while candidate:
        if candidate in module_to_path:
            return module_to_path[candidate]
        candidate = candidate.rpartition('.')[0]
    return None


def _resolve_ts_import(source: str, imported: str, paths: set[str]) -> str | None:
    if not imported.startswith('.'):
        return None
    candidate = PurePosixPath(source).parent.joinpath(imported)
    normalized = str(PurePosixPath(candidate))
    if normalized.startswith('../'):
        return None
    for suffix in ('.ts', '/index.ts', '.json'):
        target = f'{normalized}{suffix}'
        if target in paths:
            return target
    return None


def _registry_at(ref: str) -> dict[str, Any]:
    return json.loads(_read_at(ref, 'docs/reference/computations.json'))


def _module_graph(
    ref: str, source_paths: list[str], all_paths: set[str]
) -> tuple[dict[str, list[str]], list[dict], list[dict]]:
    module_to_path = {
        module: path for path in source_paths
        if (module := _module_name(path)) is not None
    }
    graph: dict[str, list[str]] = {}
    private_imports: list[dict] = []
    private_attributes: list[dict] = []
    for path in source_paths:
        content = _read_at(ref, path)
        targets: set[str] = set()
        if path.endswith('.py'):
            imports, attributes = _python_imports(content)
            for imported, names in imports:
                target = _resolve_python_import(imported, module_to_path)
                if target and target != path:
                    targets.add(target)
                    for name in names:
                        if name.startswith('_'):
                            private_imports.append({
                                'importer': path,
                                'owner': target,
                                'symbol': name,
                            })
            for item in attributes:
                private_attributes.append({'path': path, **item})
        else:
            for imported in _typescript_imports(content):
                target = _resolve_ts_import(path, imported, all_paths)
                if target and target != path:
                    targets.add(target)
        graph[path] = sorted(targets)
    return graph, private_imports, private_attributes


def _test_links(
    ref: str,
    test_paths: list[str],
    source_paths: list[str],
    all_paths: set[str],
    registry: dict[str, Any],
) -> dict[str, set[str]]:
    links: dict[str, set[str]] = defaultdict(set)
    module_to_path = {
        module: path for path in source_paths
        if (module := _module_name(path)) is not None
    }
    for path in test_paths:
        content = _read_at(ref, path)
        if path.endswith('.py'):
            imports, _ = _python_imports(content)
            for imported, _names in imports:
                target = _resolve_python_import(imported, module_to_path)
                if target:
                    links[target].add(path)
        else:
            for imported in _typescript_imports(content):
                target = _resolve_ts_import(path, imported, all_paths)
                if target:
                    links[target].add(path)
    for record in registry['computations']:
        for implementation in record['implementations']:
            links[implementation['path']].update(record['tests'])
    return links


def _history(
    ref: str, source_paths: set[str], commit_limit: int
) -> tuple[list[dict], dict[str, dict[str, int]]]:
    output = _git(
        'log', '--no-merges', f'--max-count={commit_limit}',
        '--format=COMMIT\t%H', '--numstat', ref, '--',
        'telugu_panchangam', 'scripts', 'src',
    )
    per_file: dict[str, dict[str, int]] = defaultdict(
        lambda: {'commits': 0, 'added': 0, 'deleted': 0, 'churn': 0}
    )
    current_commit = ''
    touched_in_commit: set[str] = set()
    commits: list[str] = []
    for line in output.splitlines():
        if line.startswith('COMMIT\t'):
            current_commit = line.split('\t', 1)[1]
            commits.append(current_commit)
            touched_in_commit = set()
            continue
        parts = line.split('\t')
        if len(parts) != 3 or parts[2] not in source_paths:
            continue
        added, deleted, path = parts
        if not added.isdigit() or not deleted.isdigit():
            continue
        metrics = per_file[path]
        if path not in touched_in_commit:
            metrics['commits'] += 1
            touched_in_commit.add(path)
        metrics['added'] += int(added)
        metrics['deleted'] += int(deleted)
        metrics['churn'] += int(added) + int(deleted)
    top = [
        {'path': path, **metrics}
        for path, metrics in sorted(
            per_file.items(),
            key=lambda item: (
                -item[1]['commits'], -item[1]['churn'], item[0]
            ),
        )
    ]
    return top, {
        'commit_count': len(commits),
        'first_commit': commits[-1] if commits else '',
        'last_commit': commits[0] if commits else '',
    }


def _engine_asymmetry(ref: str) -> dict[str, Any]:
    classes = {
        'PanchangamEngine': 'telugu_panchangam/engines/base.py',
        'DrikGanitaEngine': 'telugu_panchangam/engines/drik.py',
        'SuryaSiddhantaEngine': 'telugu_panchangam/engines/surya_siddhanta.py',
        'VakyaEngine': 'telugu_panchangam/engines/vakya.py',
    }
    result: dict[str, Any] = {}
    for class_name, path in classes.items():
        tree = ast.parse(_read_at(ref, path), filename=path)
        node = next(
            item for item in tree.body
            if isinstance(item, ast.ClassDef) and item.name == class_name
        )
        result[class_name] = {
            'path': path,
            'bases': [ast.unparse(base) for base in node.bases],
            'defined_methods': sorted(
                item.name for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ),
        }
    concrete = [
        set(result[name]['defined_methods'])
        for name in ('DrikGanitaEngine', 'SuryaSiddhantaEngine', 'VakyaEngine')
    ]
    result['shared_method_names'] = {
        'all_three': sorted(set.intersection(*concrete)),
        'drik_and_surya_siddhanta': sorted(concrete[0] & concrete[1]),
        'surya_siddhanta_and_vakya': sorted(concrete[1] & concrete[2]),
    }
    return result


def _duplicate_contracts(ref: str) -> list[dict]:
    groups = []
    for name, config in _DUPLICATE_CONTRACTS.items():
        locations = []
        for path, symbol in config['locations']:
            content = _read_at(ref, path)
            symbol_pattern = re.compile(
                rf'^\s*(?:(?:export\s+)?(?:def|function|class)\s+'
                rf'{re.escape(symbol)}\b|(?:export\s+)?'
                rf'(?:(?:const|let|var)\s+)?{re.escape(symbol)}\b\s*[:=])'
                if symbol.isidentifier()
                else re.escape(symbol)
            )
            line = next(
                (index for index, text in enumerate(content.splitlines(), 1)
                 if symbol_pattern.search(text)),
                None,
            )
            locations.append({'path': path, 'symbol': symbol, 'line': line})
        groups.append({
            'name': name,
            'strategy': config['strategy'],
            'locations': locations,
        })
    return groups


def build_report(ref: str = 'HEAD', commit_limit: int = DEFAULT_HISTORY_COMMITS) -> dict:
    """Build a deterministic architecture report for one Git tree and history."""
    if not 1 <= commit_limit <= MAX_HISTORY_COMMITS:
        raise ValueError(
            f'commit_limit must be between 1 and {MAX_HISTORY_COMMITS}'
        )
    commit = _resolve_ref(ref)
    tree_paths = _tree_paths(commit)
    all_paths = set(tree_paths)
    source_paths = [path for path in tree_paths if _is_source(path)]
    additive_feature_paths = [
        path for path in source_paths if source_scope_class(path) == 'additive-feature'
    ]
    established_source_paths = [
        path for path in source_paths if source_scope_class(path) == 'established'
    ]
    test_paths = [path for path in tree_paths if _is_test(path)]
    registry = _registry_at(commit)
    graph, private_imports, private_attributes = _module_graph(
        commit, source_paths, all_paths,
    )
    test_links = _test_links(
        commit, test_paths, source_paths, all_paths, registry,
    )

    linked_computations: dict[str, set[str]] = defaultdict(set)
    consumer_map = []
    for record in registry['computations']:
        owners = []
        mirrors = []
        for implementation in record['implementations']:
            linked_computations[implementation['path']].add(record['id'])
            destination = owners if implementation['role'] == 'owner' else mirrors
            destination.append(implementation['path'])
        consumer_map.append({
            'id': record['id'],
            'owners': sorted(set(owners)),
            'mirrors': sorted(set(mirrors)),
            'surfaces': record['surfaces'],
            'tests': record['tests'],
        })

    incoming: dict[str, set[str]] = defaultdict(set)
    cross_layer = Counter()
    cross_layer_details = []
    for source, targets in graph.items():
        for target in targets:
            incoming[target].add(source)
            edge = (_layer(source), _layer(target))
            if edge[0] != edge[1]:
                cross_layer[edge] += 1
                cross_layer_details.append({
                    'from': source,
                    'from_layer': edge[0],
                    'to': target,
                    'to_layer': edge[1],
                })

    modules = []
    layer_metrics: dict[str, dict[str, int]] = defaultdict(
        lambda: {'files': 0, 'nonblank_lines': 0, 'definitions': 0}
    )
    for path in source_paths:
        content = _read_at(commit, path)
        nonblank = sum(bool(line.strip()) for line in content.splitlines())
        definitions, largest = _definition_metrics(path, content)
        layer = _layer(path)
        layer_metrics[layer]['files'] += 1
        layer_metrics[layer]['nonblank_lines'] += nonblank
        layer_metrics[layer]['definitions'] += definitions
        modules.append({
            'path': path,
            'layer': layer,
            'scope_class': source_scope_class(path),
            'nonblank_lines': nonblank,
            'definitions': definitions,
            'largest_definition_lines': largest,
            'imports_out': graph[path],
            'importers_in': sorted(incoming[path]),
            'computation_ids': sorted(linked_computations[path]),
            'linked_tests': sorted(test_links[path]),
        })

    history, history_window = _history(
        commit, set(source_paths), commit_limit,
    )
    history_by_path = {item['path']: item for item in history}
    for module in modules:
        module['history'] = history_by_path.get(
            module['path'],
            {'commits': 0, 'added': 0, 'deleted': 0, 'churn': 0},
        )

    concrete_engine_imports = []
    for detail in cross_layer_details:
        if (
            detail['to_layer'] == 'engines'
            and detail['from_layer'] != 'engines'
            and detail['to'] not in {
                'telugu_panchangam/engines/__init__.py',
                'telugu_panchangam/engines/utils.py',
            }
        ):
            concrete_engine_imports.append(detail)

    generated_contract = json.loads(
        _read_at(commit, _ACTIVITY_RULES_ARTIFACT)
    )
    unique_private_imports = {
        (item['importer'], item['owner'], item['symbol'])
        for item in private_imports
    }
    top_blast_radius = sorted(
        (
            {
                'path': module['path'],
                'linked_test_count': len(module['linked_tests']),
                'linked_computation_count': len(module['computation_ids']),
            }
            for module in modules
        ),
        key=lambda item: (
            -item['linked_test_count'], -item['linked_computation_count'],
            item['path'],
        ),
    )

    return {
        'schema_version': 1,
        'source_commit': commit,
        'scope': {
            'source_files': len(source_paths),
            'established_source_files': len(established_source_paths),
            'additive_feature_source_files': len(additive_feature_paths),
            'total_source_files': len(source_paths),
            'test_files': len(test_paths),
            'computation_records': len(registry['computations']),
            'history_requested_non_merge_commits': commit_limit,
            **history_window,
        },
        'layers': dict(sorted(layer_metrics.items())),
        'modules': modules,
        'cross_layer_edge_counts': [
            {'from': source, 'to': target, 'count': count}
            for (source, target), count in sorted(cross_layer.items())
        ],
        'cross_layer_edges': sorted(
            cross_layer_details,
            key=lambda item: (item['from'], item['to']),
        ),
        'output_consumer_map': consumer_map,
        'api_boundary': {
            'private_symbol_imports': [
                {'importer': importer, 'owner': owner, 'symbol': symbol}
                for importer, owner, symbol in sorted(unique_private_imports)
            ],
            'engine_private_attribute_access': sorted(
                private_attributes,
                key=lambda item: (item['path'], item['line']),
            ),
            'concrete_engine_module_imports': sorted(
                concrete_engine_imports,
                key=lambda item: (item['from'], item['to']),
            ),
        },
        'engine_asymmetry': _engine_asymmetry(commit),
        'duplicate_contracts': _duplicate_contracts(commit),
        'generated_contracts': [{
            'source': 'telugu_panchangam/personal/activity_rules.py',
            'generator': 'tools/export_activity_rules.py',
            'artifact': _ACTIVITY_RULES_ARTIFACT,
            'exported_rule_count': len(generated_contract['rules']),
        }],
        'history_top_changed_files': history[:25],
        'test_blast_radius': top_blast_radius[:25],
    }


def _summary(report: dict) -> str:
    modules = sorted(
        report['modules'],
        key=lambda item: (-item['nonblank_lines'], item['path']),
    )
    manual = sum(
        item['strategy'] == 'manual-mirror'
        for item in report['duplicate_contracts']
    )
    lines = [
        f"Source commit: {report['source_commit']}",
        f"Production modules: {report['scope']['source_files']}",
        (
            'Established production modules: '
            f"{report['scope']['established_source_files']}"
        ),
        (
            'Additive feature modules: '
            f"{report['scope']['additive_feature_source_files']}"
        ),
        f"Computation records: {report['scope']['computation_records']}",
        f'Manual duplicate-contract groups: {manual}',
        'Largest modules by nonblank lines:',
    ]
    lines.extend(
        f"  {item['nonblank_lines']:4d}  {item['path']}"
        for item in modules[:10]
    )
    lines.append('Most frequently changed files in the measured history:')
    lines.extend(
        f"  {item['commits']:3d} commits / {item['churn']:5d} churn  {item['path']}"
        for item in report['history_top_changed_files'][:10]
    )
    lines.append('Highest direct test blast radius:')
    lines.extend(
        f"  {item['linked_test_count']:3d} tests / "
        f"{item['linked_computation_count']:2d} computations  {item['path']}"
        for item in report['test_blast_radius'][:10]
    )
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--commits', type=int, default=DEFAULT_HISTORY_COMMITS)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = build_report(args.ref, args.commits)
    if args.summary:
        print(_summary(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
