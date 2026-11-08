#!/usr/bin/env python3
"""Compare three Python methods for doubling integers in a text file."""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path
from time import perf_counter
from typing import Callable


def double_all_in_memory(input_path: Path, output_path: Path) -> int:
    """Read and transform the entire file in memory."""
    contents = input_path.read_text(encoding="ascii")
    numbers = contents.splitlines()
    doubled = [str(int(number) * 2) for number in numbers]
    with output_path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
        if doubled:
            output.write("\n".join(doubled))
            output.write("\n")
    return len(doubled)


def double_one_line_at_a_time(input_path: Path, output_path: Path) -> int:
    """Stream the file, retaining only the current line in program data."""
    count = 0
    with input_path.open("r", encoding="ascii", buffering=1024 * 1024) as source:
        with output_path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
            for line in source:
                output.write(f"{int(line) * 2}\n")
                count += 1
    return count


def double_two_parts_in_memory(input_path: Path, output_path: Path) -> int:
    """Read each half of the file into memory separately and process it."""
    file_size = input_path.stat().st_size
    midpoint = file_size // 2
    count = 0

    with input_path.open("rb") as source:
        # Move the split point to a line boundary. The first chunk includes
        # the line containing the midpoint if the midpoint is inside a line.
        source.seek(midpoint)
        source.readline()
        split_at = source.tell()

        with output_path.open("w", encoding="ascii", buffering=1024 * 1024) as output:
            for start, end in ((0, split_at), (split_at, file_size)):
                source.seek(start)
                part = source.read(end - start)
                for number in part.splitlines():
                    output.write(f"{int(number) * 2}\n")
                    count += 1

    return count


def validate_output(input_path: Path, output_path: Path) -> int:
    """Check every output row against its corresponding input row."""
    checked = 0
    with input_path.open("r", encoding="ascii") as source:
        with output_path.open("r", encoding="ascii") as output:
            while True:
                input_line = source.readline()
                output_line = output.readline()
                if not input_line and not output_line:
                    return checked
                if not input_line or not output_line:
                    raise ValueError("Input and output have different row counts")
                if int(output_line) != int(input_line) * 2:
                    raise ValueError(f"Incorrect doubled value at row {checked + 1}")
                checked += 1


def run_benchmark(input_path: Path, output_path: Path, repeats: int) -> None:
    methods: tuple[tuple[str, Callable[[Path, Path], int]], ...] = (
        ("Entire file in memory", double_all_in_memory),
        ("One line at a time", double_one_line_at_a_time),
        ("Two parts in memory", double_two_parts_in_memory),
    )

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Input size: {input_path.stat().st_size:,} bytes")
    print(f"Runs per method: {repeats}")
    print("\nMethod timings (median of runs; validation excluded):")
    print(f"{'Method':<25} {'Median seconds':>16} {'Rows verified':>16}")

    for label, method in methods:
        timings: list[float] = []
        row_count = 0
        for _ in range(repeats):
            start = perf_counter()
            row_count = method(input_path, output_path)
            timings.append(perf_counter() - start)

            verified = validate_output(input_path, output_path)
            if verified != row_count:
                raise ValueError(
                    f"{label} wrote {row_count:,} rows but verified {verified:,}"
                )

        print(f"{label:<25} {statistics.median(timings):>16.3f} {verified:>16,}")

    print("\nAll three methods produced the same correct output.")
    print("Timings include reading, doubling, and writing; validation is excluded.")
    print("The final newfile1.txt contains the result from the last method tested.")


def main() -> None:
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=folder / "file1.txt")
    parser.add_argument("--output", type=Path, default=folder / "newfile1.txt")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if not args.input.is_file():
        parser.error(f"input file not found: {args.input}")
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output paths must be different")

    run_benchmark(args.input, args.output, args.repeats)


if __name__ == "__main__":
    main()
