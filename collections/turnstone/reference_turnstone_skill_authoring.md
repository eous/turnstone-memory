---
name: reference_turnstone_skill_authoring
description: "Authoring a turnstone SKILL.md bundle: at most 10 allowlisted resource files (100 KB each); prose must reference bundle files via ${TURNSTONE_SKILL_DIR}."
metadata: 
  node_type: memory
  type: reference
---

Turnstone skills are **DB-backed** (rows in `prompt_templates` + a `skill_resources` table), NOT files-at-rest. A bundle is installed via skills.sh / GitHub / admin upload and **materialized to a tempdir at runtime**. Source of truth: parser `core/skill_parser.py` (`parse_skill_md` → `ParsedSkill`); resource gating `core/skill_sources.py` (`_accept_resource`); runtime materialize + env + bash exec in `core/session.py`. (Lines drift — grep, don't trust offsets.)

**Packaging caps (install/fetch path — hard):**
- ≤ **10** resource files total; ≤ **100 KB** each; SKILL.md ≤ 256 KB.
- Dirs `scripts/`, `references/`, `assets/` only. **No `data/` dir** — put data under `references/`. **Correction (verified 2026-07-06 against `_accept_resource` in `core/skill_sources.py`):** the gate only checks the FIRST path segment + extension, so nested subdirectories DO pass today — `scripts/sub/foo.py` and deeper are accepted (confirmed by direct call; the GitHub fetch also pulls the tree with `recursive=1`). This has been true since the feature's first commit (#111), not a recent change — the earlier "one level only" claim here was wrong. Don't rely on nesting being blocked; it isn't.
- Extension allowlist: `.md .txt .sh .py .js .ts .json .yaml .yml .toml .cfg .ini`. Everything else — binaries, `.pdf`, `.csv`, and **`requirements.txt` (extensionless)** — is **silently dropped**. Document deps in `compatibility:` or a `references/*.md`, never a manifest.

**Script wiring (the accuracy firewall):** resources → tempdir; files under `scripts/` are `chmod 755` and **on `PATH`**; `$SKILL_RESOURCES_DIR` = the root; the model runs scripts as ordinary `bash` calls and sees **only their output**, never their source. Sibling import works (`sys.path[0]` = script dir). `${CLAUDE_SKILL_DIR}` is **unsupported** (deliberately — that name lives in the host's own bash when turnstone runs as a node inside Claude Code, so turnstone never claims it) → use `$SKILL_RESOURCES_DIR` for bash. **Since 2026-07-03 (commit `3568a6db`, post-dates this memory's origin session)** there is also a canonical **`${TURNSTONE_SKILL_DIR}`** placeholder usable directly in SKILL.md prose: `_substitute_skill_args` resolves it into the actual materialized path at render time (baked into the text the model reads), which is more reliable for small/flash models than expecting them to construct a bash command that expands `$SKILL_RESOURCES_DIR`. Both env vars are exported for bash subprocesses too (`TURNSTONE_SKILL_DIR` canonical, `SKILL_RESOURCES_DIR` back-compat, same directory). **SKILL.md prose must reference bundle files by absolute path** (either substitution form) — the runtime CWD is NOT the bundle and each bash call is a fresh shell, so bare relative paths (`references/...`) fail and derail small/flash models; scratch files go under `/tmp/`. Bundles ≤ 8 KB total get **inlined into context** — keep total > 8 KB for strict on-demand.

**Zero added deps available in-host:** PDF via `pypdfium2` + `pillow` (core; mirror `core/pdf.py` `extract_pdf_text`/`rasterize_pdf`); HTTP via `httpx2` or `httpx` (both declared; #1011 moves Turnstone-owned HTTP to `httpx2`, so prefer it); `pydantic` v2 + `python-frontmatter` (core). **NOT declared:** PyYAML, bs4, lxml → use stdlib `json` + `html.parser`. The base interpreter may lack these; use the project venv (`.venv/bin/python`).

**Frontmatter:** `name` (≤64, `[a-z0-9-]`, no `--`); `description` (author **≤1024** for portability; turnstone caps 1536). Turnstone extras: `when_to_use`, `model`, `effort`, `user-invocable` (load-bearing → hides from picker), `arguments`/`$<name>` + `$ARGUMENTS`/`$N`/`${CLAUDE_SESSION_ID}`/`${CLAUDE_EFFORT}` substitution. `paths` + `disable-model-invocation` parse but have **no consumer** yet. No reserved-word block (anthropic/claude allowed — avoid anyway).

**Gaps vs official Agent Skills spec:** no parent-dir/name coupling, no reserved-word enforcement, desc cap 1536 (not 1024), and the strict resource allowlist above (official allows arbitrary files/dirs/types + network only in Claude Code). Only in-repo example was prose-only (`docs/skills/import-conversation-history/SKILL.md`) — first scripts/-bundling example is `project_civic_research_skill` (not saved).

See [[project_skills_system]].
