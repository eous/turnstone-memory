---
name: feedback_changelog_dated_headings
description: "Adding a CHANGELOG entry for unreleased work on main: head it with the date the change was made, not [Unreleased] (maintainer, 2026-10-25)."
metadata:
  type: feedback
---

Since `dev` was retired (2026-10-23) all development integrates on `main`, and preparing a release
turns the development changelog into release notes under a version heading (docs/releasing.md).
For work not yet released, the maintainer asked (2026-10-25, the MCP `tls_skip_verify` change) to
use the date the change was made as the section heading instead of `## [Unreleased]`.

**Why:** with every change landing on `main`, a dated section says when each entry arrived, which
the release prep needs when it groups the notes; an `[Unreleased]` bucket loses that.

**How to apply:** add the entry under `## [YYYY-MM-DD]` (the change's date), above the newest
version heading. The brackets match the existing `## [1.9.0]` style; that choice was mine, not
part of the ruling, so follow any later example in the file. The older "pre-releases keep
`## [Unreleased]`" note in [[project_current_state]] predates this.
