#!/usr/bin/env python3
"""Validate the canonical production-computation inventory."""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / 'docs/reference/computations.json'
PROVENANCE_PATH = ROOT / 'docs/reference/provenance.json'

_ID_RE = re.compile(r'^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$')
_TS_SYMBOL_RE = re.compile(
    r'^\s*(?:export\s+)?(?:async\s+)?'
    r'(?:function|class|interface|type|const|let|var)\s+([A-Za-z_$][\w$]*)\b',
    re.MULTILINE,
)
_REQUIRED_RECORD_FIELDS = {
    'id', 'title', 'summary', 'owning_layer', 'claim_kind',
    'implementations', 'inputs', 'outputs', 'time_basis', 'surfaces',
    'method', 'provenance', 'tests', 'limitations',
}
_REQUIRED_VOCABULARIES = {
    'owning_layers', 'claim_kinds', 'implementation_roles', 'surfaces',
    'evidence_classes', 'verification_states', 'exclusion_kinds', 'method_kinds',
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding='utf-8') as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f'{path.relative_to(ROOT)} must contain a JSON object')
    return value


def _collect_python_symbols(
    body: list[ast.stmt],
    symbols: set[str],
    prefix: str = '',
) -> None:
    for node in body:
        if isinstance(node, ast.ClassDef):
            name = f'{prefix}{node.name}'
            symbols.add(name)
            _collect_python_symbols(node.body, symbols, f'{name}.')
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.add(f'{prefix}{node.name}')
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            symbols.update(
                f'{prefix}{target.id}'
                for target in targets
                if isinstance(target, ast.Name)
            )


def _python_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    symbols: set[str] = set()
    _collect_python_symbols(tree.body, symbols)
    return symbols


def _source_symbols(path: Path) -> set[str]:
    if path.suffix == '.py':
        return _python_symbols(path)
    if path.suffix in {'.ts', '.tsx', '.js', '.mjs'}:
        return set(_TS_SYMBOL_RE.findall(path.read_text(encoding='utf-8')))
    return set()


def _is_string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _validate_formulae(
    label: str,
    kind: Any,
    method: dict[str, Any],
    errors: list[str],
) -> None:
    formulae = method.get('formulae', [])
    if not isinstance(formulae, list):
        errors.append(f'{label}.method.formulae must be a list')
        formulae = []
    if kind == 'formula' and not formulae:
        errors.append(f'{label}.method.formulae is required for formula methods')
    for index, formula in enumerate(formulae):
        formula_label = f'{label}.method.formulae[{index}]'
        if not isinstance(formula, dict):
            errors.append(f'{formula_label} must be an object')
            continue
        for field_name in ('name', 'expression'):
            value = formula.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f'{formula_label}.{field_name} must be a non-empty string'
                )
        if not _is_string_list(formula.get('variables')):
            errors.append(
                f'{formula_label}.variables must be a non-empty string list'
            )


def _validate_examples(
    label: str,
    method: dict[str, Any],
    errors: list[str],
) -> None:
    examples = method.get('worked_examples')
    if not isinstance(examples, list) or not examples:
        errors.append(f'{label}.method.worked_examples must be a non-empty list')
        examples = []
    for index, example in enumerate(examples):
        example_label = f'{label}.method.worked_examples[{index}]'
        if not isinstance(example, dict):
            errors.append(f'{example_label} must be an object')
            continue
        example_name = example.get('label')
        if not isinstance(example_name, str) or not example_name.strip():
            errors.append(f'{example_label}.label must be a non-empty string')
        for field_name in ('inputs', 'calculation', 'result'):
            if not _is_string_list(example.get(field_name)):
                errors.append(
                    f'{example_label}.{field_name} must be a non-empty string list'
                )


