from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.csv_store import read_rows, write_rows


def test_write_then_read_round_trip(tmp_path):
    path = tmp_path / "STORIES.csv"
    fieldnames = ["id", "role", "user_story", "status", "spec_ref", "notes"]
    rows = [
        {"id": "US-01", "role": "Admin", "user_story": "As an Admin...",
         "status": "not_started", "spec_ref": "", "notes": ""},
    ]

    write_rows(path, fieldnames, rows)
    result = read_rows(path)

    assert result == rows


def test_write_is_atomic_no_leftover_tmp_file(tmp_path):
    path = tmp_path / "TASKS.csv"
    fieldnames = ["task_id", "status"]
    write_rows(path, fieldnames, [{"task_id": "T-001", "status": "done"}])

    assert path.exists()
    assert not (tmp_path / "TASKS.csv.tmp").exists()


def test_read_rows_missing_file_returns_empty_list(tmp_path):
    path = tmp_path / "missing.csv"

    assert read_rows(path) == []
