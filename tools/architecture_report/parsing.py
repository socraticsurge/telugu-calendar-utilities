"""Pure source parsing and import resolution; no repository access."""
from __future__ import annotations

import ast
import re
from pathlib import PurePosixPath

_TS_FROM_IMPORT_RE = re.compile(r"\bfrom\s+['\"]([^'\"\n]+)['\"]")


_TS_SIDE_EFFECT_IMPORT_RE = re.compile(
    r"import\s+['\"]([^'\"\n]+)['\"]"
)


_TS_DEFINITION_RE = re.compile(
    r'^\s*(?:export\s+)?(?:async\s+)?'
    r'(?:function|class|interface|type|const|let|var)\s+[A-Za-z_$][\w$]*\b',
    re.MULTILINE,
)


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


def _engine_private_attribute(node: ast.AST) -> dict | None:
    if not isinstance(node, ast.Attribute):
        return None
    if not node.attr.startswith('_'):
        return None
    if not isinstance(node.value, ast.Name):
        return None
    if 'engine' not in node.value.id.lower():
        return None
    return {'line': node.lineno, 'expression': f'{node.value.id}.{node.attr}'}


def _node_imports(node: ast.AST) -> list[tuple[str, list[str]]]:
    if isinstance(node, ast.Import):
        return [(alias.name, []) for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if not node.module:
        return []
    return [(node.module, [alias.name for alias in node.names])]


def _python_imports(content: str) -> tuple[list[tuple[str, list[str]]], list[dict]]:
    tree = ast.parse(content)
    imports: list[tuple[str, list[str]]] = []
    private_attributes: list[dict] = []
    for node in ast.walk(tree):
        imports.extend(_node_imports(node))
        if (attribute := _engine_private_attribute(node)) is not None:
            private_attributes.append(attribute)
    return imports, private_attributes


def _typescript_import(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith(('import ', 'export ')):
        return None
    match = _TS_FROM_IMPORT_RE.search(stripped) or _TS_SIDE_EFFECT_IMPORT_RE.match(stripped)
    return match.group(1) if match else None


def _typescript_imports(content: str) -> list[str]:
    """Return static TypeScript imports without ambiguous regex backtracking."""
    return [
        imported for line in content.splitlines()
        if (imported := _typescript_import(line)) is not None
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
