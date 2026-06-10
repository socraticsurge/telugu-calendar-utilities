from pathlib import Path

from lib.csv_store import read_rows, write_rows

TASKS_FIELDS = ["task_id", "story_id", "phase", "description", "status", "estimate", "depends_on", "notes"]
STORIES_FIELDS = ["id", "role", "user_story", "status", "spec_ref", "notes"]


def sync_task_completion(project_root, task_id: str, tests_passed: bool) -> bool:
    """Mark `task_id` done, roll up its story's status, and detect phase completion.

    Returns True if this completion finished the last task of its phase
    (and AWAITING_REVIEW.md was written), False otherwise.
    """
    project_root = Path(project_root)
    tracking = project_root / "docs" / "tracking"
    tasks_path = tracking / "TASKS.csv"
    stories_path = tracking / "STORIES.csv"

    tasks = read_rows(tasks_path)
    target = next((t for t in tasks if t["task_id"] == task_id), None)
    if target is None:
        return False

    target["status"] = "done"
    write_rows(tasks_path, TASKS_FIELDS, tasks)

    story_id = target["story_id"]
    phase = target["phase"]

    if tests_passed:
        story_tasks = [t for t in tasks if t["story_id"] == story_id]
        if all(t["status"] == "done" for t in story_tasks):
            stories = read_rows(stories_path)
            for s in stories:
                if s["id"] == story_id:
                    s["status"] = "done"
            write_rows(stories_path, STORIES_FIELDS, stories)

    phase_tasks = [t for t in tasks if t["phase"] == phase]
    phase_complete = all(t["status"] == "done" for t in phase_tasks)

    if phase_complete:
        _write_awaiting_review(project_root, phase, phase_tasks)

    return phase_complete


def _write_awaiting_review(project_root: Path, phase: str, phase_tasks: list[dict]) -> None:
    plans_dir = project_root / "docs" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    task_ids = ", ".join(t["task_id"] for t in phase_tasks)
    content = (
        f"# Awaiting Review: Phase {phase}\n\n"
        f"All tasks in Phase {phase} are done and verified: {task_ids}\n\n"
        "Review the changes, then delete this file (or tell Claude \"approved\") "
        "to allow the next phase to start.\n"
    )
    (plans_dir / "AWAITING_REVIEW.md").write_text(content)
