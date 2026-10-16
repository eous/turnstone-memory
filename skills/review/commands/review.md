---
description: Multi-stage code review pipeline — 6 parallel finders (bug, security, performance, quality, regression, simplification) → verify → optional sweep (+ verify) → sanity (merge, fix-check, render) → final markdown report.
---

# Code Review — multi-stage pipeline

Review target: `$ARGUMENTS` — or, if empty, uncommitted changes + last commit.

This is a **top-level command** because sub-agents can't recursively spawn sub-agents via the Agent tool in this harness. Running the pipeline from here lets Claude spawn the finders, verify and sanity stages as parallel / serial Agent calls.

## Pipeline

```
find-bug             ─┐
find-security        ─┤
find-performance     ─┤
                      ├──► verify (1..n) ──► [sweep ──► verify] ──► sanity ──► final markdown
find-quality         ─┤      (claim           (optional: variants     (merge + fix-verify
find-regression      ─┤       check)           + gaps, then verify     + render)
find-simplification  ─┘                        its findings)
(parallel)
```

Each stage's job:
- **Finders** (parallel): each owns a single dimension; emit JSON findings only. Four judge the new code (bug, security, performance, quality); `find-regression` compares it with the base it replaces; `find-simplification` asks whether the design carries more mechanism than its problem needs.
- **Verify** (serial; one verifier, or several on a large review, each taking a batch): re-reads source and decides confirmed / refuted / uncertain for each finding's *claim*.
- **Sweep** (optional, serial, one per review): for high-stakes reviews only. Takes every finding with its verdict, hunts the whole change for variants of each confirmed finding and for gaps the finders left, and returns new findings, which get one verify pass of their own.
- **Sanity** (serial, always exactly one): merges the verified findings across every verifier's batch (drops refuted, applies severity overrides, clusters duplicates), re-reads source for each merged finding's *fix*, refines / validates / marks unverifiable, then renders the user-facing **markdown**. It is the only stage that sees every batch, which is why the merge lives there.

## Step 1 — Determine scope

From `$ARGUMENTS`, or infer from conversation context, figure out:

- **What to review**: file list, branch range (`origin/main..HEAD`), specific commits, or "uncommitted + last commit" as a default.
- **Context**: what the change is trying to accomplish, any focus areas the user called out, what's already been verified (lint, tests, manual pass).

If the scope is ambiguous and the default isn't obviously right, ask once and wait; otherwise proceed with the default and state the assumption in the final report's summary.

Compute the actual diff once (via `git diff <base>..HEAD` or by reading the listed files) so the finders all operate on the same bytes. Pass the diff — or a path to it — into each finder's brief.

## Step 2 — Spawn the six finders in parallel

**In a single message, make six concurrent Agent tool calls** — one per finder. Parallel invocation is how we get the wall-clock win; serial spawning defeats the design. All six run on every review, small diffs included: the regression and simplification finders catch what the four dimension finders miss (behavior drift outside the change's own mechanism, and fix-breeds-finding chains).

Finder agent types:
- `code-review-find-bug`
- `code-review-find-security`
- `code-review-find-performance`
- `code-review-find-quality`
- `code-review-find-regression`
- `code-review-find-simplification`

Each finder's `prompt` should contain, verbatim:

- The diff (inline if small; otherwise a path + a `git show` / file-list pointer the finder can read).
- The context block from Step 1.
- Reminder that the finder returns JSON only — no prose wrapper.

Two finders need one more thing each:

- **Regression**: the base ref, plus read-only base and head worktrees (or say it may `git archive` its own copies) so it can run the two side by side. Name anything that states intent: the PR description, the CHANGELOG, the docs, the maintainer's rulings.
- **Simplification**: the problem statement as its own block (the PR description, the issue, or a summary of the goal), because it designs from the problem before it reads the surrounding code. If earlier rounds kept finding bugs in the previous round's fixes, say so: that is its strongest signal.

Every brief also says: read-only (probes go in the finder's own scratch directory), time-boxed (targeted probes only, no stress loops, no fuzzing, no full-suite runs), and which databases or services, if any, the finder may use. The agents refuse every existing database and live service the brief doesn't explicitly allow, so naming the dev database as off limits is belt and braces, not the only guard.

Do NOT tell a finder what the other finders are doing. Each works in isolation; sanity handles overlap.

## Step 3 — Combine finder output

Each finder returns a JSON object:

```json
{
  "finder": "bug|security|performance|quality|regression|simplification",
  "findings": [
    {"id": "...", "severity": "critical|major|minor|nit", "location": "...", "claim": "...", "evidence": "...",
     "failure_scenario": "...", "probe": "...", "pre_existing": false, "fix": "..."}
  ]
}
```

`evidence` is a verbatim quote of the code; `failure_scenario` is what the claim predicts; `probe` is what the finder ran and saw (empty when it only read); `pre_existing` marks a defect that predates the change, in code the change touches (finders report these rather than dropping them, and the reader decides). The regression finder also returns an `intended` list, and sweep findings add `dimension` and `variant_of`.

Build the combined list: concatenate all six `findings` arrays, stamping each entry with its finder name. Ids are already namespaced (`bug-N`, `sec-N`, `perf-N`, `q-N`, `reg-N`, `simp-N`) — no renumbering. Keep the regression finder's `intended` list aside for sanity; it is not a finding. If two find-bug runs were spawned (sensitive mode), prefix the sonnet run's ids with `bug2-` before concatenating so verdicts key unambiguously.

If a finder returned malformed JSON or errored, treat it as `{"findings": []}` and remember its name for the `finder_failures` field passed to sanity. Don't retry — cost.

If the combined list is empty, skip steps 4–5 and emit a short "Approve — no issues found" report directly.

## Step 4 — Spawn verify (serial)

Usually one Agent call with `subagent_type: "code-review-verify"`, passing the combined findings as JSON in the prompt. On a large review, split the findings into batches (for example by slice) and spawn one verifier per batch, in parallel; each verdict set covers only its own batch.

Each verifier returns:

```json
{
  "verified": [
    {"id": "...", "verdict": "confirmed|refuted|uncertain", "reason": "...", "severity_override": "...", "duplicate_of": "..."}
  ]
}
```

`duplicate_of` is optional: a verifier sets it when another finding in its own batch describes the same problem. It is a hint for sanity, which makes the final merge across batches.

## Step 4b — Optional sweep (high-stakes reviews)

Run it when the change touches a security seam (auth, sandbox, trust boundaries, redaction, approvals), when it is a large refactor or redesign, or when the user asks for a sweep or a high-stakes review. Skip it otherwise.

1. One Agent call with `subagent_type: "code-review-sweep"`. Pass the diff pointers and the Step 1 context, plus every finding with its verdict and the verifier's reason: confirmed, uncertain **and refuted** (so it doesn't re-raise the same false positives). A sweep agent once switched branches in its last minute and contaminated the verifiers that ran after it, so:
   - **Committed review target** (a branch range, a PR, specific commits): run it with `isolation: "worktree"`, and make the brief's first step `git checkout --detach <reviewed sha>` inside its own worktree, then `git rev-parse HEAD` to confirm it; the brief allows that one checkout, in the sweep's own worktree only. A fresh worktree doesn't start at the branch under review (one came up at the default branch's tip, the commit the session started on), so there is nothing to check before launch.
   - **Uncommitted changes**: don't isolate it. A fresh worktree starts at a commit, never at the working tree, so it would quietly sweep other code. Point it at the working tree and rely on its read-only rule.
   - Either way, check `git branch --show-current` and `git status` when it returns, before trusting anything later.
