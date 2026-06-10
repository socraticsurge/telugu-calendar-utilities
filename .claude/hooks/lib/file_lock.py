import os
import time
from pathlib import Path


class FileLock:
    """A simple cross-process lock using an atomic mkdir.

    Used by sync_tracker_on_task.py so concurrent subagent TaskUpdate
    completions don't corrupt TASKS.csv/STORIES.csv.
    """

    def __init__(self, path, timeout: float = 5.0, retry_interval: float = 0.05):
        self.path = Path(path)
        self.timeout = timeout
        self.retry_interval = retry_interval

    def __enter__(self):
        start = time.monotonic()
        while True:
            try:
                os.mkdir(self.path)
                return self
            except FileExistsError:
                if time.monotonic() - start > self.timeout:
                    raise TimeoutError(f"Could not acquire lock at {self.path}")
                time.sleep(self.retry_interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.rmdir(self.path)
