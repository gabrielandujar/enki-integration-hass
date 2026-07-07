#!/usr/bin/env bash
# Backward-compatible alias — use scripts/sync_github_labels.sh instead.
exec "$(dirname "${BASH_SOURCE[0]}")/sync_github_labels.sh" "$@"
