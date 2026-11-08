#!/usr/bin/env python3
"""Double each integer in file1.txt while processing one line at a time."""

from pathlib import Path
from time import perf_counter


def double_numbers(input_path: Path, output_path: Path) -> tuple[int, float]:
    """Stream integers from input_path to output_path and return count and seconds."""
    line_count = 0
    start = perf_counter()

    # Iterating over the input file reads one line at a time; the files' I/O
    # buffers improve disk efficiency without loading the complete dataset.
    with input_path.open("r", encoding="ascii", buffering=1024 * 1024) as source:
        with output_path.open("w", encoding="ascii", buffering=1024 * 1024) as destination:
            for line in source:
                number = int(line)
                destination.write(f"{number * 2}\n")
                line_count += 1

    elapsed = perf_counter() - start
    return line_count, elapsed


def main() -> None:
    folder = Path(__file__).resolve().parent
    input_path = folder / "file1.txt"
    output_path = folder / "newfile1.txt"

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file was not found: {input_path}")

    line_count, elapsed = double_numbers(input_path, output_path)
    print(f"Method: one line at a time")
    print(f"Input: {input_path.name}")
    print(f"Output: {output_path.name}")
    print(f"Lines processed: {line_count:,}")
    print(f"Elapsed time: {elapsed:.3f} seconds")


if __name__ == "__main__":
    main()
