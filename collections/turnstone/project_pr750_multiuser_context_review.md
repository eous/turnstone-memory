---
name: project_pr750_multiuser_context_review
description: "PR #750 multi-user chat context (external, merged 07-02): CLOSED; 3 majors fixed by 7f20b1bc/21efeece; re-verify session.py/fence.py before citing any as open."
metadata:
  node_type: memory
  type: project
  modified: 2026-07-20T17:01:55.993Z
---

**PR #750** was reviewed on 2026-07-02: 12 findings became 11 after clustering. It merged that day,
with the technical follow-ups recorded below. This is a dated review record; verify the current code
before citing a finding as unresolved.

**The 3 majors flagged pre-merge — all addressed by follow-up commits landed the same day or the day after:**
1. `_recompute_shared_state` deriving `_known_senders`/`_shared_workstream` from the compaction-narrowed message slice (duplicate `participant_joined` notes, True→False banner flips thrashing the cached prompt prefix) — addressed by `7f20b1bc` "fix(session): durable shared-workstream state + fork sender persistence".
2. `resume(fork=True)` bulk-persist dropping `_sender` on row meta (forked user turns losing attribution on reopen) — addressed by the same `7f20b1bc` pass.
3. Unfenced `[message from X]` sender labels (any participant could type a forged label / impersonate the owner) — addressed by `21efeece` "fix(session): fence sender labels; move shared-ws behavior to a declaration".

**Further hardening landed in the same wave** (not independently re-verified line-by-line, but all present in `git log`): `2ba54266` blocks cross-user mid-turn interjections, `9c1b76b6` disables send for non-acting participants while busy, `6424f73d` extends the cross-user send gate to the coordinator surface, `b9f95c35` addresses ultrareview findings on the shared-workstream branch, `73e7972f` closes out PR feedback + CI typecheck/test failures.

**Treat this thread as closed.** Before citing any of the 3 majors as still-open, re-verify against current `core/session.py` (`_recompute_shared_state`) and `fence.py` (`SENDER_LABEL_TAG`) — this memory asserts they're fixed based on commit messages, not a fresh line-by-line re-read.

**Minors/nits from the original review** (lower confidence — not independently re-verified as fixed, check before citing): banner overclaiming per-participant credentials (only MCP `oauth_user` honors `_mcp_effective_user_id`; built-ins run as server/owner); `_resolve_display_name` precedence (`username or display_name`) opposite of `auth.py:1736`, a 5th copy of the same idiom; per-turn (not per-distinct-sender) name resolution during storage outages; lineage/tombstone comments; bare `etc/` in `.gitignore`.

**Cleared at review time (don't re-litigate):** `_sender` not client-forgeable (server-stamped, sanitize-stripped everywhere incl. the Anthropic native lane); fold/repair/sanitize ordering sound; `reconstruct_turns` meta routing role-exclusive; no migration needed; no new endpoint/scope surface.

Relates to [[project_external_contributor_review]] (same process, lessons applied — this is its "second instance") and [[project_envelope_nonce_tags]] (the fence-fix pattern reused here).
