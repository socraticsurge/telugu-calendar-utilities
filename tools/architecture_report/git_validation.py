"""Exact command grammars for the reporter's four read-only Git operations."""
from __future__ import annotations

import re

_GIT_REF_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$')
_CONTROL_CHARACTER_RE = re.compile(r'[\0\n\r]')


def _validate_text(value: str) -> None:
    if not isinstance(value, str):
        raise ValueError('Git arguments must be strings')
    if _CONTROL_CHARACTER_RE.search(value):
        raise ValueError('Git arguments must not contain control characters')


def _validate_ref_token(ref: str) -> None:
    if not isinstance(ref, str):
        raise ValueError(f'unsupported Git ref: {ref!r}')
    if not _GIT_REF_RE.fullmatch(ref):
        raise ValueError(f'unsupported Git ref: {ref!r}')


def validate_ref(ref: str) -> None:
    _validate_ref_token(ref)
    if '..' in ref or ref.endswith(('.', '/')):
        raise ValueError(f'unsupported Git ref: {ref!r}')


def validate_commit(commit: str) -> None:
    _validate_text(commit)
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Git reads require a pinned 40-character commit ID')


def validate_path(path: str) -> None:
    _validate_text(path)
    if '\\' in path:
        raise ValueError('Git blob paths must use forward slashes')
    if any(part in {'', '.', '..'} for part in path.split('/')):
        raise ValueError('Git blob paths must be canonical and repository-relative')


def validate_history_limit(limit: int) -> None:
    if type(limit) is not int:
        raise ValueError('Git history limit must be an integer')
    if not 1 <= limit <= 10_000:
        raise ValueError('Git history limit must be between 1 and 10000')


def _validate_revision(revision: str) -> None:
    if not revision.endswith('^{commit}'):
        raise ValueError('Git resolution must require a commit')
    validate_ref(revision.removesuffix('^{commit}'))


def _validate_blob(blob: str) -> None:
    commit, separator, path = blob.partition(':')
    if not separator:
        raise ValueError('Git show must read a pinned blob')
    validate_commit(commit)
    validate_path(path)


def _validate_count_option(option: str) -> None:
    match = re.fullmatch(r'--max-count=([1-9]\d{0,4})', option, flags=re.ASCII)
    if match is None:
        raise ValueError('unsupported Git history limit option')
    validate_history_limit(int(match.group(1)))


def validate_command(args: tuple[str, ...]) -> None:
    """Validate every argument immediately before the process-launch sink."""
    for argument in args:
        _validate_text(argument)
    match args:
        case ('rev-parse', '--verify', '--end-of-options', revision):
            _validate_revision(revision)
        case ('show', blob):
            _validate_blob(blob)
        case ('ls-tree', '-r', '--name-only', commit):
            validate_commit(commit)
        case ('log', '--no-merges', limit, '--format=COMMIT\t%H', '--numstat',
              commit, '--', 'telugu_panchangam', 'scripts', 'src'):
            _validate_count_option(limit)
            validate_commit(commit)
        case _:
            raise ValueError('unsupported Git command shape')
