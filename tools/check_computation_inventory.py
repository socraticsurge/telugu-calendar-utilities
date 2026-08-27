#!/usr/bin/env python3
"""Validate the canonical production-computation inventory."""
from __future__ import annotations

import ast
import json
import re
import sys
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
    'provenance', 'tests', 'limitations',
}
_REQUIRED_VOCABULARIES = {
    'owning_layers', 'claim_kinds', 'implementation_roles', 'surfaces',
    'evidence_classes', 'verification_states', 'exclusion_kinds',
}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding='utf-8') as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f'{path.relative_to(ROOT)} must contain a JSON object')
    return value


def _python_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    symbols: set[str] = set()

    def collect(body: list[ast.stmt], prefix: str = '') -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                name = f'{prefix}{node.name}'
                symbols.add(name)
                collect(node.body, f'{name}.')
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.add(f'{prefix}{node.name}')
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        symbols.add(f'{prefix}{target.id}')

    collect(tree.body)
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


def _relative_source_paths(registry: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    coverage = registry.get('coverage', {})
    roots = coverage.get('roots', []) if isinstance(coverage, dict) else []
    for item in roots:
        if not isinstance(item, dict):
            continue
        root_name = item.get('path')
        extensions = item.get('extensions')
        if not isinstance(root_name, str) or not _is_string_list(extensions):
            continue
        root = ROOT / root_name
        if not root.is_dir():
            continue
        for path in root.rglob('*'):
            if not path.is_file() or path.suffix not in extensions:
                continue
            relative = path.relative_to(ROOT)
            if '__tests__' in relative.parts:
                continue
            paths.add(relative.as_posix())
    return paths


def validate_registry(path: Path = REGISTRY_PATH) -> list[str]:
    """Return all validation failures without stopping at the first error."""
    errors: list[str] = []
    try:
        registry = _load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if registry.get('schema_version') != 1:
        errors.append('schema_version must be 1')

    vocabularies = registry.get('vocabularies')
    if not isinstance(vocabularies, dict):
        errors.append('vocabularies must be an object')
        vocabularies = {}
    missing_vocabularies = _REQUIRED_VOCABULARIES - set(vocabularies)
    if missing_vocabularies:
        errors.append(
            'missing vocabularies: ' + ', '.join(sorted(missing_vocabularies)))
    for name, values in vocabularies.items():
        if not _is_string_list(values):
            errors.append(f'vocabularies.{name} must be a non-empty string list')

    try:
        provenance = _load_json(PROVENANCE_PATH)
        provenance_claims = {
            claim['id'] for claim in provenance.get('claims', [])
            if isinstance(claim, dict) and isinstance(claim.get('id'), str)
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f'cannot load provenance registry: {exc}')
        provenance_claims = set()

    records = registry.get('computations')
    if not isinstance(records, list) or not records:
        errors.append('computations must be a non-empty list')
        records = []

    seen_ids: set[str] = set()
    referenced_paths: set[str] = set()
    symbol_cache: dict[str, set[str]] = {}
    for index, record in enumerate(records):
        label = f'computations[{index}]'
        if not isinstance(record, dict):
            errors.append(f'{label} must be an object')
            continue
        record_id = record.get('id')
        if not isinstance(record_id, str) or not _ID_RE.fullmatch(record_id):
            errors.append(f'{label}.id is not a stable identifier: {record_id!r}')
            record_id = label
        elif record_id in seen_ids:
            errors.append(f'duplicate computation id: {record_id}')
        else:
            seen_ids.add(record_id)
        label = record_id

        missing = _REQUIRED_RECORD_FIELDS - set(record)
        if missing:
            errors.append(f'{label}: missing fields: {", ".join(sorted(missing))}')
        for field in ('title', 'summary', 'time_basis'):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f'{label}.{field} must be a non-empty string')
        for field, vocabulary in (
            ('owning_layer', 'owning_layers'), ('claim_kind', 'claim_kinds')
        ):
            if record.get(field) not in vocabularies.get(vocabulary, []):
                errors.append(f'{label}.{field} is outside {vocabulary}')
        for field in ('inputs', 'outputs', 'surfaces', 'limitations'):
            if not _is_string_list(record.get(field)):
                errors.append(f'{label}.{field} must be a non-empty string list')
        for surface in record.get('surfaces', []):
            if surface not in vocabularies.get('surfaces', []):
                errors.append(f'{label}.surfaces contains unknown value: {surface}')

        implementations = record.get('implementations')
        if not isinstance(implementations, list) or not implementations:
            errors.append(f'{label}.implementations must be a non-empty list')
            implementations = []
        owner_found = False
        for impl_index, implementation in enumerate(implementations):
            impl_label = f'{label}.implementations[{impl_index}]'
            if not isinstance(implementation, dict):
                errors.append(f'{impl_label} must be an object')
                continue
            impl_path = implementation.get('path')
            symbol = implementation.get('symbol')
            role = implementation.get('role')
            if role not in vocabularies.get('implementation_roles', []):
                errors.append(f'{impl_label}.role is unknown: {role!r}')
            owner_found = owner_found or role == 'owner'
            if not isinstance(impl_path, str) or not impl_path:
                errors.append(f'{impl_label}.path must be a non-empty string')
                continue
            source = Path(impl_path)
            if source.is_absolute() or '..' in source.parts:
                errors.append(f'{impl_label}.path must be repository-relative')
                continue
            absolute = ROOT / source
            referenced_paths.add(source.as_posix())
            if not absolute.is_file():
                errors.append(f'{impl_label}.path does not exist: {impl_path}')
                continue
            if not isinstance(symbol, str) or not symbol:
                errors.append(f'{impl_label}.symbol must be a non-empty string')
                continue
            symbols = symbol_cache.setdefault(impl_path, _source_symbols(absolute))
            if symbol not in symbols:
                errors.append(f'{impl_label}.symbol not found in {impl_path}: {symbol}')
        if not owner_found:
            errors.append(f'{label} must have at least one owner implementation')

        tests = record.get('tests')
        if not _is_string_list(tests, allow_empty=True):
            errors.append(f'{label}.tests must be a string list')
            tests = []
        test_gap = record.get('test_gap')
        if not tests and (not isinstance(test_gap, str) or not test_gap.strip()):
            errors.append(f'{label} needs at least one test or a visible test_gap')
        for test_path in tests:
            relative_test = Path(test_path)
            if relative_test.is_absolute() or '..' in relative_test.parts:
                errors.append(f'{label}.tests path must be repository-relative: {test_path}')
            elif not (ROOT / relative_test).is_file():
                errors.append(f'{label}.tests path does not exist: {test_path}')

        provenance_record = record.get('provenance')
        if not isinstance(provenance_record, dict):
            errors.append(f'{label}.provenance must be an object')
            continue
        for field, vocabulary in (
            ('evidence_classes', 'evidence_classes'),
            ('verification_states', 'verification_states'),
        ):
            values = provenance_record.get(field)
            if not _is_string_list(values):
                errors.append(f'{label}.provenance.{field} must be non-empty')
                continue
            unknown = set(values) - set(vocabularies.get(vocabulary, []))
            if unknown:
                errors.append(
                    f'{label}.provenance.{field} contains unknown values: '
                    + ', '.join(sorted(unknown)))
        claim_ids = provenance_record.get('claim_ids')
        if not _is_string_list(claim_ids, allow_empty=True):
            errors.append(f'{label}.provenance.claim_ids must be a string list')
            claim_ids = []
        for claim_id in claim_ids:
            if claim_id not in provenance_claims:
                errors.append(f'{label}: unknown provenance claim id: {claim_id}')
        note = provenance_record.get('note')
        if not claim_ids and (not isinstance(note, str) or not note.strip()):
            errors.append(f'{label}: provenance without claim_ids needs a note')

    coverage = registry.get('coverage')
    if not isinstance(coverage, dict):
        errors.append('coverage must be an object')
        coverage = {}
    exclusions = coverage.get('exclusions')
    if not isinstance(exclusions, list):
        errors.append('coverage.exclusions must be a list')
        exclusions = []
    excluded_paths: set[str] = set()
    for index, exclusion in enumerate(exclusions):
        label = f'coverage.exclusions[{index}]'
        if not isinstance(exclusion, dict):
            errors.append(f'{label} must be an object')
            continue
        excluded_path = exclusion.get('path')
        kind = exclusion.get('kind')
        reason = exclusion.get('reason')
        if not isinstance(excluded_path, str) or not excluded_path:
            errors.append(f'{label}.path must be a non-empty string')
            continue
        if excluded_path in excluded_paths:
            errors.append(f'duplicate coverage exclusion: {excluded_path}')
        excluded_paths.add(excluded_path)
        if kind not in vocabularies.get('exclusion_kinds', []):
            errors.append(f'{label}.kind is unknown: {kind!r}')
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f'{label}.reason must be a non-empty string')
        if not (ROOT / excluded_path).is_file():
            errors.append(f'{label}.path does not exist: {excluded_path}')
        if excluded_path in referenced_paths:
            errors.append(f'{excluded_path} is both implemented and excluded')

    audited_paths = _relative_source_paths(registry)
    uncovered = audited_paths - referenced_paths - excluded_paths
    stale_exclusions = excluded_paths - audited_paths
    if uncovered:
        errors.append('unclassified production source paths: ' + ', '.join(sorted(uncovered)))
    if stale_exclusions:
        errors.append('exclusions outside coverage roots: ' + ', '.join(sorted(stale_exclusions)))

    return errors


def main() -> int:
    errors = validate_registry()
    if errors:
        for error in errors:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    registry = _load_json(REGISTRY_PATH)
    implementation_count = sum(
        len(record['implementations']) for record in registry['computations'])
    print(
        f"Computation inventory valid: {len(registry['computations'])} records, "
        f'{implementation_count} implementations, '
        f"{len(_relative_source_paths(registry))} audited source files."
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
