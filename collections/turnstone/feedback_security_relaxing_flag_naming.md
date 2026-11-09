---
name: feedback_security_relaxing_flag_naming
description: "Naming a boolean that relaxes a security check (tls_skip_verify): name the unsafe state, default false, one name and polarity across config, API, DB and UI."
metadata:
  type: feedback
---

When the MCP per-server switch for self-signed certificates was built (2026-10-25), the option
put to the maintainer said `tls_verify = false`; the code shipped `tls_skip_verify = true`. The
maintainer accepted it as the more common spelling across the industry, and asked that the two
names and their boolean meanings never be mixed.

**Why:** naming the unsafe state makes every forgotten default fail safe. A missing key, a null,
an older row, or code that drops the default all mean "keep verifying"; with a positive
`tls_verify`, `bool(body.get("tls_verify"))` without its default turns the check off. Mixing the
two spellings across layers invites exactly that inversion.

**How to apply:**
- One name in the config key, API field, DB column, SDKs and docs; DOM ids may only kebab-case it.
- Default false everywhere (column `server_default="0"`). The only polarity flip is at the library
  boundary (`verify=not tls_skip_verify`).
- Accept only a real boolean: the API refuses anything else with a 400, and config files act on
  `is True` only, so a string `"false"` cannot turn the check off.
- Before calling the change done, grep the diff for the other spelling and for negations.
Related: [[feedback_runtime_toggles_settings_registry]], [[feedback_designs_that_need_no_memory]].
