#!/usr/bin/env bash

# Upload the milestone programs and input data to the existing Linux home directory.
# Run this on the Windows host through Git Bash or WSL while the SSH tunnel
# to localhost:2224 is active.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_USER="${REMOTE_USER:-student}"
REMOTE_HOST="${REMOTE_HOST:-127.0.0.1}"
REMOTE_PORT="${REMOTE_PORT:-2224}"
REMOTE_DIR="${REMOTE_DIR:-~}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/k8s-debian-mini}"

FILES=(
    "$SCRIPT_DIR/file1.txt"
    "$SCRIPT_DIR/double_numbers_stream.py"
    "$SCRIPT_DIR/double_numbers_benchmark.py"
    "$SCRIPT_DIR/double_numbers.sh"
)

if ! command -v ssh >/dev/null 2>&1 || ! command -v scp >/dev/null 2>&1; then
    echo "Error: ssh and scp are required (install/use OpenSSH in Git Bash or WSL)." >&2
    exit 1
fi

if [[ ! -f "$SSH_KEY" ]]; then
    echo "Error: SSH private key not found: $SSH_KEY" >&2
    echo "Set SSH_KEY to the key path visible from this Bash environment." >&2
    exit 1
fi

for file in "${FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "Error: required upload file not found: $file" >&2
        exit 1
    fi
done

SCP_OPTIONS=(-i "$SSH_KEY" -P "$REMOTE_PORT" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
REMOTE="$REMOTE_USER@$REMOTE_HOST"

# Do not create a destination directory; copy directly to the existing home/root.
scp "${SCP_OPTIONS[@]}" "${FILES[@]}" "$REMOTE:$REMOTE_DIR/"

printf 'Uploaded to %s:%s\n' "$REMOTE" "$REMOTE_DIR"
printf 'Files uploaded:\n'
printf '  %s\n' "${FILES[@]}"
