from time import perf_counter_ns


class MemoryBlock:
    """Represents a dynamic block of contiguous memory."""
    def __init__(self, block_id, size):
        self.block_id = block_id
        self.size = size
        self.allocated_to = None  # None denotes unallocated (free) block

    def __repr__(self):
        status = f"Allocated to {self.allocated_to}" if self.allocated_to else "Free"
        return f"[Block {self.block_id} | Size: {self.size} KB | Status: {status}]"


def simulate_allocation(blocks, processes, strategy):
    """Allocate processes using first-fit, next-fit, best-fit, or worst-fit."""
    if strategy not in {"first", "next", "best", "worst"}:
        raise ValueError(f"Unknown allocation strategy: {strategy}")

    results = []
    next_fit_start = 0
    for proc_name, proc_size in processes.items():
        if strategy == "next":
            search_order = [
                (next_fit_start + offset) % len(blocks)
                for offset in range(len(blocks))
            ]
        else:
            search_order = range(len(blocks))

        candidates = [
            index
            for index in search_order
            if blocks[index].allocated_to is None and blocks[index].size >= proc_size
        ]

        if not candidates:
            results.append((proc_name, proc_size, None))
            continue

        if strategy in {"first", "next"}:
            index = candidates[0]
        elif strategy == "best":
            index = min(candidates, key=lambda i: blocks[i].size)
        else:
            index = max(candidates, key=lambda i: blocks[i].size)

        block = blocks[index]
        original_size = block.size
        block.allocated_to = proc_name
        block.size = proc_size
        results.append((proc_name, proc_size, block.block_id))

        remaining_size = original_size - proc_size
        if remaining_size > 0:
            new_id = max(item.block_id for item in blocks) + 1
            blocks.insert(index + 1, MemoryBlock(new_id, remaining_size))

        if strategy == "next":
            # Begin the next search immediately after this allocation.
            next_fit_start = (index + 1) % len(blocks)

    return results


def display_simulation(label, blocks, results):
    print("==================================================")
    print(f" {label.upper()} MEMORY ALLOCATION SIMULATION")
    print("==================================================\n")

    for proc_name, proc_size, block_id in results:
        if block_id is None:
            print(
                f"Request: {proc_name} ({proc_size} KB) -> "
                "FAILED: Insufficient contiguous space\n"
            )
        else:
            print(
                f"Request: {proc_name} ({proc_size} KB) -> "
                f"SUCCESS: Allocated to Block {block_id}\n"
            )

    print("--------------------------------------------------")
    print(" FINAL MEMORY ALLOCATION STATE")
    print("--------------------------------------------------")
    for block in sorted(blocks, key=lambda item: item.block_id):
        print(block)
    print()


def first_fit_allocation(blocks, processes):
    """Backward-compatible First-Fit simulation entry point."""
    results = simulate_allocation(blocks, processes, "first")
    display_simulation("First-Fit", blocks, results)


def create_initial_blocks():
    return [
        MemoryBlock(1, 100),
        MemoryBlock(2, 500),
        MemoryBlock(3, 200),
        MemoryBlock(4, 300),
        MemoryBlock(5, 600),
    ]


def benchmark_algorithms(processes, iterations=10_000):
    """Print average runtime per simulation; timings depend on the machine."""
    strategies = (
        ("First-Fit", "first"),
        ("Next-Fit", "next"),
        ("Best-Fit", "best"),
        ("Worst-Fit", "worst"),
    )

    print("==================================================")
    print(f" BENCHMARK ({iterations:,} SIMULATIONS PER ALGORITHM)")
    print("==================================================")
    print(f"{'Algorithm':<12} {'Average time (µs/run)':>24}")

    for label, strategy in strategies:
        # Warm up once before measuring each strategy.
        simulate_allocation(create_initial_blocks(), processes, strategy)

        start = perf_counter_ns()
        for _ in range(iterations):
            simulate_allocation(create_initial_blocks(), processes, strategy)
        elapsed_ns = perf_counter_ns() - start
        average_us = elapsed_ns / iterations / 1_000
        print(f"{label:<12} {average_us:>24.2f}")


if __name__ == "__main__":
    # Process allocation requests in sequential arrival order
    process_requests = {
        "Process_1": 210,
        "Process_2": 410,
        "Process_3": 110,
        "Process_4": 420,
    }

    algorithms = (
        ("First-Fit", "first"),
        ("Next-Fit", "next"),
        ("Best-Fit", "best"),
        ("Worst-Fit", "worst"),
    )

    for label, strategy in algorithms:
        blocks = create_initial_blocks()
        results = simulate_allocation(blocks, process_requests, strategy)
        display_simulation(label, blocks, results)

    benchmark_algorithms(process_requests)