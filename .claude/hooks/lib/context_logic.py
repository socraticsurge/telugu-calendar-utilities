from pathlib import Path


def build_context(project_root) -> str:
    """Build a SessionStart additionalContext string from HANDOFF.md, NOW.md,
    and the most recent SESSION_LOG.md entry. Returns "" if nothing exists."""
    project_root = Path(project_root)
    parts = []

    handoff = project_root / "docs" / "plans" / "HANDOFF.md"
    if handoff.exists() and handoff.read_text().strip():
        parts.append("## Handoff (from last checkpoint)\n" + handoff.read_text().strip())

    now = project_root / "docs" / "NOW.md"
    if now.exists() and now.read_text().strip():
        parts.append(now.read_text().strip())

    log = project_root / "docs" / "tracking" / "SESSION_LOG.md"
    if log.exists():
        text = log.read_text()
        sections = text.split("\n## ")
        entries = [s for s in sections if s.strip() and not s.startswith("Session Log")]
        if entries:
            last = entries[-1]
            if not last.startswith("#"):
                last = "## " + last
            parts.append("## Most recent session log entry\n" + last.strip())

    return "\n\n".join(parts)
