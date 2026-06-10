from pathlib import Path

from lib.csv_store import read_rows

GATED_TOOLS = ("Edit", "Write")
EXEMPT_PREFIXES = ("docs/", ".claude/")


def _relative_to_root(file_path, project_root) -> str:
    return str(Path(file_path).resolve().relative_to(Path(project_root).resolve()))


def _is_exempt(rel_path: str) -> bool:
    return rel_path.startswith(EXEMPT_PREFIXES)


def _has_spec(project_root: Path) -> bool:
    specs_dir = Path(project_root) / "docs" / "specs"
    if not specs_dir.is_dir():
        return False
    return any(p.name != "INDEX.md" for p in specs_dir.glob("*.md"))


def _has_stories(project_root: Path) -> bool:
    rows = read_rows(Path(project_root) / "docs" / "tracking" / "STORIES.csv")
    return len(rows) > 0


def _override_active(project_root: Path) -> bool:
    return (Path(project_root) / ".claude" / "harness-override").exists()


def _awaiting_review(project_root: Path) -> bool:
    return (Path(project_root) / "docs" / "plans" / "AWAITING_REVIEW.md").exists()


def check_gate(tool_name: str, file_path: str, project_root) -> str | None:
    """Return a block reason string, or None if the edit is allowed."""
    if tool_name not in GATED_TOOLS:
        return None

    project_root = Path(project_root)
    rel_path = _relative_to_root(file_path, project_root)

    if _is_exempt(rel_path):
        return None

    if _override_active(project_root):
        return None

    if not _has_spec(project_root) or not _has_stories(project_root):
        return (
            "Blocked: no spec found in docs/specs/ and/or docs/tracking/STORIES.csv "
            "has no stories yet. Run the roles/user-stories and spec phases "
            "(superpowers:brainstorming) before editing source files."
        )

    if _awaiting_review(project_root):
        return (
            "Blocked: docs/plans/AWAITING_REVIEW.md exists. The current phase is "
            "awaiting human review. Wait for approval before starting next-phase work."
        )

    return None
