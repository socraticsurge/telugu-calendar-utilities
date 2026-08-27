"""Packaging guardrails for the MCP server dependency contract."""

from pathlib import Path

from packaging.requirements import Requirement

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _requirement(name: str) -> Requirement:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        dependencies = tomllib.load(handle)["project"]["dependencies"]

    matches = [Requirement(item) for item in dependencies if Requirement(item).name == name]
    assert len(matches) == 1, f"pyproject.toml must declare exactly one {name} dependency"
    return matches[0]


def test_mcp_dependency_accepts_the_supported_1_x_api():
    assert _requirement("mcp").specifier.contains("1.28.1")


def test_mcp_dependency_excludes_the_unverified_2_x_api():
    assert not _requirement("mcp").specifier.contains("2.0.0")


def test_icalendar_dependency_preserves_the_frozen_feed_serializer():
    requirement = _requirement("icalendar")

    assert requirement.specifier.contains("7.2.2")
    assert not requirement.specifier.contains("7.3.0")
