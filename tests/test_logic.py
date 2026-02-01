import mmap
import re
from pathlib import Path

from pygrep.grepper import GrepOptions, grep


def test_basic_search(tmp_path: Path) -> None:
    """Verify that we can find a simple string as expected."""

    filepath = tmp_path / "system.txt"
    filepath.write_bytes(b"INFO: Starting session\nERROR: Kernel panic\nDEBUG: End")

    assert [30] == grep(filepath, re.compile("Kernel panic".encode()))


def test_boundary_split(tmp_path: Path) -> None:
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


def test_multiple_matches_and_overlap(tmp_path: Path):
    """Tests that multiple matches in one chunk are all found."""

    filepath = tmp_path / "multiple_matches.txt"

    content = bytearray(b"." * 200)

    content[0:6] = b"needle"
    content[100:106] = b"needle"
    content[110:116] = b"needle"

    filepath.write_bytes(content)

    assert [0, 100, 110] == grep(
        filepath, pattern=re.compile(b"needle"), options=GrepOptions(max_match_length=16)
    )
