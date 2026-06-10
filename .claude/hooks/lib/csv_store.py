import csv
from pathlib import Path


def read_rows(path) -> list[dict]:
    """Read a CSV file into a list of dicts. Returns [] if the file doesn't exist."""
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path, fieldnames, rows) -> None:
    """Write rows to a CSV file atomically (write to .tmp, then rename)."""
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp_path.replace(path)
