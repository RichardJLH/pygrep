import os
import re
from concurrent.futures import ProcessPoolExecutor
from mmap import ACCESS_READ, ALLOCATIONGRANULARITY, mmap
from typing import Iterator, List, Optional


def get_spans(file_size: int, chunk_size: int, overlap: int) -> Iterator[tuple[int, int]]:
    """Yields (start, end) tuples aligned with mmap granularity."""

    offset = 0
    while offset < file_size:
        end = min(offset + chunk_size + overlap, file_size)
        yield offset, end

        offset += chunk_size


def search_chunk(file_path: str, pattern: re.Pattern[bytes], start: int, end: int) -> Optional[int]:
    """Searches a chunk for a regex pattern and returns the global file offset."""

    with open(file_path, "rb") as file:
        with mmap(file.fileno(), length=end - start, offset=start, access=ACCESS_READ) as memory:
            match = pattern.search(memory)
            if match:
                return start + match.start()
    return None


DEFAULT_ALLOCATIONS_PER_CHUNK = 2560
ALLOCATION_SIZE = ALLOCATIONGRANULARITY


def run_grep(
    file_path: str, query: str, allocations_per_chunk: int = DEFAULT_ALLOCATIONS_PER_CHUNK
) -> List[int]:
    """Parallelized regex search across a large file."""

    pattern = re.compile(query.encode())
    size = os.path.getsize(file_path)

    overlap = len(query.encode()) - 1
    chunk_size = allocations_per_chunk * ALLOCATION_SIZE

    results = []
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(search_chunk, file_path, pattern, s, e)
            for s, e in get_spans(size, chunk_size, overlap)
        ]

        for future in futures:
            res = future.result()
            if res is not None:
                results.append(res)

    return sorted(results)
