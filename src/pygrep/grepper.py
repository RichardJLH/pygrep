import os
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from mmap import ACCESS_READ, ALLOCATIONGRANULARITY, mmap
from pathlib import Path
from typing import Iterator, Optional


@dataclass(frozen=True, slots=True)
class View:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


def get_views(size: int, chunk_size: int, overlap: int) -> Iterator[View]:
    """Yields View with with start and end with an overlap"""

    offsets = range(0, size, chunk_size)
    spans = (View(start=offset, end=min(offset + chunk_size + overlap, size)) for offset in offsets)

    return spans


def search_chunk(filepath: Path, pattern: re.Pattern[bytes], view: View) -> Optional[int]:
    """Searches a chunk for a regex pattern and returns the global file offset."""

    with open(filepath, "rb") as file:
        with mmap(
            fileno=file.fileno(), length=view.length, offset=view.start, access=ACCESS_READ
        ) as memory:
            match = pattern.search(memory)
            return view.start + match.start() if match is not None else None


type ByteCount = int


@dataclass(frozen=True, slots=True)
class GrepOptions:
    chunk_size: ByteCount = 2560 * ALLOCATIONGRANULARITY
    max_match_length: ByteCount = 4096

    def __post_init__(self) -> None:
        if self.chunk_size < 1 or self.max_match_length < 1:
            raise ValueError("max_match_length and chunk_size must be positive integers")

        if self.chunk_size % ALLOCATIONGRANULARITY != 0:
            raise ValueError(
                f"chunk_size ({self.chunk_size}) must be a multiple of "
                f"mmap.ALLOCATION_GRANULARITY ({ALLOCATIONGRANULARITY})"
            )

        if self.max_match_length >= self.chunk_size:
            raise ValueError("max_match_length must be smaller than chunk_size")


DEFAULT_GREP_OPTIONS = GrepOptions()


def grep(
    filepath: Path, pattern: re.Pattern[bytes], options: GrepOptions = DEFAULT_GREP_OPTIONS
) -> list[int]:
    """Parallelized regex search across a large file."""

    search_in_file = partial(search_chunk, filepath, pattern)

    views = get_views(
        size=os.path.getsize(filepath),
        chunk_size=options.chunk_size,
        overlap=options.max_match_length,
    )

    with ProcessPoolExecutor() as executor:
        results = executor.map(search_in_file, views)

    offsets = {result for result in results if result is not None}
    return sorted(offsets)