2. If it returns findings (`sw-N`), spawn one more `code-review-verify` on those findings only.
3. One sweep per review, never a loop. If the sweep turns up a lot (several confirmed variants of a major finding, say), that is a reason for another full round, and the orchestrator's call; it doesn't trigger a second sweep.

## Step 5 — Spawn sanity (serial)

One Agent call with `subagent_type: "code-review-sanity"`, always exactly one however many verifiers ran. Pass:

- The combined findings (with bodies), including the sweep's when it ran.
- Every verifier's verdicts, concatenated, including the sweep verify's.
- The list of finder failures from step 3.
- The regression finder's `intended` list, and the sweep's `coverage` note when it ran.

Sanity drops refuted findings, applies severity overrides, clusters duplicates across all batches, re-reads source for each merged finding's `fix` (marking it `unchanged` / `refined` / `unverifiable`), and renders the final user-facing markdown. Its counts come from its own merged list, so the summary prose can't drift from the tally.

## Step 6 — Return the report

Emit sanity's markdown verbatim to the user. Do NOT wrap it in commentary — the report is self-contained and includes any pipeline-failure notes inline.

When the report becomes a GitHub review, map the pipeline's severities to the review's: critical → High, major → Medium, minor and nit → Low (Low items go in collapsed sections).

Pre-existing findings are the maintainer's decision, never dropped silently. On the maintainer's own branch, the usual rule is to fix them in place when the fix is bounded. On someone else's PR, they go to the maintainer rather than into the contributor's review.

If sanity itself errored or returned nothing, fall back to a minimal report built from the confirmed and uncertain findings (refuted ones dropped, severity overrides applied, no merging), prepended with:

> ⚠ Pipeline note: sanity did not complete normally; the report below skips merging and fix-verification.

## Parallelism and cost

- Wall clock ≈ max(finders) + max(verifiers) + sanity, plus sweep + one more verify when the sweep runs. Finders run in parallel, and so do verifiers when there are several; sweep and sanity are serial.
- Token cost ≈ 8–10× a single-agent review. Deliberate — verify removes hallucinated claims, sanity merges overlap and tightens fixes before they reach the user.
- A tiny diff still gets all six finders; they finish fast on small diffs, and the regression and simplification finders are the ones that catch what a small fix drags along.

## Invocation hints

- User says "review this" / "code review" → full pipeline.
- User says "quick review" / "sanity check" → 2-finder short pipeline (bug + quality), still run verify + sanity. Only on that explicit request; the default is all six.
- User says "sensitive" / "involved" / hands you risk angles → spawn `find-bug` TWICE in
  the step-2 batch: one opus run whose brief lists ALL the angles as numbered focus areas
  (one run total — orientation is the cost, angles are additive), plus one `model: "sonnet"`
  run on a neutral brief as an independent variance sample. Other finders stay single-run.
- User says "sweep" / "high stakes", or the change touches a security seam or is a large refactor → full pipeline plus the Step 4b sweep.
- User says "security review" → delegate to the `security-review` skill instead of this pipeline.

## Why this is a command, not an agent

The `code-reviewer` agent still exists in `~/.claude/agents/` as a single-agent fallback for callers (other agents, legacy call sites) that invoke it by name. Those callers get the old single-pass behavior — which is fine, just less robust.

When a human invokes `/review`, we want the full multi-stage pipeline, and running it from the top-level scope is the only way to spawn the finders in parallel given the "agents can't spawn agents" constraint in this harness.
