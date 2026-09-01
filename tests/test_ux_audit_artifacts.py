"""Release guards for checked-in UX evidence."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCREENSHOTS = ROOT / "docs/screenshots/ux-audit-2026-08-29"


def test_ux_audit_screenshot_extensions_match_jpeg_payloads() -> None:
    screenshots = sorted(AUDIT_SCREENSHOTS.iterdir())

    assert len(screenshots) == 25
    assert all(path.suffix == ".jpg" for path in screenshots)
    assert all(path.read_bytes().startswith(b"\xff\xd8\xff") for path in screenshots)
