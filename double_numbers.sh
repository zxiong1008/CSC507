#!/usr/bin/env bash

# Double each integer one line at a time using AWK, a standard Linux text tool.
# The Bash wrapper measures the complete transform and reports a high-resolution time.
set -euo pipefail

input_file="${1:-file1.txt}"
output_file="${2:-newfile1_bash.txt}"

if [[ ! -f "$input_file" ]]; then
    printf 'Error: input file not found: %s\n' "$input_file" >&2
    exit 1
fi
if [[ "$(realpath -- "$input_file")" == "$(realpath -m -- "$output_file")" ]]; then
    printf 'Error: input and output files must be different.\n' >&2
    exit 1
fi
if ! command -v awk >/dev/null 2>&1 || ! command -v date >/dev/null 2>&1; then
    printf 'Error: this script requires awk and date.\n' >&2
    exit 1
fi

start_ns=$(date +%s%N)
line_count=$(awk '
    !/^[0-9]+$/ { printf "Invalid integer at line %d\n", NR > "/dev/stderr"; exit 1 }
    { printf "%.0f\n", $1 * 2 }
    END { print NR > "/dev/stderr" }
' "$input_file" 2>&1 > "$output_file")
end_ns=$(date +%s%N)
elapsed_ns=$((end_ns - start_ns))

printf 'Method: Bash script using AWK (one input line at a time)\n'
printf 'Input: %s\n' "$input_file"
printf 'Output: %s\n' "$output_file"
printf 'Lines processed: %s\n' "$line_count"
printf 'Elapsed time: %d.%03d seconds\n' "$((elapsed_ns / 1000000000))" "$(((elapsed_ns % 1000000000) / 1000000))"
