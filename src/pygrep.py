import mmap
import os
import re
from concurrent.futures import ProcessPoolExecutor
from typing import Iterator, List, Optional


def get_spans(file_size: int, chunk_size: int) -> Iterator[tuple[int, int]]:
    """Yields (start, end) tuples aligned with mmap granularity."""
    offset = 0
    while offset < file_size:
        end = min(offset + chunk_size, file_size)
        yield offset, end
        offset = end


def search_chunk(file_path: str, pattern: re.Pattern[bytes], start: int, end: int) -> Optional[int]:
    """Searches a chunk for a regex pattern and returns the global file offset."""
    with open(file_path, "rb") as file:
        with mmap.mmap(
            file.fileno(), length=end - start, offset=start, access=mmap.ACCESS_READ
        ) as memory:
            match = pattern.search(memory)
            if match:
                return start + match.start()
    return None


def run_grep(file_path: str, query: str) -> List[int]:
    """Parallelized regex search across a large file."""
    pattern: re.Pattern[bytes] = re.compile(query.encode())
    size: int = os.path.getsize(file_path)
    chunk_size: int = 1024 * 1024 * 10

    results: List[int] = []
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(search_chunk, file_path, pattern, s, e)
            for s, e in get_spans(size, chunk_size)
        ]

        for future in futures:
            res = future.result()
            if res is not None:
                results.append(res)

    return sorted(results)
