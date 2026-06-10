from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.context_logic import build_context


def test_includes_handoff_now_and_recent_log(tmp_path):
    (tmp_path / ".claude").mkdir()
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    tracking = tmp_path / "docs" / "tracking"
    tracking.mkdir(parents=True)

    (plans / "HANDOFF.md").write_text("In progress: T-002, waiting on API key.")
    (tmp_path / "docs" / "NOW.md").write_text("## Right now\n- Phase: 1 of 3")
    (tracking / "SESSION_LOG.md").write_text(
        "# Session Log\n\n## 2026-06-09 10:00\n- did A\n\n## 2026-06-10 09:00\n- did B\n"
    )

    context = build_context(tmp_path)

    assert "In progress: T-002" in context
    assert "Phase: 1 of 3" in context
    assert "did B" in context


def test_handles_missing_files_gracefully(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "tracking").mkdir(parents=True)

    context = build_context(tmp_path)

    assert context == ""
