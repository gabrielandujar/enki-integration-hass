#!/usr/bin/env bash
# Create or update GitHub labels (workflow triage + telemetry prefills).
#
# Usage:
#   ./scripts/sync_github_labels.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHONPATH=custom_components:scripts python3 -c "
from github_labels import github_label_definitions, github_label_orphans

for name, color, description in github_label_definitions():
    print(f'upsert\t{name}\t{color}\t{description}')
for name in github_label_orphans():
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

echo "OK — GitHub labels synced"
