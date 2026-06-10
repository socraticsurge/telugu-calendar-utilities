from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.gate_logic import check_gate


def _make_project(tmp_path, with_spec=False, with_stories=False,
                   override=False, awaiting_review=False):
    (tmp_path / ".claude").mkdir()
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "tracking").mkdir(parents=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True)

    if with_spec:
        (tmp_path / "docs" / "specs" / "feature-design.md").write_text("# Spec")

    stories_csv = tmp_path / "docs" / "tracking" / "STORIES.csv"
    if with_stories:
        stories_csv.write_text("id,role,user_story,status,spec_ref,notes\nUS-01,Admin,story,not_started,,\n")
    else:
        stories_csv.write_text("id,role,user_story,status,spec_ref,notes\n")

    if override:
        (tmp_path / ".claude" / "harness-override").write_text("reason")

    if awaiting_review:
        (tmp_path / "docs" / "plans" / "AWAITING_REVIEW.md").write_text("waiting")

    return tmp_path


def test_blocks_source_edit_when_no_spec_or_stories(tmp_path):
    root = _make_project(tmp_path)
    src = root / "src" / "main.py"
    src.parent.mkdir(parents=True)
    src.write_text("")

    reason = check_gate("Edit", str(src), root)

    assert reason is not None
    assert "spec" in reason.lower()


def test_allows_source_edit_when_spec_and_stories_exist(tmp_path):
    root = _make_project(tmp_path, with_spec=True, with_stories=True)
    src = root / "src" / "main.py"
    src.parent.mkdir(parents=True)
    src.write_text("")

    reason = check_gate("Edit", str(src), root)

    assert reason is None


def test_allows_doc_edits_even_without_spec(tmp_path):
    root = _make_project(tmp_path)
    doc = root / "docs" / "specs" / "design.md"

    reason = check_gate("Write", str(doc), root)

    assert reason is None


def test_override_file_bypasses_gate(tmp_path):
    root = _make_project(tmp_path, override=True)
    src = root / "src" / "main.py"
    src.parent.mkdir(parents=True)
    src.write_text("")

    reason = check_gate("Edit", str(src), root)

    assert reason is None


def test_blocks_when_awaiting_review_even_with_spec(tmp_path):
    root = _make_project(tmp_path, with_spec=True, with_stories=True, awaiting_review=True)
    src = root / "src" / "main.py"
    src.parent.mkdir(parents=True)
    src.write_text("")

    reason = check_gate("Edit", str(src), root)

    assert reason is not None
    assert "review" in reason.lower()


def test_non_edit_tools_are_never_blocked(tmp_path):
    root = _make_project(tmp_path)

    reason = check_gate("Read", str(root / "src" / "main.py"), root)

    assert reason is None
