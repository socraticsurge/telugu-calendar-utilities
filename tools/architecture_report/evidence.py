"""Aggregate module, consumer and cross-layer facts without rendering."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .parsing import _definition_metrics
from .repository import SourceSnapshot
from .scope import _layer, source_scope_class


@dataclass(frozen=True)
class ModuleRelations:
    graph: dict[str, list[str]]
    incoming: dict[str, set[str]]
    linked_computations: dict[str, set[str]]
    test_links: dict[str, set[str]]


def _consumer_evidence(
    registry: dict[str, Any],
) -> tuple[dict[str, set[str]], list[dict]]:
    linked: dict[str, set[str]] = defaultdict(set)
    consumers: list[dict] = []
    for record in registry['computations']:
        owners: list[str] = []
        mirrors: list[str] = []
        for implementation in record['implementations']:
            linked[implementation['path']].add(record['id'])
            destination = owners if implementation['role'] == 'owner' else mirrors
            destination.append(implementation['path'])
        consumers.append({
            'id': record['id'],
            'owners': sorted(set(owners)),
            'mirrors': sorted(set(mirrors)),
            'surfaces': record['surfaces'],
            'tests': record['tests'],
        })
    return linked, consumers


def _edge_evidence(
    graph: dict[str, list[str]],
) -> tuple[dict[str, set[str]], Counter, list[dict]]:
    incoming: dict[str, set[str]] = defaultdict(set)
    cross_layer = Counter()
    details: list[dict] = []
    for source, targets in graph.items():
        for target in targets:
            incoming[target].add(source)
            edge = (_layer(source), _layer(target))
            if edge[0] == edge[1]:
                continue
            cross_layer[edge] += 1
            details.append({
                'from': source,
                'from_layer': edge[0],
                'to': target,
                'to_layer': edge[1],
            })
    return incoming, cross_layer, details


def _module_evidence(
    snapshot: SourceSnapshot, source_paths: list[str], relations: ModuleRelations,
) -> tuple[list[dict], dict[str, dict[str, int]]]:
    modules: list[dict] = []
    layer_metrics: dict[str, dict[str, int]] = defaultdict(
        lambda: {'files': 0, 'nonblank_lines': 0, 'definitions': 0}
    )
    for path in source_paths:
        content = snapshot.read(path)
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
            'imports_out': relations.graph[path],
            'importers_in': sorted(relations.incoming[path]),
            'computation_ids': sorted(relations.linked_computations[path]),
            'linked_tests': sorted(relations.test_links[path]),
        })
    return modules, layer_metrics


def _attach_history(modules: list[dict], history: list[dict]) -> None:
    history_by_path = {item['path']: item for item in history}
    for module in modules:
        module['history'] = history_by_path.get(
            module['path'],
            {'commits': 0, 'added': 0, 'deleted': 0, 'churn': 0},
        )


def _concrete_engine_imports(details: list[dict]) -> list[dict]:
    public_engine_modules = {
        'telugu_panchangam/engines/__init__.py',
        'telugu_panchangam/engines/utils.py',
    }
    return [
        detail
        for detail in details
        if detail['to_layer'] == 'engines'
        and detail['from_layer'] != 'engines'
        and detail['to'] not in public_engine_modules
    ]


def _top_blast_radius(modules: list[dict]) -> list[dict]:
    return sorted(
        (
            {
                'path': module['path'],
                'linked_test_count': len(module['linked_tests']),
                'linked_computation_count': len(module['computation_ids']),
            }
            for module in modules
        ),
        key=lambda item: (
            -item['linked_test_count'],
            -item['linked_computation_count'],
            item['path'],
        ),
    )
