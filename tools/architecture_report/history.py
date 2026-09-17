"""Git-history collection and pure numstat aggregation."""
from __future__ import annotations

from collections import defaultdict

from .repository import SourceSnapshot


def _numstat_entry(line: str, source_paths: set[str]) -> tuple[str, str, str] | None:
    parts = line.split('\t')
    if len(parts) != 3:
        return None
    added, deleted, path = parts
    if path not in source_paths:
        return None
    if not added.isdigit():
        return None
    if not deleted.isdigit():
        return None
    return added, deleted, path


def parse_history(output: str, source_paths: set[str]) -> tuple[list[dict], dict]:
    per_file: dict[str, dict[str, int]] = defaultdict(
        lambda: {'commits': 0, 'added': 0, 'deleted': 0, 'churn': 0}
    )
    touched_in_commit: set[str] = set()
    commits: list[str] = []
    for line in output.splitlines():
        if line.startswith('COMMIT\t'):
            current_commit = line.split('\t', 1)[1]
            commits.append(current_commit)
            touched_in_commit = set()
            continue
        entry = _numstat_entry(line, source_paths)
        if entry is None:
            continue
        added, deleted, path = entry
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


def _history(snapshot: SourceSnapshot, source_paths: set[str], commit_limit: int):
    output = snapshot.repository.git(
        'log', '--no-merges', f'--max-count={commit_limit}',
        '--format=COMMIT\t%H', '--numstat', snapshot.commit, '--',
        'telugu_panchangam', 'scripts', 'src',
    )
    return parse_history(output, source_paths)
