---
name: commit-artifact-cleanliness-what-not-to-include
description: "Writing a commit, PR body, code comment or planning doc: no tool attribution or product names (even homages); design notes stay local in docs/design/."
metadata: 
  node_type: memory
  type: feedback
---

Consolidated rules for what to keep OUT of commits, code, and generated artifacts (plus one output-path rule). All are standing user preferences.

**No Claude Code mention.** Don't include "Generated with Claude Code" or similar tool attribution in PR descriptions, commit messages, or any generated content. Omit the `🤖 Generated with [Claude Code]` footer and any other auto-attribution pattern. *Why:* user preference — no tool attribution in project artifacts.

**No Co-Authored-By trailer.** Do not add `Co-Authored-By: Claude ...` (or any co-author) trailer to commit messages. *Why:* user preference — no co-author attribution in commits.

**No product names — including genre/inspiration references.** Do not reference other products' names in commit messages, code comments, docstrings, READMEs, or PR descriptions. Describe the behavior, not the origin — "split-pane layout" not "<editor>-style splits"; "classic-door-game-style legacy reset" not "<game>-style reset"; "in the BBS door-game tradition" not the title of the game it echoes. *Why:* turnstone gets its own identity, not references to other products. **This includes the games/tools you're paying homage to** — the blind spot is that inspiration references feel like flavor, not branding. Scrub them at write time, not at the PR gate: in the Understone build (2026-06-12) the name of the game it echoes leaked into 4 files + 3 commit messages and the user caught it only when the PR was about to open. Cost: a full branch-history rewrite (`git filter-branch` scoped to `main..branch` with `--msg-filter`/`--tree-filter` over a shared sed script) + `reflog expire --expire=now --all` + `gc --prune=now` + a fresh branch + re-push. NB the old pre-scrub objects stay reachable (un-prunable) until you ALSO delete the stale `refs/remotes/origin/<branch>` tracking ref, even after the remote branch is deleted upstream.

**No tombstone comments.** When deleting a stale/dead line, just delete it — don't replace it with a 3–5 line comment narrating why it was removed. *Why:* git blame + the PR thread already carry that context; an inline tombstone is noise for future readers and rots as surrounding code evolves (observed on PR #373; user reverted it as overly descriptive). If context is genuinely load-bearing, put it in the commit message, not a code comment.

**Design docs are local-only, and they live in the `docs/design/` FOLDER — don't invent root planning files.** Put planning/design/working notes in `docs/design/*.md` (the usual place), NOT a root `BRIEFING.md` / `PROGRESS.md` / etc. They are never committed: `git status` should show them untracked; never `git add`. *Why:* design docs evolve during implementation and aren't a stable deliverable (user pushback on PR #424); at ~50K LOC/week paths/signatures/line-refs rot within days, so a committed doc misleads more than it helps. Summarize the rationale inline in the PR description; keep the doc local. **Recurrence 2026-07-12:** created a root `BRIEFING.md` as a working plan, then a single `git add -A` (instead of naming files) swept it into a feature-branch commit; the xhigh finder caught it and it took a cherry-pick history rewrite to remove. Two guards: (1) planning docs go in `docs/design/`, not root — that's the usual convention; (2) prefer naming files in `git add` over `-A` so untracked local docs can't hitch a ride.

**PR bodies describe what changed, not what was skipped.** Keep the PR description to the actual changes; don't add a "left as-is / out of scope / benign noise" section cataloguing things you deliberately didn't touch. *Why:* user trimmed exactly this from PR #641 as noise. The triage of benign-vs-real belongs in the chat thread; the PR body is a record of the change. Same lean posture as the no-tombstone rule. (Genuine follow-ups a reader needs — known-unfixed bugs, the next PR in a sequence — are fine; the ban is on cataloguing non-changes.)

**No process meta in PR bodies.** Don't describe HOW the change was reviewed (review rounds,
tooling, methodology) or mention account or quota limits hit along the way. The PR body is about the
change, not the process that produced it — that's chat-thread context. Applies even when the process
was notable (a crashed review, a recovered run); keep it in the conversation.

**PlantUML PNG output path.** Generated PNGs go in `docs/diagrams/png/`, not alongside the `.puml` source in `docs/diagrams/`. *Why:* the project keeps `.puml` source and `.png` output in separate directories. Use `java -jar /tmp/plantuml.jar -tpng -o png docs/diagrams/*.puml` (the `-o png` flag emits to a `png/` subdir relative to each input).
