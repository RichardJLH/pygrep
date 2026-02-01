import mmap
import re
from typing import Any

from pygrep.grepper import GrepOptions, grep


def test_basic_search(tmp_path: Any) -> None:
    """Verify that we can find a simple string as expected."""

    filepath = tmp_path / "system.txt"
    filepath.write_bytes(b"INFO: Starting session\nERROR: Kernel panic\nDEBUG: End")

    assert [30] == grep(filepath, re.compile("Kernel panic".encode()))


def test_boundary_split(tmp_path: Any) -> None:
    """Force a pattern to split across two chunks to test overlap logic."""

    filepath = tmp_path / "split.txt"

    prefix = b" " * (mmap.ALLOCATIONGRANULARITY - 1)
    pattern = b"test"
    filepath.write_bytes(prefix + pattern)

    expected = [len(prefix)]
    actual = grep(
        filepath,
        re.compile(pattern),
        GrepOptions(chunk_size=mmap.ALLOCATIONGRANULARITY, max_match_length=len(pattern)),
    )

    assert expected == actual
