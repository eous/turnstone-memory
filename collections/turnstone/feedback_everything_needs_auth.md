---
name: feedback-everything-needs-auth
description: "New session kind, actor, or token lane: require a real authenticated principal at construction, fail loudly; user_id='' stays a CLI/eval-only sentinel."
metadata: 
  node_type: memory
  type: feedback
---

Everything in turnstone needs some form of auth; exceptions may exist, but this was not one — stated
2026-06-12 while flagging unauthenticated coordinators as a bug (fixed: ChatSession refuses
kind=COORDINATOR with empty user_id; console no longer masks empty uid as a phantom "system"
principal when minting coordinator JWTs).

**Why:** anonymous actors that mint tokens, own persisted rows, or get
durable namespaces create unattributable authority (audit holes, shared
fail-open namespaces like a `scope_id=""` memory pool).

**How to apply:** when adding any new session kind / actor / token lane,
require a real authenticated principal at the construction choke point and
fail loudly (no `or "system"`-style masking, no silent empty-string
fallthrough). The one sanctioned exception: `user_id=""` as an
interactive-only sentinel for CLI / eval / placeholder sessions (documented
in ChatSession.__init__). Don't extend that sentinel to new kinds. See
[[project_canonical_trajectory_redesign]] for the session.py landscape.
