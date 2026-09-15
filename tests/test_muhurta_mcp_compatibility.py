"""Byte-level snapshots from e05eb3b: a compatibility guard, not an accuracy oracle."""

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from telugu_panchangam.mcp.tools import tool_find_muhurta

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "muhurta-mcp-compatibility.json").read_text()
)


def test_find_muhurta_signature_stays_compatible():
    assert str(inspect.signature(tool_find_muhurta)) == FIXTURE["signature"]


@pytest.mark.parametrize("case", FIXTURE["cases"])
def test_find_muhurta_bytes_stay_compatible(case):
    actual = tool_find_muhurta(**case["request"])
    assert hashlib.sha256(actual.encode()).hexdigest() == case["sha256"]
