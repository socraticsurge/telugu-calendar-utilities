from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.paths import find_project_root


def test_find_project_root_from_nested_dir(tmp_path):
    (tmp_path / ".claude").mkdir()
    nested = tmp_path / "docs" / "tracking"
    nested.mkdir(parents=True)

    result = find_project_root(nested)

    assert result == tmp_path


def test_find_project_root_raises_when_not_found(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        find_project_root(tmp_path)
