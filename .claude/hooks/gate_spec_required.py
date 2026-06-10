#!/usr/bin/env python3
"""PreToolUse hook: blocks Edit/Write on source files unless a spec and
stories exist (and no phase is awaiting review). See docs/specs/2026-06-10-
spec-driven-harness-design.md section 4."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.gate_logic import check_gate
from lib.paths import find_project_root


def main() -> int:
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path")

    if not file_path:
        return 0

    project_root = find_project_root(data.get("cwd", "."))
    reason = check_gate(tool_name, file_path, project_root)

    if reason:
        print(reason, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
