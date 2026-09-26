---
name: alembic-linear-chain
description: "Adding an Alembic migration on a fix branch while a feature branch's migration is unmerged: chain down_revision to it, merge after; never renumber."
type: feedback
---

Alembic migrations require a linear `down_revision` chain. When creating a fix migration on a separate branch from `main`, it must depend on the feature branch's migration number (not skip it). This means the fix branch must be merged AFTER the feature branch. Don't try to renumber migrations to bypass this — just document the merge order.

**Why:** Attempted to create migration 016 on a fix branch when 016 already existed on the feature branch. Alembic would fail with duplicate revision IDs or broken chain.

**How to apply:** When creating migrations on separate branches, always use the next available number and document merge ordering in the commit message.
