---
name: pre-commit-quality-gates-lint-review-docs
description: "Before any commit or push: ruff+mypy (Python only) plus an unprimed /review per chunk, fix rounds included; never pipe pytest, read its summary line first."
metadata: 
  node_type: memory
  type: feedback
---

The user expects a consistent set of quality gates on EVERY commit and push, not just the final one. Apply all of the following before staging/committing, and re-run lint before pushing.

## Lint (ruff + mypy)
- **Before every commit AND before every push.** Run `ruff check` and `mypy` before each `git commit`, then again after commit and before `git push` — the pre-push run is the last gate, and issues caught after push need an extra commit to fix.
- Commit-time: run on the full package (`python -m ruff check turnstone/`, `python -m mypy turnstone/`). Pre-push: at minimum `ruff check turnstone/ tests/` plus `mypy` on changed production files (e.g. `turnstone/core/session.py`, `turnstone/server.py`).
- If a commit was already made without linting, verify immediately and amend if needed (subject to the git-workflow amend rules — see [[feedback_git_workflow]]).
- **Ruff and mypy are PYTHON-ONLY.** Never pass JS/CSS/HTML to ruff — it produces thousands of garbage parse errors (caught once feeding `admin.js` to ruff). Restrict paths to `.py` files.

## Running pytest: NO pipes (user directive, 2026-06-16)
- **Never pipe pytest** (`pytest … | tail`, `| grep`, etc.) — a pipeline's exit status is the LAST stage's (`tail`/`grep` exit 0), which **masks pytest's real exit code**. Run it bare so the exit code is authoritative: either backgrounded (`run_in_background`, output → file, then read the file's summary), or foreground with `-q --tb=short`/`--tb=line` to keep output manageable WITHOUT a pipe. This rule holds especially while flaky tests exist — a masked exit code + a flake = a silent bad release.
- **Why (caught the hard way 2026-06-16):** a backgrounded `pytest -m "not live" | tail` reported "exit code 0" (tail's) while pytest had `1 failed`; a chained commit+release shipped a tag (v1.7.0a2) on a red gate. The failure was flaky (`test_tls_client` passes 15/15 in isolation; re-run was 7514/7514) — but the process was wrong regardless.
- **Run the local full suite as `-m "not live"`, not CI's selection.** CI deselects `e2e_recovery` as well, so a break in the SSE end-to-end harness goes unnoticed there: in #988 the harness's custom session factory swallowed a new `workstream_lease` kwarg for two review rounds (2026-10-03).
- **Read the SUMMARY LINE** (`N passed` with NO `failed`/`error`), not just the exit code, before committing/tagging/pushing on a suite's strength.
- **Never chain `commit`/`release`/`push` after a suite in one unconditional command.** Run the suite → READ the result → commit/release as a SEPARATE step gated on green. A red gate (even a suspected flake) stops the release until the failure is re-run in isolation and explained.

## Review (use the /review skill)
- **Always run code + security review before committing — even for small chunks.** This is a consistent quality gate: review → fix → commit for every chunk, not just large ones.
- **Use the `/review` slash command, NOT the single-pass `code-reviewer` subagent.** `/review` is the multi-stage pipeline (4 parallel specialist finders → verify → dedupe → synthesize → final markdown report). *Why:* parallel finders + a verify step that re-reads cited source catch more, and the structured report matches the user's review-fix cycle; the single-pass agent is shallower and has missed things in practice.
- **Stage the new + modified files first** (`git add <paths>`) so the diff the pipeline reads reflects the actual change set — untracked new files are invisible to a base-tree diff otherwise.
- **Run reviews incrementally**, after each logical chunk completes (storage layer → API endpoints → SDK methods, etc.), not batched at the end of a large feature. *Why:* catches issues early instead of deferring all review to the end.

## Fix rounds get their own review — UNPRIMED (user catches, 2026-07-10)
- **Code written in RESPONSE to review findings is new, unreviewed code.** A review of the pre-fix diff does not cover the fixes — if applying findings added substantial code (a new module/pass/seam, not a one-line tweak), run the review again before pushing/PR. Caught on the sub-tool id PR: the pre-fix review ran, the fixes added a whole lowering pass + a session counter, and the push was about to go out with that code unreviewed (the user had to ask whether it had been reviewed).
- **Do NOT steer the re-review at the fix code.** Steering finder attention ("focus especially on …") makes findings artificially converge — the #819 lesson ([[feedback_review_convergence_methodology]]): delta-steered rounds measure attention allocation, not convergence, and #819's unprimed round 6 found 2 CRITICALs after five steered rounds looked clean. The re-review runs unprimed over the ENTIRE change (scope = what the diff is, e.g. "branch X vs main"; never where to look inside it). Caught a second time same day when I steered the round-2 review at the fix locations.

## Sanity before fixing
- After dedupe returns its findings, **always run the sanity stage on the deduped finder set BEFORE applying any fixes** (`subagent_type: "code-review-sanity"`) — even when findings look like targeted, well-cited, obviously valid bugs.
- *Why:* sanity's highest-value output isn't validating individual fixes — it's identifying **choke points** where one targeted change collapses multiple findings into a single concise edit. Without it the model tends to fix finding-by-finding, producing N edits where one well-placed edit would do: bigger diffs, more review surface, more places for a future regression to slip through.
- Read sanity's output for collapse opportunities before opening the first Edit (e.g. if two bugs share one guard, fix the guard once). The cost is one extra agent call; the upside compounds.
- Skipping sanity is acceptable only in tightly-scoped, single-finding cases with no chance of overlap.

## Docs before committing
- **Update all relevant documentation as part of the same commit as the code**, not as an afterthought: `README.md` (if user-facing behavior changed), `docs/*.md` (feature docs), `docs/diagrams/*.puml` + regenerated PNGs, and `PROGRESS.md` (local-only — track what was done).
- *Why:* documentation drift accumulates when docs lag the code; the user wants docs and code committed together.

Related: [[feedback_git_workflow]], [[feedback_sdk_boundary_testing]].
