import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "gate_spec_required.py"


def _run_hook(payload, cwd):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_blocks_edit_with_exit_code_2_when_no_spec(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "tracking").mkdir(parents=True)
    (tmp_path / "docs" / "tracking" / "STORIES.csv").write_text("id,role,user_story,status,spec_ref,notes\n")
    src = tmp_path / "src" / "main.py"
    src.parent.mkdir(parents=True)
    src.write_text("")

    result = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": str(src)}, "cwd": str(tmp_path)},
        cwd=str(tmp_path),
    )

    assert result.returncode == 2
    assert "spec" in result.stderr.lower()


def test_allows_edit_when_spec_and_stories_exist(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "tracking").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "feature-design.md").write_text("# Spec")
    (tmp_path / "docs" / "tracking" / "STORIES.csv").write_text(
        "id,role,user_story,status,spec_ref,notes\nUS-01,Admin,story,not_started,,\n"
    )
    src = tmp_path / "src" / "main.py"
    src.parent.mkdir(parents=True)
    src.write_text("")

    result = _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": str(src)}, "cwd": str(tmp_path)},
        cwd=str(tmp_path),
    )

    assert result.returncode == 0


def test_allows_when_no_file_path_in_tool_input(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "tracking").mkdir(parents=True)
    (tmp_path / "docs" / "tracking" / "STORIES.csv").write_text("id,role,user_story,status,spec_ref,notes\n")

    result = _run_hook(
        {"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(tmp_path)},
        cwd=str(tmp_path),
    )

    assert result.returncode == 0
