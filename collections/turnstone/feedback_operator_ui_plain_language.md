---
name: feedback_operator_ui_plain_language
description: "Operator UI copy or a user setting hitting the wire (PR #774 effort labels): plain domain words; send verbatim or visibly snapped, never silently."
metadata: 
  node_type: memory
  type: feedback
---

2026-07-05 (PR #774 session): effort-select labels "Max (= minimal)" / my proposed "Max (= on)" both rejected as badly confusing to a user who neither knows nor cares how the code is implemented. Two proposal rounds failed before alignment; the user's stated rule: setting max reasoning effort should send max on the wire, with snapping acceptable only against a declared vocabulary and visible in the label.

**Why:** UI annotations derived from internal projection tokens leak implementation dialect; silently degrading an explicit user setting (effort → bare boolean toggle) violates least surprise even when the degradation is "technically truthful".

**How to apply:** (1) Translate internal state into plain domain words in UI copy ("Low — sends high"), never internal tokens or sibling references. (2) An explicit user setting must reach the wire verbatim or visibly snapped — if the config can't express it, fix the semantics rather than annotating the loss. (3) When challenged on UX, re-derive what a non-implementer reads instead of defending implementation truthfulness. See [[project_messages_api_provider]].
