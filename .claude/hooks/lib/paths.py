from pathlib import Path


def find_project_root(start) -> Path:
    """Walk up from `start` until a directory containing `.claude` is found."""
    p = Path(start).resolve()
    candidates = [p, *p.parents]
    for parent in candidates:
        if (parent / ".claude").is_dir():
            return parent
    raise FileNotFoundError(f"No .claude directory found above {start}")
