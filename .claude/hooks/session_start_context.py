#!/usr/bin/env python3
"""SessionStart hook: injects HANDOFF.md, NOW.md, and the most recent
SESSION_LOG.md entry into context so a fresh session (or post-compaction
continuation) knows where things stand."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.context_logic import build_context
from lib.paths import find_project_root


def main() -> int:
    data = json.load(sys.stdin)
    project_root = find_project_root(data.get("cwd", "."))
    context = build_context(project_root)

    if context:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }))

    return 0


if __name__ == "__main__":
    sys.exit(main())
