import multiprocessing as mp
import csv
import os
import random
import statistics
import time

INPUT_FILE = "input_10m.txt"
NUM_ROWS = 10_000_000


def generate_sample_file(filename: str, rows: int) -> None:
    """Generates a 10-million-row sample dataset if it does not exist."""
    if os.path.exists(filename):
        return
    print(f"Generating {rows:,} rows...")
    chunk = "\n".join(f"record_{i},value_{i % 1000}" for i in range(100_000)) + "\n"
    with open(filename, "w", encoding="utf-8") as f:
        for _ in range(rows // 100_000):
            f.write(chunk)


def transform_line(line: str) -> str:
    """Simulated CPU + string processing workload."""
    parts = line.strip().split(",")
    if len(parts) == 2:
        val = int(parts[1].split("_")[1]) * 2
        return f"{parts[0].upper()},{val}\n"
    return ""


def process_file_worker(args: tuple[str, str]) -> None:
    """Processes an individual split file."""
    in_path, out_path = args
    with (
        open(in_path, "r", encoding="utf-8") as fin,
        open(out_path, "w", encoding="utf-8") as fout,
    ):
        fout.writelines(transform_line(line) for line in fin)


def validate_output(input_path: str, output_path: str) -> int:
    """Verify every output row against its corresponding input row."""
    count = 0
    with (
        open(input_path, "r", encoding="utf-8") as source,
        open(output_path, "r", encoding="utf-8") as output,
    ):
        for input_line, output_line in zip(source, output):
            expected = transform_line(input_line)
            if output_line != expected:
                raise ValueError(f"Incorrect output at row {count + 1}")
            count += 1

        if next(source, None) is not None or next(output, None) is not None:
            raise ValueError("Input and output have different row counts")
    if count != NUM_ROWS:
        raise ValueError(f"Expected {NUM_ROWS:,} rows, found {count:,}")
    return count


def run_split_method(num_splits: int) -> tuple[float, int]:
    """Implements Methods 1-5: Split -> Parallel Process -> Merge."""
    start_time = time.perf_counter()
    output_final = f"output_{num_splits}_splits.txt"

    if num_splits == 1:
        process_file_worker((INPUT_FILE, output_final))
        elapsed = time.perf_counter() - start_time
        count = validate_output(INPUT_FILE, output_final)
        os.remove(output_final)
        return elapsed, count

    # 1. Split phase
    split_files = [f"temp_in_{i}.txt" for i in range(num_splits)]
    out_files = [f"temp_out_{i}.txt" for i in range(num_splits)]
    rows_per_split = (NUM_ROWS + num_splits - 1) // num_splits

    with open(INPUT_FILE, "r", encoding="utf-8") as fin:
        for i, split_file in enumerate(split_files):
            with open(split_file, "w", encoding="utf-8") as fout:
                for _ in range(min(rows_per_split, NUM_ROWS - i * rows_per_split)):
                    line = fin.readline()
                    if not line:
                        break
                    fout.write(line)

    # 2. Parallel execution phase
    with mp.Pool(processes=num_splits) as pool:
        pool.map(process_file_worker, zip(split_files, out_files))

    # 3. Combine phase
    with open(output_final, "w", encoding="utf-8") as fout:
        for out_f in out_files:
            with open(out_f, "r", encoding="utf-8") as fin:
                fout.write(fin.read())

    elapsed = time.perf_counter() - start_time
    count = validate_output(INPUT_FILE, output_final)

    # Cleanup
    for f in split_files + out_files + [output_final]:
        if os.path.exists(f):
            os.remove(f)

    return elapsed, count


def byte_offset_worker(args: tuple[str, int, int, str]) -> None:
    """Optimized Strategy: Reads specific byte offsets without splitting input."""
    filepath, start_byte, end_byte, out_path = args
    with (
        open(filepath, "rb") as fin,
        open(out_path, "w", encoding="utf-8") as fout,
    ):
        fin.seek(start_byte)
        if start_byte != 0:
            fin.seek(start_byte - 1)
            if fin.read(1) != b"\n":
                fin.readline()
            else:
                fin.seek(start_byte)
        while fin.tell() < end_byte:
            line = fin.readline()
            if not line:
                break
            fout.write(transform_line(line.decode("utf-8")))


def run_optimized_offset_method(num_workers: int) -> tuple[float, int]:
    """Zero-split parallel processing using byte offsets."""
    start_time = time.perf_counter()
    file_size = os.path.getsize(INPUT_FILE)
    chunk_size = file_size // num_workers

    tasks = []
    out_files = []
    for i in range(num_workers):
        s_byte = i * chunk_size
        e_byte = file_size if i == num_workers - 1 else (i + 1) * chunk_size
        out_f = f"temp_opt_{i}.txt"
        out_files.append(out_f)
        tasks.append((INPUT_FILE, s_byte, e_byte, out_f))

    with mp.Pool(processes=num_workers) as pool:
        pool.map(byte_offset_worker, tasks)

    output_final = "output_optimized.txt"
    with open(output_final, "w", encoding="utf-8") as fout:
        for out_f in out_files:
            with open(out_f, "r", encoding="utf-8") as fin:
                fout.write(fin.read())

    elapsed = time.perf_counter() - start_time
    count = validate_output(INPUT_FILE, output_final)

    for f in out_files + [output_final]:
        if os.path.exists(f):
            os.remove(f)

    return elapsed, count


if __name__ == "__main__":
    generate_sample_file(INPUT_FILE, NUM_ROWS)
    opt_workers = os.cpu_count() or 1
    print(f"Logical CPU count: {opt_workers}")
    print("Timing includes partitioning, processing, and merging; validation is excluded.")
    with open(INPUT_FILE, "rb") as source:
        while source.read(4 * 1024 * 1024):
            pass
    print("Input warmed in the file cache; running three randomized rounds.")

    methods = [
        (f"{splits} file(s)", lambda splits=splits: run_split_method(splits))
        for splits in [1, 2, 5, 10, 20]
    ]
    methods.append(
        (f"Byte offsets ({opt_workers} workers)", lambda: run_optimized_offset_method(opt_workers))
    )
    results = []
    for repeat in range(1, 4):
        round_methods = methods.copy()
        random.Random(repeat).shuffle(round_methods)
        for name, run_method in round_methods:
            duration, verified = run_method()
            results.append((name, repeat, duration, verified))
            print(f"Round {repeat}: {name}: {duration:.2f} seconds ({verified:,} rows verified)")

    summaries = {}
    for name, _, duration, _ in results:
        summaries.setdefault(name, []).append(duration)
    print("\nMedian elapsed time by method:")
    for name, timings in sorted(summaries.items(), key=lambda item: statistics.median(item[1])):
        print(f"{name}: {statistics.median(timings):.2f} seconds")

    with open("CSC507_M06_CT_results.csv", "w", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)
        writer.writerow(("method", "round", "elapsed_seconds", "rows_verified"))
        writer.writerows(
            (name, repeat, f"{duration:.6f}", verified)
            for name, repeat, duration, verified in results
        )