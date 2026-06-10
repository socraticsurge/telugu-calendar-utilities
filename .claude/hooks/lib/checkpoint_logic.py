import shutil
from datetime import datetime
from pathlib import Path

from lib.csv_store import read_rows, write_rows

TASKS_FIELDS = ["task_id", "story_id", "phase", "description", "status", "estimate", "depends_on", "notes"]
STORIES_FIELDS = ["id", "role", "user_story", "status", "spec_ref", "notes"]


def _diff_done_ids(old_rows, new_rows, id_field):
    old_status = {r[id_field]: r["status"] for r in old_rows}
    return [r[id_field] for r in new_rows if r["status"] == "done" and old_status.get(r[id_field]) != "done"]


def run_checkpoint(project_root, now: datetime | None = None) -> None:
    """Diff trackers against the last snapshot, append a SESSION_LOG entry
    if anything changed, refresh HANDOFF.md and NOW.md, and update the
    snapshot. No LLM calls -- pure file diffing."""
    project_root = Path(project_root)
    now = now or datetime.now()
    tracking = project_root / "docs" / "tracking"
    snapshot = tracking / ".checkpoint-snapshot"
    snapshot.mkdir(parents=True, exist_ok=True)

    tasks = read_rows(tracking / "TASKS.csv")
    stories = read_rows(tracking / "STORIES.csv")
    old_tasks = read_rows(snapshot / "TASKS.csv")
    old_stories = read_rows(snapshot / "STORIES.csv")

    completed_tasks = _diff_done_ids(old_tasks, tasks, "task_id")
    done_stories = _diff_done_ids(old_stories, stories, "id")

    if completed_tasks or done_stories:
        _append_session_log(tracking / "SESSION_LOG.md", now, completed_tasks, done_stories)

    _write_handoff(project_root, tasks)
    _write_now(project_root, tasks, stories)

    if tasks:
        write_rows(snapshot / "TASKS.csv", TASKS_FIELDS, tasks)
    if stories:
        write_rows(snapshot / "STORIES.csv", STORIES_FIELDS, stories)


def _append_session_log(path: Path, now: datetime, completed_tasks, done_stories) -> None:
    lines = [f"\n## {now:%Y-%m-%d %H:%M} — checkpoint\n"]
    if completed_tasks:
        lines.append(f"- Tasks completed: {', '.join(completed_tasks)}\n")
    if done_stories:
        lines.append(f"- Stories now done: {', '.join(done_stories)}\n")
    with open(path, "a", encoding="utf-8") as f:
        f.writelines(lines)


def _write_handoff(project_root: Path, tasks) -> None:
    in_progress = [t for t in tasks if t["status"] == "in_progress"]
    not_started = [t for t in tasks if t["status"] == "not_started"]

    lines = ["# Handoff\n"]
    if in_progress:
        lines.append("\nIn progress:\n")
        for t in in_progress:
            lines.append(f"- {t['task_id']}: {t['description']}\n")
    else:
        lines.append("\nNothing in progress.\n")

    if not_started:
        lines.append("\nNext up:\n")
        for t in not_started[:5]:
            lines.append(f"- {t['task_id']}: {t['description']}\n")

    (project_root / "docs" / "plans" / "HANDOFF.md").write_text("".join(lines))


def _write_now(project_root: Path, tasks, stories) -> None:
    awaiting = (project_root / "docs" / "plans" / "AWAITING_REVIEW.md").exists()
    status_line = "⏸ AWAITING YOUR REVIEW" if awaiting else "▶ in progress"

    not_started = [t for t in tasks if t["status"] == "not_started"]

    phases = sorted({t["phase"] for t in tasks}, key=lambda p: (len(p), p))
    current_phase = next((t["phase"] for t in tasks if t["status"] in ("in_progress", "not_started")), phases[-1] if phases else "-")

    phase_story_ids = {t["story_id"] for t in tasks if t["phase"] == current_phase}
    done_stories_this_phase = [s["id"] for s in stories if s["status"] == "done" and s["id"] in phase_story_ids]

    what_needed = (
        "Review docs/plans/AWAITING_REVIEW.md, then delete it (or say 'approved')"
        if awaiting else "nothing — walk away"
    )

    lines = [
        "## Right now\n",
        f"- Phase: {current_phase} of {phases[-1] if phases else '-'}\n",
        f"- Status: {status_line}\n",
        f"- What I need from you: {what_needed}\n",
        f"- Stories done this phase: {', '.join(done_stories_this_phase) if done_stories_this_phase else 'none'}\n",
        f"- Next up: {', '.join(t['task_id'] for t in not_started[:5]) if not_started else '-'}\n",
    ]
    (project_root / "docs" / "NOW.md").write_text("".join(lines))
