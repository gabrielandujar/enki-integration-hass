#!/usr/bin/env bash
# Create or update GitHub labels used by Enki telemetry issue prefills.
#
# Usage:
#   ./scripts/sync_telemetry_labels.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHONPATH=custom_components python3 -c "
from enki.lib.telemetry_labels import (
    TELEMETRY_GITHUB_LABEL_DEFINITIONS,
    TELEMETRY_GITHUB_ORPHAN_LABELS,
)

for name, color, description in TELEMETRY_GITHUB_LABEL_DEFINITIONS:
    print(f'upsert\t{name}\t{color}\t{description}')
for name in TELEMETRY_GITHUB_ORPHAN_LABELS:
    print(f'delete\t{name}')
" | while IFS=$'\t' read -r action name arg1 arg2; do
    if [[ "$action" == "upsert" ]]; then
        color="$arg1"
        description="$arg2"
        if gh label list --search "$name" --json name --jq '.[].name' | grep -qx "$name"; then
            gh label edit "$name" --color "$color" --description "$description"
            echo "updated $name"
        else
            gh label create "$name" --color "$color" --description "$description"
            echo "created $name"
        fi
    elif [[ "$action" == "delete" ]]; then
        if gh label list --search "$name" --json name --jq '.[].name' | grep -qx "$name"; then
            gh label delete "$name" --yes
            echo "deleted $name"
        fi
    fi
done

echo "OK — telemetry labels synced"
