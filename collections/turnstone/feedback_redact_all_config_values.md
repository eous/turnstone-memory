---
name: feedback_redact_all_config_values
description: "Grepping a config file, DB row or env dump to find where a secret lives: print key names only, never values; a redaction pattern for one key leaves the other matches in the clear."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-23T12:58:33.151Z
---

When locating a credential in config.toml, a DB, container env or memory notes, print key names
or shapes (prefix, length) only: `grep -o '^[^=]*'`, `${K:0:7}`, `${#K}`. Never print lines and
redact afterwards with a pattern that only covers the key I'm looking for.

**Why:** a grep for `secret|api_key` whose redaction covers only `api_key` values prints every
other matching line in the clear, and it lands in the session transcript. A secret shown that way
has to be rotated.
**How to apply:** move a secret straight into a probe's env by command substitution, so it is
never printed; see [[feedback_secrets_not_in_env]], [[feedback_local_only_memories]].
