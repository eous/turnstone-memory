---
name: feedback_redaction_regex_design
description: "Editing output_guard or redact_credentials.js rules: whole-value rules before key-prefix rules, runs stop where the next match could start, linear-time and long-value tests."
metadata:
  type: feedback
---

The #1233 branch (PR #1238, 2026-09-30) spent most of its ten review rounds on regressions that
earlier fixes put into the credential-redaction regexes:

- a JWT rule that could start at every "eyJ" inside one base64 run (46 s on 300 KB);
- a connection-string password capped at 256 characters for speed, which silently stopped
  redacting longer passwords;
- a "/" stop, then a "://" stop, each dropping a real password shape;
- a %26 stop that cut ordinary query values short;
- whole-value rules ordered after the key-prefix rules (sk-, ghp_, AKIA), which redacted a value's
  start and left its tail visible.

**Why:** redaction runs on every tool result, audit detail and lowered httpx2 log line. A quadratic
pattern is a denial of service a fetched page can trigger, and a speed fix that narrows a match
leaks without any test noticing.

**How to apply:**
- Rules that know a value's whole extent (JWT, credential-named query parameter, connection
  string) run before rules that recognise only a key's start. Keep `_CREDENTIAL_PATTERNS` and the
  registry priorities in step; the order-parity test pins them.
- For linear time, let a match start only where the token can start, and stop each repeated run
  exactly where another match could begin. For connection strings that is the scheme alternation
  with a bounded driver suffix, with the same bound in the match and in the stop. Never stop at a
  length cap.
- Tie a stop to the encoding level that makes it a separator: %26/%23 end a value only after %3D.
- Pin a linear-time test for each input family (nested, escaped, suffixed) and a long-value test,
  and confirm each fails when its fix is reverted.
- Mirror every change in `shared_static/redact_credentials.js`, add new anchors to
  `_RE_PREFILTER` (#797), and give a JS perf input a prefix that passes the prefilter, or the
  pattern never runs.

Related: [[feedback_regex_timeout_needs_subprocess]], [[project_output_guard_llm_merge]],
[[feedback_nonconverging_reviews_mean_simplify]], [[project_1233_guarded_fetch_httpx2]].
