---
name: feedback_mutation_control_hygiene
description: "Running mutation or negative controls: commit the fix first; restore mutants from a python-held copy, never git restore/stash (#894 lost work 4x)."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-07-24T22:01:14.073Z
---

Commit the fix under test **before** running mutation controls or negative controls, and restore mutated files from a **python-held copy of the original** (read the file into a variable, write the mutant, run, write the variable back) — never `git restore`/`git checkout --`/`git stash` while related work is uncommitted.

**Why:** `git restore --source=HEAD` reverts to a state that lacks any uncommitted fixes — in the #894 campaign this silently destroyed in-progress work four separate times (twice wiping the current fix-round's production edits mid-validation, once popping an unrelated pre-existing stash into the branch with conflicts across seven files). The python-held pattern is immune: the restore source is the exact bytes that were just on disk.

**How to apply:** the control loop is (1) commit the round's fixes; (2) for each mutant: `orig = read(); write(mutate(orig)); run test; write(orig)`; (3) never mix `git stash` into control scripting at all — the stash stack may hold the maintainer's unrelated WIP.
