from pathlib import Path
import sys
import os
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.file_lock import FileLock


def test_lock_creates_and_removes_lockdir(tmp_path):
    lock_path = tmp_path / "tracking.lock"

    with FileLock(lock_path):
        assert lock_path.exists()

    assert not lock_path.exists()


def test_lock_raises_timeout_if_already_held(tmp_path):
    lock_path = tmp_path / "tracking.lock"
    os.mkdir(lock_path)

    with pytest.raises(TimeoutError):
        with FileLock(lock_path, timeout=0.2, retry_interval=0.05):
            pass
