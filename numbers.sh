#!/usr/bin/env bash

set -euo pipefail

SECONDS=0
printf 'Start time: '
date '+%Y-%m-%d %H:%M:%S %Z'

for ((i = 1; i <= 1000000; i++)); do
    printf '%s\n' "$RANDOM"
done > file1.txt

printf 'End time:   '
date '+%Y-%m-%d %H:%M:%S %Z'
printf 'Elapsed: %02d:%02d:%02d (HH:MM:SS)\n' \
    "$((SECONDS / 3600))" "$(((SECONDS / 60) % 60))" "$((SECONDS % 60))"
