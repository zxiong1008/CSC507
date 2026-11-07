#!/usr/bin/env python3
"""Compare sequential, batched, threaded, and process-based number generation."""

from __future__ import annotations

import csv
import os
import random
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

COUNT = 1_000_000
MAX_RANDOM = 32_767
WORKERS = min(4, os.cpu_count() or 1)


def make_chunk(args: tuple[int, int]) -> str:
    """Generate one independently-seeded chunk; suitable for process pools."""
    count, seed = args
    rng = random.Random(seed)
    return "".join(f"{rng.randrange(MAX_RANDOM + 1)}\n" for _ in range(count))


def write_sequential(path: Path) -> None:
    rng = random.Random()
    with path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
        for _ in range(COUNT):
            output.write(f"{rng.randrange(MAX_RANDOM + 1)}\n")


def write_batched(path: Path) -> None:
    rng = random.Random()
    lines = [f"{rng.randrange(MAX_RANDOM + 1)}\n" for _ in range(COUNT)]
    with path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
        output.writelines(lines)


def write_threaded(path: Path) -> None:
    chunk_size = (COUNT + WORKERS - 1) // WORKERS
    jobs = [
        (min(chunk_size, COUNT - index * chunk_size), random.getrandbits(64))
        for index in range(WORKERS)
    ]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        chunks = list(pool.map(make_chunk, jobs))
    with path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
        output.writelines(chunks)


def write_multiprocess(path: Path) -> None:
    chunk_size = (COUNT + WORKERS - 1) // WORKERS
    jobs = [
        (min(chunk_size, COUNT - index * chunk_size), random.getrandbits(64))
        for index in range(WORKERS)
    ]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        chunks = list(pool.map(make_chunk, jobs))
    with path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
        output.writelines(chunks)


def count_lines(path: Path) -> int:
    with path.open("rb") as source:
        return sum(block.count(b"\n") for block in iter(lambda: source.read(1024 * 1024), b""))


def main() -> None:
    methods: list[tuple[str, Callable[[Path], None]]] = [
        ("sequential buffered writes", write_sequential),
        ("batched writelines", write_batched),
        ("thread pool", write_threaded),
        ("process pool", write_multiprocess),
    ]
    results: list[tuple[str, float, str]] = []

    with tempfile.TemporaryDirectory(prefix="number-bench-") as temporary:
        temp_dir = Path(temporary)
        for index, (name, method) in enumerate(methods):
            output_path = temp_dir / f"method-{index}.txt"
            start = time.perf_counter()
            method(output_path)
            elapsed = time.perf_counter() - start
            lines = count_lines(output_path)
            if lines != COUNT:
                raise RuntimeError(f"{name} produced {lines:,} lines, expected {COUNT:,}")
            results.append((name, elapsed, str(output_path)))
            print(f"{name}: {elapsed:.3f} seconds ({lines:,} lines)", flush=True)

        best = min(results, key=lambda result: result[1])
        shutil.copyfile(best[2], Path("file2.txt"))

    with Path("benchmark_results.csv").open("w", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)
        writer.writerow(("method", "elapsed_seconds", "line_count"))
        writer.writerows((name, f"{elapsed:.6f}", COUNT) for name, elapsed, _ in results)

    print(f"Fastest method: {best[0]} ({best[1]:.3f} seconds)")
    print(f"Saved its output to file2.txt ({count_lines(Path('file2.txt')):,} lines).")
    print(f"Worker count for concurrent methods: {WORKERS}")
    print("Detailed timings: benchmark_results.csv")


if __name__ == "__main__":
    main()
