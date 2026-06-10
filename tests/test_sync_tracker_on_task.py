import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))
from lib.csv_store import read_rows, write_rows

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "sync_tracker_on_task.py"

TASKS_FIELDS = ["task_id", "story_id", "phase", "description", "status", "estimate", "depends_on", "notes"]
STORIES_FIELDS = ["id", "role", "user_story", "status", "spec_ref", "notes"]


def _run_hook(payload, cwd):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _setup(tmp_path):
    (tmp_path / ".claude").mkdir()
    tracking = tmp_path / "docs" / "tracking"
    tracking.mkdir(parents=True)
    write_rows(tracking / "TASKS.csv", TASKS_FIELDS, [
        {"task_id": "T-001", "story_id": "US-01", "phase": "1", "description": "Build login form",
         "status": "in_progress", "estimate": "S", "depends_on": "", "notes": ""},
    ])
    write_rows(tracking / "STORIES.csv", STORIES_FIELDS, [
        {"id": "US-01", "role": "Admin", "user_story": "story", "status": "in_progress", "spec_ref": "", "notes": ""},
    ])


def test_extracts_task_id_and_marks_done(tmp_path):
    _setup(tmp_path)

    result = _run_hook(
        {
            "tool_name": "TaskUpdate",
            "tool_input": {"content": "[T-001] Build login form", "status": "completed"},
            "cwd": str(tmp_path),
        },
        cwd=str(tmp_path),
    )

    assert result.returncode == 0
    tasks = read_rows(tmp_path / "docs" / "tracking" / "TASKS.csv")
    assert tasks[0]["status"] == "done"


def test_announces_phase_complete_via_additional_context(tmp_path):
    _setup(tmp_path)

    result = _run_hook(
        {
            "tool_name": "TaskUpdate",
            "tool_input": {"content": "[T-001] Build login form", "status": "completed"},
            "cwd": str(tmp_path),
        },
        cwd=str(tmp_path),
    )

    output = json.loads(result.stdout)
    assert "PushNotification" in output["hookSpecificOutput"]["additionalContext"]


def test_ignores_non_task_update_tools(tmp_path):
    _setup(tmp_path)

    result = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": "x.py"}, "cwd": str(tmp_path)},
        cwd=str(tmp_path),
    )

    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_ignores_non_completed_status(tmp_path):
    _setup(tmp_path)

    result = _run_hook(
        {
            "tool_name": "TaskUpdate",
            "tool_input": {"content": "[T-001] Build login form", "status": "in_progress"},
            "cwd": str(tmp_path),
        },
        cwd=str(tmp_path),
    )

    assert result.returncode == 0
    tasks = read_rows(tmp_path / "docs" / "tracking" / "TASKS.csv")
    assert tasks[0]["status"] == "in_progress"
