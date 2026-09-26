#!/usr/bin/env bash
# Optional local hook: regenerate indexes; MEMORY_SYNC_FETCH=1 also pulls updates.
# Never commits, rebases, resets, or pushes. Publication uses a manual branch and PR.
# start runs now, end launches a background refresh, note prints the reading path.
set -uo pipefail

repo="${MEMORY_REPO_DIR:-$(cd -- "$(dirname -- "$0")/.." && pwd)}"
mode="${1:-start}"

if [ "$mode" = note ]; then
    echo "Shared memory: read $repo/collections/turnstone/MEMORY.md, then relevant files." \
        "Indexes are generated. Follow $repo/AGENTS.md when editing; publication requires" \
        "an explicit request and content review."
    exit 0
fi
case "$mode" in start|end|background) ;; *) echo "memory sync: unknown mode"; exit 1 ;; esac
cd "$repo" 2>/dev/null || { echo "memory sync: clone not found"; exit 0; }
log="$(git rev-parse --git-path memory-sync.log)" || exit 0

if [ "$mode" = end ]; then
    setsid nohup "$repo/scripts/sync.sh" background </dev/null >/dev/null 2>&1 &
    exit 0
fi

# Serialize refreshes across sessions. The lock is not inherited by git children.
if [ -z "${MEMORY_SYNC_LOCKED:-}" ]; then
    MEMORY_SYNC_LOCKED=1 flock -o -E 75 -w 30 \
        "$(git rev-parse --git-path memory-sync.lock)" "$repo/scripts/sync.sh" "$mode"
    [ $? -eq 75 ] && echo "memory sync: another refresh holds the lock; skipped"
    exit 0
fi

# Read or append the log only while holding the lock.
if [ "$mode" = background ]; then
    exec >>"$log" 2>&1
elif [ "$mode" = start ] && [ -s "$log" ]; then
    cat "$log"
    : >"$log"
fi
for state in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
    if [ -e "$(git rev-parse --git-path "$state")" ]; then
        echo "memory sync: a git operation is in progress; refresh skipped"
        exit 0
    fi
done
if [ -n "$(git ls-files --unmerged)" ]; then
    echo "memory sync: unmerged files; refresh skipped"
    exit 0
fi

refresh() {
    [ "${MEMORY_SYNC_FETCH:-0}" = 1 ] || return 0
    [ "$(git symbolic-ref --quiet --short HEAD)" = main ] || {
        echo "memory sync: not on main; fetch skipped"; return
    }
    [ -z "$(git status --porcelain)" ] || {
        echo "memory sync: local edits present; fetch skipped"; return
    }
    timeout 15 git fetch -q origin main || {
        echo "memory sync: fetch failed; keeping local memories"; return
    }
    # Resolve the target once: the scan and the merge must see the same commits.
    target="$(git rev-parse --verify --quiet origin/main^{commit})" || return
    # Only memory-only history fast-forwards on its own; changes to scripts, hooks or
    # CI are code this hook would run, so they wait for a deliberate manual pull.
    python3 scripts/scan.py --proposal --commits "HEAD..$target" >/dev/null || {
        echo "memory sync: incoming commits change more than memories, or failed checks;" \
            "review them and pull by hand (git log -p HEAD..origin/main)"; return
    }
    git merge --ff-only --quiet "$target" || {
        echo "memory sync: branches diverged; resolve manually"; return
    }
}
refresh
python3 scripts/index.py || echo "memory sync: index rebuild failed; run scripts/index.py --check"
exit 0
