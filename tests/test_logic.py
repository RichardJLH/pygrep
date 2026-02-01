from typing import Any

from pygrep.grepper import run_grep


def test_basic_search(tmp_path: Any) -> None:
    """Verify that we can find a simple string using mmap."""

    log_file = tmp_path / "system.log"
    log_file.write_bytes(b"INFO: Starting session\nERROR: Kernel panic\nDEBUG: End")

    results = run_grep(str(log_file), "Kernel panic")

    assert len(results) == 1
    assert results[0] == 30
