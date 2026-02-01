from typing import Any

from pygrep import grepper
from pygrep.grepper import run_grep


def test_basic_search(tmp_path: Any) -> None:
    """Verify that we can find a simple string as expected."""

    filepath = tmp_path / "system.txt"
    filepath.write_bytes(b"INFO: Starting session\nERROR: Kernel panic\nDEBUG: End")

    assert [30] == run_grep(str(filepath), "Kernel panic")


def test_boundary_split(tmp_path: Any) -> None:
    """Force a pattern to split across two chunks to test overlap logic."""

    filepath = tmp_path / "split.txt"

    prefix = b" " * (grepper.ALLOCATION_SIZE - 1)
    pattern = "test"
    filepath.write_bytes(prefix + pattern.encode())

    assert [len(prefix)] == run_grep(str(filepath), pattern, allocations_per_chunk=1)
