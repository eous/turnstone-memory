---
name: feedback_local_only_memories
description: "Public memory boundaries: keep personal, financial, access, private strategy, and undisclosed security details out of shared files and their history."
metadata:
  type: feedback
---

Treat every tracked memory as public. Files under `user/` are ignored local notes; they must never
be staged, committed, linked from shared files, or included in an export.

Keep these categories out of shared memories:

- credentials, keys, credential locations, account state, host inventories, and access paths
- personal matters, finances, budgets, spending, career history, and private priorities
- private business or legal discussions, unannounced plans, and undisclosed security findings
- opinions about identifiable people, private quotations, and unpublished drafts
- internal session identifiers and private note filenames

Record the engineering decision and its rationale in neutral language. Use placeholders for
deployment details. Keep third-party references to necessary technical facts, and verify that
security findings and plans are already public before including them.

**Why:** removing a passage in a later commit leaves it in earlier history. Automated scans catch
some credential patterns but cannot determine whether a conversation or operational detail was
intended for publication.

**How to apply:** review content at write time, inspect every outgoing commit, and read the full
publication snapshot before release. If a private detail is needed locally, store it in `user/`
only when the user requests it. Where local storage cannot persist, leave it out of the repository.
