"""Compose the stable schema from a single pinned Git revision."""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import _ACTIVITY_RULES_ARTIFACT, _duplicate_contracts, _engine_asymmetry
from .evidence import (
    ModuleRelations,
    _attach_history,
    _concrete_engine_imports,
    _consumer_evidence,
    _edge_evidence,
    _module_evidence,
    _top_blast_radius,
)
from .graph import _module_graph, _test_links
from .history import _history
from .repository import GitRepository, SourceSnapshot
from .scope import _is_source, _is_test, source_scope_class

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HISTORY_COMMITS = 200
MAX_HISTORY_COMMITS = 10_000


def _scope_evidence(source_paths, test_paths, registry, history_window):
    additive = sum(source_scope_class(path) == 'additive-feature' for path in source_paths)
    return {
        'source_files': len(source_paths),
        'established_source_files': len(source_paths) - additive,
        'additive_feature_source_files': additive,
        'total_source_files': len(source_paths),
        'test_files': len(test_paths),
        'computation_records': len(registry['computations']),
        'history_requested_non_merge_commits': history_window['history_requested_non_merge_commits'],
        **history_window,
    }


def _api_boundary(private_imports, private_attributes, cross_layer_details):
    unique_imports = {
        (item['importer'], item['owner'], item['symbol']) for item in private_imports
    }
    return {
        'private_symbol_imports': [
            {'importer': importer, 'owner': owner, 'symbol': symbol}
            for importer, owner, symbol in sorted(unique_imports)
        ],
        'engine_private_attribute_access': sorted(
            private_attributes, key=lambda item: (item['path'], item['line']),
        ),
        'concrete_engine_module_imports': sorted(
            _concrete_engine_imports(cross_layer_details),
            key=lambda item: (item['from'], item['to']),
        ),
    }


def _generated_contract(snapshot: SourceSnapshot):
    generated = json.loads(snapshot.read(_ACTIVITY_RULES_ARTIFACT))
    return {
        'source': 'telugu_panchangam/personal/activity_rules.py',
        'generator': 'tools/export_activity_rules.py',
        'artifact': _ACTIVITY_RULES_ARTIFACT,
        'exported_rule_count': len(generated['rules']),
    }


def build_report(ref: str = 'HEAD', commit_limit: int = DEFAULT_HISTORY_COMMITS) -> dict:
    """Build a deterministic architecture report for one Git tree and history."""
    if not 1 <= commit_limit <= MAX_HISTORY_COMMITS:
        raise ValueError(
            f'commit_limit must be between 1 and {MAX_HISTORY_COMMITS}'
        )
    repository = GitRepository(ROOT)
    commit = repository.resolve_ref(ref)
    snapshot = SourceSnapshot(repository, commit)
    tree_paths = snapshot.paths()
    all_paths = set(tree_paths)
    source_paths = [path for path in tree_paths if _is_source(path)]
    test_paths = [path for path in tree_paths if _is_test(path)]
    registry = json.loads(snapshot.read('docs/reference/computations.json'))
    graph, private_imports, private_attributes = _module_graph(
        snapshot, source_paths, all_paths,
    )
    test_links = _test_links(
        snapshot, test_paths, source_paths, registry,
    )

    linked_computations, consumer_map = _consumer_evidence(registry)
    incoming, cross_layer, cross_layer_details = _edge_evidence(graph)
    modules, layer_metrics = _module_evidence(
        snapshot, source_paths,
        ModuleRelations(graph, incoming, linked_computations, test_links),
    )

    history, history_window = _history(
        snapshot, set(source_paths), commit_limit,
    )
    history_window['history_requested_non_merge_commits'] = commit_limit
    _attach_history(modules, history)
    top_blast_radius = _top_blast_radius(modules)

    return {
        'schema_version': 1,
        'source_commit': commit,
        'scope': _scope_evidence(source_paths, test_paths, registry, history_window),
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
        'api_boundary': _api_boundary(private_imports, private_attributes, cross_layer_details),
        'engine_asymmetry': _engine_asymmetry(snapshot),
        'duplicate_contracts': _duplicate_contracts(snapshot),
        'generated_contracts': [_generated_contract(snapshot)],
        'history_top_changed_files': history[:25],
        'test_blast_radius': top_blast_radius[:25],
    }
