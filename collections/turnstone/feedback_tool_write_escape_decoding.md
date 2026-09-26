---
name: feedback_tool_write_escape_decoding
description: "Typing literal escape sequences into Write/Edit/Bash args: a bare backslash-u XXXX escape lands as a raw byte (git sees binary); backslash-x hex is safe."
metadata: 
  node_type: memory
  type: feedback
---

Strings passed as Write/Edit/Bash tool arguments are escape-decoded by the transport before hitting disk: a backslash-u-XXXX unicode escape in the argument becomes the raw codepoint **byte** in the file (verified live this session — the NUL escape produced a raw 0x00 byte; the escape for 'A' produced a literal A). Double-backslashing is unreliable (the doubled form did not collapse cleanly). This silently shipped raw 0x00/0x01 separators in `projects.js` `_fp()` — runtime-identical to the escape inside a JS string, so node/prettier/tests all passed, but git treated the whole file as **binary** (no reviewable diff; `file` reports "data").

**Refined 2026-07-07 (renderer.js containment work, byte-verified with hexdump):** the trap is **specific to `\uXXXX` 4-hex-digit unicode escapes**. `\xNN` **hex** escapes are SAFE — typed `\x00`/`\x08`/`\x1f`/`\x7f` all survived as the literal 4-char escape on disk, as did `\u{0000}` (brace form), `\0`, and regex metachars `\n \t \d \s \/ \1`. Only bare `\uXXXX` decoded to a raw byte. So a whole `renderer.js` was authored with literal `\x00` sentinels and `/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/` classes typed directly, byte-clean. A design brief that lumps `\x00` in with the trap is over-general — prefer `\xNN` (it also matches this file's existing `\x00` convention). Still byte-scan after (`file` + `LC_ALL=C grep -aPc '[\x00-...]'`), since the cost of a miss (binary file) is high.

**Why:** the model intends a literal backslash-escape *sequence* (a JS string escape, a regex metachar, etc.) to land in the file as text, but the tool transport interprets it one level first — but only for the `\uXXXX` form.

**How to apply:** when source needs literal escape sequences, don't type them raw into Write/Edit. Prefer escape-free constructs (`String.fromCharCode`, `JSON.stringify`, `chr()`), build the bytes programmatically in a Python/Bash one-liner, or write a no-backslash helper script and run it. Edit's `old_string` matching fails the same way — a unicode escape in `old_string` won't match the literal text already in the file, so anchor matches on escape-free substrings. After writing any source with intended escapes, byte-scan for control chars or run `file`. Relates to [[feedback_artifact_cleanliness]].
