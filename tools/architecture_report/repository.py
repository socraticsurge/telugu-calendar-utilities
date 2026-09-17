"""Read-only Git access and an immutable source-revision handle."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .git_validation import (
    validate_command,
    validate_commit,
    validate_history_limit,
    validate_path,
    validate_ref,
)


@dataclass(frozen=True)
class GitRepository:
    root: Path

    def git(self, *args: str) -> str:
        """Compatibility entrypoint; arbitrary Git options are not accepted."""
        validate_command(args)
        result = subprocess.run(
            ['git', *args], cwd=self.root, check=True, text=True,
            capture_output=True,
        )
        return result.stdout

    def resolve_ref(self, ref: str) -> str:
        validate_ref(ref)
        commit = self.git(
            'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}',
        ).strip()
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise ValueError(f'Git ref did not resolve to a commit: {ref!r}')
        return commit

    def read_blob(self, commit: str, path: str) -> str:
        validate_commit(commit)
        validate_path(path)
        return self.git('show', f'{commit}:{path}')

    def list_paths(self, commit: str) -> list[str]:
        validate_commit(commit)
        return sorted(self.git('ls-tree', '-r', '--name-only', commit).splitlines())

    def read_history(self, commit: str, limit: int) -> str:
        validate_commit(commit)
        validate_history_limit(limit)
        return self.git(
            'log', '--no-merges', f'--max-count={limit}',
            '--format=COMMIT\t%H', '--numstat', commit, '--',
            'telugu_panchangam', 'scripts', 'src',
        )


@dataclass(frozen=True)
class SourceSnapshot:
    repository: GitRepository
    commit: str

    def __post_init__(self) -> None:
        validate_commit(self.commit)

    def read(self, path: str) -> str:
        return self.repository.read_blob(self.commit, path)

    def paths(self) -> list[str]:
        return self.repository.list_paths(self.commit)