def _validate_method(
    label: str,
    method: Any,
    vocabularies: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate the required reproducible computation method."""
    if method is None:
        errors.append(f'{label}.method is required')
        return
    if not isinstance(method, dict):
        errors.append(f'{label}.method must be an object')
        return

    kind = method.get('kind')
    if kind not in vocabularies.get('method_kinds', []):
        errors.append(f'{label}.method.kind is unknown: {kind!r}')
    summary = method.get('summary')
    if not isinstance(summary, str) or not summary.strip():
        errors.append(f'{label}.method.summary must be a non-empty string')
    if not _is_string_list(method.get('steps')):
        errors.append(f'{label}.method.steps must be a non-empty string list')

    _validate_formulae(label, kind, method, errors)
    _validate_examples(label, method, errors)

    if 'notes' in method and not _is_string_list(method['notes']):
        errors.append(f'{label}.method.notes must be a non-empty string list')


def _coverage_root_paths(item: Any) -> set[str]:
    if not isinstance(item, dict):
        return set()
    root_name = item.get('path')
    extensions = item.get('extensions')
    if not isinstance(root_name, str) or not _is_string_list(extensions):
        return set()
    root = ROOT / root_name
    if not root.is_dir():
        return set()
    return {
        path.relative_to(ROOT).as_posix()
        for path in root.rglob('*')
        if path.is_file()
        and path.suffix in extensions
        and '__tests__' not in path.relative_to(ROOT).parts
    }


def _relative_source_paths(registry: dict[str, Any]) -> set[str]:
    coverage = registry.get('coverage', {})
    roots = coverage.get('roots', []) if isinstance(coverage, dict) else []
    return set().union(*(_coverage_root_paths(item) for item in roots))


@dataclass
class _RegistryState:
    errors: list[str] = field(default_factory=list)
    seen_ids: set[str] = field(default_factory=set)
    referenced_paths: set[str] = field(default_factory=set)
    symbol_cache: dict[str, set[str]] = field(default_factory=dict)


def _validate_vocabularies(
    registry: dict[str, Any], state: _RegistryState
) -> dict[str, Any]:
    vocabularies = registry.get('vocabularies')
    if not isinstance(vocabularies, dict):
        state.errors.append('vocabularies must be an object')
        vocabularies = {}
    missing = _REQUIRED_VOCABULARIES - set(vocabularies)
    if missing:
        state.errors.append('missing vocabularies: ' + ', '.join(sorted(missing)))
    for name, values in vocabularies.items():
        if not _is_string_list(values):
            state.errors.append(
                f'vocabularies.{name} must be a non-empty string list'
            )
    return vocabularies


def _load_provenance_claims(state: _RegistryState) -> set[str]:
    try:
        provenance = _load_json(PROVENANCE_PATH)
    except (OSError, ValueError) as exc:
        state.errors.append(f'cannot load provenance registry: {exc}')
        return set()
    return {
        claim['id']
        for claim in provenance.get('claims', [])
        if isinstance(claim, dict) and isinstance(claim.get('id'), str)
    }


def _record_label(
    record: dict[str, Any], index: int, state: _RegistryState
) -> str:
    fallback = f'computations[{index}]'
    record_id = record.get('id')
    if not isinstance(record_id, str) or not _ID_RE.fullmatch(record_id):
        state.errors.append(
            f'{fallback}.id is not a stable identifier: {record_id!r}'
        )
        return fallback
    if record_id in state.seen_ids:
        state.errors.append(f'duplicate computation id: {record_id}')
    else:
        state.seen_ids.add(record_id)
    return record_id


def _validate_record_fields(
    label: str,
    record: dict[str, Any],
    vocabularies: dict[str, Any],
    state: _RegistryState,
) -> None:
    missing = _REQUIRED_RECORD_FIELDS - set(record)
    if missing:
        state.errors.append(f'{label}: missing fields: {", ".join(sorted(missing))}')
    for field_name in ('title', 'summary', 'time_basis'):
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            state.errors.append(f'{label}.{field_name} must be a non-empty string')
    for field_name, vocabulary in (
        ('owning_layer', 'owning_layers'),
        ('claim_kind', 'claim_kinds'),
    ):
        if record.get(field_name) not in vocabularies.get(vocabulary, []):
            state.errors.append(f'{label}.{field_name} is outside {vocabulary}')
    for field_name in ('inputs', 'outputs', 'surfaces', 'limitations'):
        if not _is_string_list(record.get(field_name)):
            state.errors.append(
                f'{label}.{field_name} must be a non-empty string list'
            )
    for surface in record.get('surfaces', []):
        if surface not in vocabularies.get('surfaces', []):
            state.errors.append(f'{label}.surfaces contains unknown value: {surface}')
    _validate_method(label, record.get('method'), vocabularies, state.errors)


def _validate_implementations(
    label: str,
    record: dict[str, Any],
    vocabularies: dict[str, Any],
    state: _RegistryState,
) -> None:
    implementations = record.get('implementations')
    if not isinstance(implementations, list) or not implementations:
        state.errors.append(f'{label}.implementations must be a non-empty list')
        implementations = []
    owner_found = False
    for index, implementation in enumerate(implementations):
        item_label = f'{label}.implementations[{index}]'
        if not isinstance(implementation, dict):
            state.errors.append(f'{item_label} must be an object')
            continue
        role = implementation.get('role')
        if role not in vocabularies.get('implementation_roles', []):
            state.errors.append(f'{item_label}.role is unknown: {role!r}')
        owner_found = owner_found or role == 'owner'
        _validate_implementation_location(item_label, implementation, state)
    if not owner_found:
        state.errors.append(f'{label} must have at least one owner implementation')


def _validate_implementation_location(
    label: str,
    implementation: dict[str, Any],
    state: _RegistryState,
) -> None:
    path_value = implementation.get('path')
    symbol = implementation.get('symbol')
    if not isinstance(path_value, str) or not path_value:
        state.errors.append(f'{label}.path must be a non-empty string')
        return
    source = Path(path_value)
    if source.is_absolute() or '..' in source.parts:
        state.errors.append(f'{label}.path must be repository-relative')
        return
    absolute = ROOT / source
    state.referenced_paths.add(source.as_posix())
    if not absolute.is_file():
        state.errors.append(f'{label}.path does not exist: {path_value}')
        return
    if not isinstance(symbol, str) or not symbol:
        state.errors.append(f'{label}.symbol must be a non-empty string')
        return
    symbols = state.symbol_cache.setdefault(path_value, _source_symbols(absolute))
    if symbol not in symbols:
        state.errors.append(f'{label}.symbol not found in {path_value}: {symbol}')


def _validate_tests(
    label: str, record: dict[str, Any], state: _RegistryState
) -> None:
    tests = record.get('tests')
    if not _is_string_list(tests, allow_empty=True):
        state.errors.append(f'{label}.tests must be a string list')
        tests = []
    test_gap = record.get('test_gap')
    if not tests and (not isinstance(test_gap, str) or not test_gap.strip()):
        state.errors.append(f'{label} needs at least one test or a visible test_gap')
    for path_value in tests:
        relative = Path(path_value)
        if relative.is_absolute() or '..' in relative.parts:
            state.errors.append(
                f'{label}.tests path must be repository-relative: {path_value}'
            )
        elif not (ROOT / relative).is_file():
            state.errors.append(f'{label}.tests path does not exist: {path_value}')


def _validate_record_provenance(
    label: str,
    record: dict[str, Any],
    vocabularies: dict[str, Any],
    provenance_claims: set[str],
    state: _RegistryState,
) -> None:
    provenance = record.get('provenance')
    if not isinstance(provenance, dict):
        state.errors.append(f'{label}.provenance must be an object')
        return
    for field_name, vocabulary in (
        ('evidence_classes', 'evidence_classes'),
        ('verification_states', 'verification_states'),
    ):
        values = provenance.get(field_name)
        if not _is_string_list(values):
            state.errors.append(f'{label}.provenance.{field_name} must be non-empty')
            continue
        unknown = set(values) - set(vocabularies.get(vocabulary, []))
        if unknown:
            state.errors.append(
                f'{label}.provenance.{field_name} contains unknown values: '
                + ', '.join(sorted(unknown))
            )
    claim_ids = provenance.get('claim_ids')
    if not _is_string_list(claim_ids, allow_empty=True):
        state.errors.append(f'{label}.provenance.claim_ids must be a string list')
        claim_ids = []
    for claim_id in claim_ids:
        if claim_id not in provenance_claims:
            state.errors.append(f'{label}: unknown provenance claim id: {claim_id}')
    note = provenance.get('note')
    if not claim_ids and (not isinstance(note, str) or not note.strip()):
        state.errors.append(f'{label}: provenance without claim_ids needs a note')


def _validate_records(
    registry: dict[str, Any],
    vocabularies: dict[str, Any],
    provenance_claims: set[str],
    state: _RegistryState,
) -> None:
    records = registry.get('computations')
    if not isinstance(records, list) or not records:
        state.errors.append('computations must be a non-empty list')
        records = []
    for index, record in enumerate(records):
        fallback = f'computations[{index}]'
        if not isinstance(record, dict):
            state.errors.append(f'{fallback} must be an object')
            continue
        label = _record_label(record, index, state)
        _validate_record_fields(label, record, vocabularies, state)
        _validate_implementations(label, record, vocabularies, state)
        _validate_tests(label, record, state)
        _validate_record_provenance(
            label, record, vocabularies, provenance_claims, state
        )


def _validate_exclusion(
    index: int,
    exclusion: Any,
    vocabularies: dict[str, Any],
    state: _RegistryState,
    excluded_paths: set[str],
) -> None:
    label = f'coverage.exclusions[{index}]'
    if not isinstance(exclusion, dict):
        state.errors.append(f'{label} must be an object')
        return
    path_value = exclusion.get('path')
    if not isinstance(path_value, str) or not path_value:
        state.errors.append(f'{label}.path must be a non-empty string')
        return
    if path_value in excluded_paths:
        state.errors.append(f'duplicate coverage exclusion: {path_value}')
    excluded_paths.add(path_value)
    if exclusion.get('kind') not in vocabularies.get('exclusion_kinds', []):
        state.errors.append(f'{label}.kind is unknown: {exclusion.get("kind")!r}')
    reason = exclusion.get('reason')
    if not isinstance(reason, str) or not reason.strip():
        state.errors.append(f'{label}.reason must be a non-empty string')
    if not (ROOT / path_value).is_file():
        state.errors.append(f'{label}.path does not exist: {path_value}')
    if path_value in state.referenced_paths:
        state.errors.append(f'{path_value} is both implemented and excluded')


def _validate_coverage(
    registry: dict[str, Any],
    vocabularies: dict[str, Any],
    state: _RegistryState,
) -> None:
    coverage = registry.get('coverage')
    if not isinstance(coverage, dict):
        state.errors.append('coverage must be an object')
        coverage = {}
    exclusions = coverage.get('exclusions')
    if not isinstance(exclusions, list):
        state.errors.append('coverage.exclusions must be a list')
        exclusions = []
    excluded_paths: set[str] = set()
    for index, exclusion in enumerate(exclusions):
        _validate_exclusion(
            index, exclusion, vocabularies, state, excluded_paths
        )
    audited_paths = _relative_source_paths(registry)
    uncovered = audited_paths - state.referenced_paths - excluded_paths
    stale_exclusions = excluded_paths - audited_paths
    if uncovered:
        state.errors.append(
            'unclassified production source paths: ' + ', '.join(sorted(uncovered))
        )
    if stale_exclusions:
        state.errors.append(
            'exclusions outside coverage roots: '
            + ', '.join(sorted(stale_exclusions))
        )


def validate_registry(path: Path = REGISTRY_PATH) -> list[str]:
    """Return all validation failures without stopping at the first error."""
    try:
        registry = _load_json(path)
    except (OSError, ValueError) as exc:
        return [str(exc)]

    state = _RegistryState()
    if registry.get('schema_version') != 1:
        state.errors.append('schema_version must be 1')
    vocabularies = _validate_vocabularies(registry, state)
    provenance_claims = _load_provenance_claims(state)
    _validate_records(registry, vocabularies, provenance_claims, state)
    _validate_coverage(registry, vocabularies, state)
    return state.errors


def main() -> int:
    errors = validate_registry()
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    registry = _load_json(REGISTRY_PATH)
    implementation_count = sum(
        len(record['implementations']) for record in registry['computations'])
    method_count = sum(
        'method' in record for record in registry['computations'])
    print(
        f"Computation inventory valid: {len(registry['computations'])} records, "
        f'{implementation_count} implementations, '
        f"{len(_relative_source_paths(registry))} audited source files, "
        f'{method_count}/{len(registry["computations"])} methods documented.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
