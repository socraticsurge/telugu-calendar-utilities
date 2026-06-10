from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.csv_store import write_rows
from lib.checkpoint_logic import run_checkpoint

TASKS_FIELDS = ["task_id", "story_id", "phase", "description", "status", "estimate", "depends_on", "notes"]
STORIES_FIELDS = ["id", "role", "user_story", "status", "spec_ref", "notes"]


def _setup(tmp_path):
    (tmp_path / ".claude").mkdir()
    tracking = tmp_path / "docs" / "tracking"
    snapshot = tracking / ".checkpoint-snapshot"
    snapshot.mkdir(parents=True)
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)

    (tracking / "SESSION_LOG.md").write_text("# Session Log\n")
    (tracking / "DECISIONS.md").write_text("# Decisions\n")
    (tmp_path / "docs" / "NOW.md").write_text("")

    write_rows(snapshot / "TASKS.csv", TASKS_FIELDS, [])
    write_rows(snapshot / "STORIES.csv", STORIES_FIELDS, [])

    write_rows(tracking / "TASKS.csv", TASKS_FIELDS, [
        {"task_id": "T-001", "story_id": "US-01", "phase": "1", "description": "Build login form",
         "status": "done", "estimate": "S", "depends_on": "", "notes": ""},
    ])
    write_rows(tracking / "STORIES.csv", STORIES_FIELDS, [
        {"id": "US-01", "role": "Admin", "user_story": "story", "status": "done", "spec_ref": "", "notes": ""},
    ])


def test_appends_session_log_entry_for_newly_completed_work(tmp_path):
    _setup(tmp_path)

    run_checkpoint(tmp_path, now=datetime(2026, 6, 10, 14, 32))

    log = (tmp_path / "docs" / "tracking" / "SESSION_LOG.md").read_text()
    assert "2026-06-10 14:32" in log
    assert "T-001" in log
    assert "US-01" in log


def test_writes_handoff_and_now(tmp_path):
    _setup(tmp_path)

    run_checkpoint(tmp_path, now=datetime(2026, 6, 10, 14, 32))

    handoff = (tmp_path / "docs" / "plans" / "HANDOFF.md")
    now_file = (tmp_path / "docs" / "NOW.md")
    assert handoff.exists()
    assert now_file.read_text().strip() != ""


def test_updates_snapshot_to_current_state(tmp_path):
    _setup(tmp_path)

    run_checkpoint(tmp_path, now=datetime(2026, 6, 10, 14, 32))

    from lib.csv_store import read_rows
    snapshot_tasks = read_rows(tmp_path / "docs" / "tracking" / ".checkpoint-snapshot" / "TASKS.csv")
    assert snapshot_tasks[0]["status"] == "done"


def test_second_checkpoint_with_no_changes_logs_nothing_new(tmp_path):
    _setup(tmp_path)
    run_checkpoint(tmp_path, now=datetime(2026, 6, 10, 14, 32))
    log_after_first = (tmp_path / "docs" / "tracking" / "SESSION_LOG.md").read_text()

    run_checkpoint(tmp_path, now=datetime(2026, 6, 10, 15, 0))

    log_after_second = (tmp_path / "docs" / "tracking" / "SESSION_LOG.md").read_text()
    assert "15:00" not in log_after_second
    assert log_after_second == log_after_first
