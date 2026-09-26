---
name: project_881_boot_epoch
description: "#881 global-SSE boot epoch SHIPPED PR #896: ids are epoch-counter at _format_event; its browser reconnect gotchas surfaced only in the real-browser harness."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-23T06:24:46.172Z
---

**SHIPPED: PR #896 from `fix/881-global-boot-epoch` (2026-07-22, 11 commits; closes #881 + rider #885 + CI test-timeout 20→30). The last silent-gap class from the [[project_sse_truncated_resync_hole]] campaign.**

**Design (rulings at-site; do not re-litigate):** every global SSE id is `"{boot_epoch}-{counter}"` — `secrets.token_hex(8)` per process, attached at the single `_format_event` chokepoint. Epoch-in-id over handshake-carried was decisive because the browser echoes the opaque id verbatim on NATIVE auto-reconnects — the dominant restart path, unreachable by any handshake field. Three-way parse: absent→fresh; same-epoch→ring logic untouched; anything else→`replay_truncated reason="boot_epoch"` (numeric fields omitted — no consumer reads them, mapper-verified) + snapshot floor; in-epoch ring miss keeps honest lost_count under `reason="ring_evicted"` (boot_epoch also covers the same-epoch-empty-ring fail-safe). Registration under the fan-out lock (no-loss ordering, load-bearing), O(W) snapshot AFTER release inside a registration-window guard (`_deregister` shared with the generator finally; BaseException; await-free-window constraint documented). app.js cursor: captured pre-dispatch, presented `?last_event_id=`, cleared at THREE tripwire-pinned sites — truncated branch, node_snapshot branch (REQUIRED — see lesson 1), onLogout. Per-ws ids stay bare ints (storage-seeded counter; epoch prefix would NaN coordinator.js's `Number()` reset detector — ruling at `_format_event`). Collector stays cursorless (ruling at `_node_sse_task`); SDKs fresh-only + id-blind.

**Three browser/infra mechanisms — ALL found only by the real-browser harness (mechanism-5 lesson re-validated three times):**
1. **Id-less SSE frames inherit the connection's persisted `lastEventId` on native reconnects** (WHATWG; a fresh EventSource starts empty, so manual paths are immune). A pre-dispatch cursor capture therefore RE-STORES a just-cleared dead cursor on the envelope/snapshot frames — clears must live in the snapshot branch itself, not only where the gap is detected.
2. **A failed EventSource reconnect ATTEMPT is terminal** (fail-the-connection → CLOSED, no second retry). Any restart e2e wanting the native leg must never expose a refused window — the harness now has `make_listen_socket` (SO_REUSEPORT on every listener) + RecoveryServer `sock` injection: bind the successor's placeholder before stopping the old node; its backlog carries the single retry across the boot.
3. **uvicorn's graceful drain parks indefinitely on an SSE stream still open at stop()** — the 20s join just expires and the browser stays attached to the zombie. `timeout_graceful_shutdown=2` bounds it; lifespan shutdown (and #885's thread teardown) still runs after the bounded drain.

**#885 (rider, closed):** the three lifespan daemon threads got a real shutdown — shared Event as tick sleep, identity-checked `_FANOUT_SHUTDOWN` queue sentinel (FIFO drain), bounded off-loop joins. Harness dropped its thread-neutering workaround (docstring piece 4) — which is what let the global lane run real in e2e.

**Review history (validates [[feedback_review_convergence_methodology]] + the fix-loop):** mapper-first (7 closed edges pre-implementation incl. the service-scope bound: browsers reach the global stream only via token-login-inherited service scope — auth.py:1634 + admin.py mint). r1 = 0-correctness (perf: snapshot-under-lock; quality: false coverage pointer). **r1's lock fix manufactured r2's listener-leak regression** (registration-first left the raising build unguarded before the generator's finally existed — the append-last-in-lock base was the exception-safety) → seam redesign (window guard), the campaign's fix-rounds-manufacture-findings lesson re-validated verbatim. r3 = 0-corr (native re-capture → verify-classified redundancy-doc-contract), r4 = 0-corr (32-bit nonce → design-margin, widened anyway; De Morgan absence-assert → test-honesty) → converged r3+r4; post-convergence F1/F2 delta got a targeted single-finder review (clean). **Converged-tail finder drops exercised**: security after 2 zeros (the maintainer's call), performance after 2 zeros; bug never drops. **Verify-classifies-the-ledger pattern worth keeping**: when a finding's correctness-vs-{design-margin, redundancy, test-honesty} classification decides the convergence clock, pose it to the verify stage explicitly and adversarially — never self-rule as the author.

**Scenario F2's discriminator shape (reusable):** phase C forces a manual reconnect immediately post-heal and asserts CURSORLESS + no second truncated (`cursor0-trunc1`; pre-fix shape `cursor1-trunc2`), guarded by an idFrames-unchanged precondition against the 10s aggregate tick, with es-readyState in failure verdicts. `__globalOpens` counts CONSTRUCTIONS (native reuses the object) — isolates the manual leg cleanly.

Historical follow-up candidates (verify current issue state): `_build_node_snapshot` producer
field-projection has no direct unit test (honest pointer at the stub); dashboard TABLE membership
refreshes on interaction only (the maintainer to rule wart-vs-design before anyone "fixes" it).

Related: [[project_sse_truncated_resync_hole]] (campaign parent), [[project_890_clear_ui_guard]], [[feedback_harness_scripted_events_not_verification]].
