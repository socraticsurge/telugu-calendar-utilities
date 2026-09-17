"""Dependency and test-link evidence from a pinned source snapshot."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .parsing import (
    _module_name,
    _python_imports,
    _resolve_python_import,
    _resolve_ts_import,
    _typescript_imports,
)
from .repository import SourceSnapshot


def _python_graph_details(
    path: str,
    content: str,
    module_to_path: dict[str, str],
) -> tuple[set[str], list[dict], list[dict]]:
    targets: set[str] = set()
    private_imports: list[dict] = []
    imports, private_attributes = _python_imports(content)
    for imported, names in imports:
        target = _resolve_python_import(imported, module_to_path)
        if not target or target == path:
            continue
        targets.add(target)
        private_imports.extend(
            {'importer': path, 'owner': target, 'symbol': name}
            for name in names
            if name.startswith('_')
        )
    return targets, private_imports, [
        {'path': path, **item} for item in private_attributes
    ]


def _typescript_graph_targets(
    path: str,
    content: str,
    all_paths: set[str],
) -> set[str]:
    return {
        target
        for imported in _typescript_imports(content)
        if (target := _resolve_ts_import(path, imported, all_paths))
        and target != path
    }


def _module_graph(
    snapshot: SourceSnapshot, source_paths: list[str], all_paths: set[str]
) -> tuple[dict[str, list[str]], list[dict], list[dict]]:
    module_to_path = {
        module: path for path in source_paths
        if (module := _module_name(path)) is not None
    }
    graph: dict[str, list[str]] = {}
    private_imports: list[dict] = []
    private_attributes: list[dict] = []
    for path in source_paths:
        content = snapshot.read(path)
        if path.endswith('.py'):
            targets, imports, attributes = _python_graph_details(
                path, content, module_to_path
            )
            private_imports.extend(imports)
            private_attributes.extend(attributes)
        else:
            targets = _typescript_graph_targets(path, content, all_paths)
        graph[path] = sorted(targets)
    return graph, private_imports, private_attributes


def _test_import_targets(
    path: str,
    content: str,
    module_to_path: dict[str, str],
    all_paths: set[str],
) -> set[str]:
    if path.endswith('.py'):
        imports, _ = _python_imports(content)
        return {
            target
            for imported, _names in imports
            if (target := _resolve_python_import(imported, module_to_path))
        }
    return {
        target
        for imported in _typescript_imports(content)
        if (target := _resolve_ts_import(path, imported, all_paths))
    }


def _test_links(
    snapshot: SourceSnapshot,
    test_paths: list[str],
    source_paths: list[str],
    registry: dict[str, Any],
) -> dict[str, set[str]]:
    all_paths = set(snapshot.paths())
    links: dict[str, set[str]] = defaultdict(set)
    module_to_path = {
        module: path for path in source_paths
        if (module := _module_name(path)) is not None
    }
    for path in test_paths:
        content = snapshot.read(path)
        for target in _test_import_targets(
            path, content, module_to_path, all_paths
        ):
            links[target].add(path)
    _attach_registry_tests(links, registry)
    return links


def _attach_registry_tests(links: dict[str, set[str]], registry: dict) -> None:
    for record in registry['computations']:
        for implementation in record['implementations']:
            links[implementation['path']].update(record['tests'])
