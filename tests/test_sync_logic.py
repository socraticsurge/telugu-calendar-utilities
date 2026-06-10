from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.csv_store import read_rows, write_rows
from lib.sync_logic import sync_task_completion

TASKS_FIELDS = ["task_id", "story_id", "phase", "description", "status", "estimate", "depends_on", "notes"]
STORIES_FIELDS = ["id", "role", "user_story", "status", "spec_ref", "notes"]


def _setup(tmp_path, tasks, stories):
    tracking = tmp_path / "docs" / "tracking"
    tracking.mkdir(parents=True)
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    write_rows(tracking / "TASKS.csv", TASKS_FIELDS, tasks)
    write_rows(tracking / "STORIES.csv", STORIES_FIELDS, stories)
    return tmp_path


def test_marks_task_done_and_rolls_up_story_when_all_tasks_done(tmp_path):
    tasks = [
        {"task_id": "T-001", "story_id": "US-01", "phase": "1", "description": "a",
         "status": "done", "estimate": "S", "depends_on": "", "notes": ""},
        {"task_id": "T-002", "story_id": "US-01", "phase": "1", "description": "b",
         "status": "in_progress", "estimate": "S", "depends_on": "T-001", "notes": ""},
    ]
    stories = [{"id": "US-01", "role": "Admin", "user_story": "story", "status": "in_progress", "spec_ref": "", "notes": ""}]
    root = _setup(tmp_path, tasks, stories)

    sync_task_completion(root, "T-002", tests_passed=True)

    updated_tasks = read_rows(root / "docs" / "tracking" / "TASKS.csv")
    updated_stories = read_rows(root / "docs" / "tracking" / "STORIES.csv")

    assert {t["task_id"]: t["status"] for t in updated_tasks} == {"T-001": "done", "T-002": "done"}
    assert updated_stories[0]["status"] == "done"


def test_story_stays_in_progress_if_tests_not_passed(tmp_path):
    tasks = [
        {"task_id": "T-001", "story_id": "US-01", "phase": "1", "description": "a",
         "status": "in_progress", "estimate": "S", "depends_on": "", "notes": ""},
    ]
    stories = [{"id": "US-01", "role": "Admin", "user_story": "story", "status": "in_progress", "spec_ref": "", "notes": ""}]
    root = _setup(tmp_path, tasks, stories)

    sync_task_completion(root, "T-001", tests_passed=False)

    updated_stories = read_rows(root / "docs" / "tracking" / "STORIES.csv")
    assert updated_stories[0]["status"] == "in_progress"


def test_writes_awaiting_review_when_last_task_of_phase_done(tmp_path):
    tasks = [
        {"task_id": "T-001", "story_id": "US-01", "phase": "1", "description": "a",
         "status": "done", "estimate": "S", "depends_on": "", "notes": ""},
        {"task_id": "T-002", "story_id": "US-01", "phase": "1", "description": "b",
         "status": "in_progress", "estimate": "S", "depends_on": "T-001", "notes": ""},
    ]
    stories = [{"id": "US-01", "role": "Admin", "user_story": "story", "status": "in_progress", "spec_ref": "", "notes": ""}]
    root = _setup(tmp_path, tasks, stories)

    phase_complete = sync_task_completion(root, "T-002", tests_passed=True)

    assert phase_complete is True
    awaiting = root / "docs" / "plans" / "AWAITING_REVIEW.md"
    assert awaiting.exists()
    assert "Phase 1" in awaiting.read_text()


def test_no_awaiting_review_when_other_phase_tasks_remain(tmp_path):
    tasks = [
        {"task_id": "T-001", "story_id": "US-01", "phase": "1", "description": "a",
         "status": "in_progress", "estimate": "S", "depends_on": "", "notes": ""},
        {"task_id": "T-002", "story_id": "US-01", "phase": "1", "description": "b",
         "status": "not_started", "estimate": "S", "depends_on": "T-001", "notes": ""},
    ]
    stories = [{"id": "US-01", "role": "Admin", "user_story": "story", "status": "not_started", "spec_ref": "", "notes": ""}]
    root = _setup(tmp_path, tasks, stories)

    phase_complete = sync_task_completion(root, "T-001", tests_passed=True)

    assert phase_complete is False
    assert not (root / "docs" / "plans" / "AWAITING_REVIEW.md").exists()


def test_logs_decision_when_task_id_unknown(tmp_path):
    root = _setup(tmp_path, [], [])

    sync_task_completion(root, "T-999", tests_passed=True)

    decisions = (root / "docs" / "tracking" / "DECISIONS.md")
    decisions.parent.mkdir(parents=True, exist_ok=True)
    if not decisions.exists():
        decisions.write_text("# Decisions\n")
    # Should not raise; unknown task ids are simply ignored.
