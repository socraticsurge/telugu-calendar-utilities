#!/usr/bin/env python3
"""PreCompact/Stop hook: diffs trackers against the last snapshot, appends a
SESSION_LOG entry, refreshes HANDOFF.md/NOW.md, commits tracker files to git,
and updates the snapshot."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.checkpoint_logic import run_checkpoint
from lib.paths import find_project_root


def main() -> int:
    data = json.load(sys.stdin)
    project_root = find_project_root(data.get("cwd", "."))

    run_checkpoint(project_root)

    subprocess.run(["git", "add", "docs/tracking", "docs/plans", "docs/NOW.md"],
                    cwd=project_root, capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: checkpoint trackers", "--allow-empty-message", "-q"],
                    cwd=project_root, capture_output=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
