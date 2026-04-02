#!/bin/bash
# Pre-commit hook: block commits without a message
# Exit code 2 = block. Exit code 0 = allow.

COMMIT_MSG_FILE="$1"

if [ -z "$COMMIT_MSG_FILE" ] || [ ! -f "$COMMIT_MSG_FILE" ]; then
  exit 0  # Not a commit context, allow
fi

MSG=$(cat "$COMMIT_MSG_FILE" | grep -v "^#" | tr -d '[:space:]')

if [ -z "$MSG" ]; then
  echo "ERROR: Commit message cannot be empty. Every session gets logged."
  exit 2
fi

echo "Commit message OK."
exit 0
