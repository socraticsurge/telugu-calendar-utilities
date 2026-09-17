"""Read-only Git access and an immutable source-revision handle."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_GIT_REF_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$')
_CONTROL_CHARACTER_RE = re.compile(r'[\0\n\r]')


def validate_ref(ref: str) -> None:
    if not _GIT_REF_RE.fullmatch(ref):
        raise ValueError(f'unsupported Git ref: {ref!r}')
    if '..' in ref:
        raise ValueError(f'unsupported Git ref: {ref!r}')
    if ref.endswith(('.', '/')):
        raise ValueError(f'unsupported Git ref: {ref!r}')


def validate_command(args: tuple[str, ...]) -> None:
    if not args:
        raise ValueError('unsupported Git command')
    if args[0] not in {'log', 'ls-tree', 'rev-parse', 'show'}:
        raise ValueError('unsupported Git command')
    if any(_CONTROL_CHARACTER_RE.search(argument) for argument in args):
        raise ValueError('Git arguments must not contain control characters')


@dataclass(frozen=True)
class GitRepository:
    root: Path

    def git(self, *args: str) -> str:
        validate_command(args)
        result = subprocess.run(
            ['git', *args], cwd=self.root, check=True, text=True,
            capture_output=True,
        )  # NOSONAR -- fixed executable, no shell, validated command/arguments
        return result.stdout

    def resolve_ref(self, ref: str) -> str:
        validate_ref(ref)
        commit = self.git(
            'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}',
        ).strip()
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise ValueError(f'Git ref did not resolve to a commit: {ref!r}')
        return commit


@dataclass(frozen=True)
class SourceSnapshot:
    repository: GitRepository
    commit: str

    def read(self, path: str) -> str:
        return self.repository.git('show', f'{self.commit}:{path}')

    def paths(self) -> list[str]:
        return sorted(self.repository.git(
            'ls-tree', '-r', '--name-only', self.commit,
        ).splitlines())
