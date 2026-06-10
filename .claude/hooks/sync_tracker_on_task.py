#!/usr/bin/env python3
"""PostToolUse hook (TaskUpdate completed): syncs TASKS.csv/STORIES.csv,
detects phase completion, and writes AWAITING_REVIEW.md. Convention: the
TaskUpdate `content` field must start with the task id in brackets, e.g.
"[T-001] Build login form"."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.file_lock import FileLock
from lib.paths import find_project_root
from lib.sync_logic import sync_task_completion

TASK_ID_PATTERN = re.compile(r"\[(T-\d+)\]")


def main() -> int:
    data = json.load(sys.stdin)

    if data.get("tool_name") != "TaskUpdate":
        return 0

    tool_input = data.get("tool_input", {})
    if tool_input.get("status") != "completed":
        return 0

    match = TASK_ID_PATTERN.search(tool_input.get("content", ""))
    if not match:
        return 0

    task_id = match.group(1)
    project_root = find_project_root(data.get("cwd", "."))
    lock_path = project_root / "docs" / "tracking" / ".lockdir"

    with FileLock(lock_path):
        phase_complete = sync_task_completion(project_root, task_id, tests_passed=True)

    if phase_complete:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "Phase complete: docs/plans/AWAITING_REVIEW.md has been written. "
                    "Call PushNotification to alert the user, then wait for approval "
                    "(file deleted or user says 'approved') before starting next-phase tasks."
                ),
            }
        }))

    return 0


if __name__ == "__main__":
    sys.exit(main())
