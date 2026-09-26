#!/usr/bin/env bash
# Public reader setup. Supply MEMORY_REPO_URL, then --agent and --project arguments.
# No write token or publication hook is installed. Reruns preserve existing edits.
set -euo pipefail

: "${MEMORY_REPO_URL:?set MEMORY_REPO_URL to the public clone URL}"
repo="${MEMORY_REPO_DIR:-$HOME/turnstone-memory}"
case "$MEMORY_REPO_URL" in
    *'?'*|https://*@*|http://*@*)
        echo "Use a clone URL without embedded credentials or query parameters" >&2
        exit 1 ;;
esac

if [ -e "$repo" ]; then
    actual="$(git -C "$repo" rev-parse --show-toplevel)"
    [ "$actual" = "$(cd -- "$repo" && pwd -P)" ] || {
        echo "MEMORY_REPO_DIR is not a repository root" >&2; exit 1;
    }
    [ "$(git -C "$repo" remote get-url origin)" = "$MEMORY_REPO_URL" ] || {
        echo "Existing clone has a different origin; choose another MEMORY_REPO_DIR" >&2; exit 1;
    }
else
    GIT_TERMINAL_PROMPT=0 git -c credential.helper= clone -q -- "$MEMORY_REPO_URL" "$repo"
fi
python3 "$repo/scripts/index.py"
python3 "$repo/scripts/setup.py" --memory-dir "$repo" "$@"
