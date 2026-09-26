---
name: sse-fanout-pending
description: "SSE fan-in or browser connection cap (#540): RESOLVED, never built; Caddy HTTP/2 retired the 6-connection cap, per-pane EventSource is canonical."
metadata:
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:34.860Z
---

**RESOLUTION (recorded 2026-06-11): the fan-in was never built (issue #540).**
Turnstone now ships Caddy with HTTP/2 + TLS and dropped HTTP/1.1 as the supported
browser-facing shape (the old "HTTP/1.1 stays first-class" operator policy flipped — see
[[project_mtls_architecture]]). HTTP/2 multiplexing retires the browser's 6-connection-per-origin
cap, which was the entire problem. The L-shell ([[project_frontend_lshell_renovation]])
therefore uses **per-pane `EventSource` Tier-2 streams + ONE global Tier-1 clusterState
stream as the canonical architecture** — do NOT resurrect this memory's old "per-pane SSE
is the wrong architecture" guidance; it inverted.

**What survived from the #540 design:** reconnect-with-replay shipped as the event-id
cursor resume (#610/#612/#616, [[project_fresh_connect_replay_completeness]]). The
message-bus envelope (`node_id, ws_id, seq_id, event_type, payload`; per-(node,ws)
monotonic `seq_id` for gap-detection + ordered replay) remains an unbuilt design breadcrumb.

**If an HTTP/1.1-constrained deployment shape ever returns**, the #540 design held:
trilemma framing (real-time-in-every-tab / unbounded tabs / no out-of-band channel — pick
two); sequencing = replay → fan-in (envelope `node_id, ws_id, seq_id, event_type, payload`)
→ service-worker push → lifecycle close; the "let-it-die" idle-TCP parking insight;
`visibilitychange` does NOT fire for side-by-side visible windows (needs debounced blur).
Rejected then: WebSocket, polling-for-inactive, max-age teardown, external brokers, and
removing per-ws SSE endpoints — those endpoints have hard dependents (channel adapters
`channels/_sse.py`, both SDKs' published contracts), so any future fan-in must stay
purely additive.
