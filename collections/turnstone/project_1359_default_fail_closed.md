---
name: project_1359_default_fail_closed
description: "#1359 (a load moves the default model): 2026-10-13 rulings (fail closed, stored default, hold on reopen, delete failover chain), two-PR split, local plan."
metadata:
  node_type: memory
  type: project
  modified: 2026-10-14T21:36:24.007Z
---

#1359: when the configured default model is missing from a registry load, nodes route new
sessions to another alias. Scoped 2026-10-13 against dev @ 4593eefb. The plan is the LOCAL
untracked note `docs/design/1359-default-fail-closed.md` in the main checkout, and the code map is
`docs/design/1359-dataflow.md` (the plan's S-numbers point at the map's Surprises section).
Re-check line numbers before coding ([[project_velocity]]).

**Rulings (maintainer, 2026-10-13):**
- Delete the substitution. Anything that needs a default or task model that isn't loaded fails
  with a message naming the alias and the remedy (fix it, or choose another model / `/model`).
  No split between "left out of the load" and "deleted, disabled or misspelled".
- D1: delete the `[model] fallback` failover chain, in PR 2.
- D2: reopening a workstream whose model isn't loaded opens it but holds model turns with the
  `/model` message until the model loads again or the user switches; saves keep the original
  alias. The same state replaces the live-session send-anyway latch once the chain is gone.
- D3 (the maintainer's own variant): the first model added becomes the stored default
  (`model.default_alias`), and an upgrade pins the current default. With nothing stored or
  configured, the pick is the first defined model, never the first loaded. Every automatic pick
  takes chat models only (`serves_chat`: no reranker, no dedicated speech model), because the
  stored setting outranks every node's config.toml default. Final pin rule (third revision the
  same day, after pin-at-first-Sync and pin-on-any-refresh): the console stores the default only
  when an add or edit gives the cluster its first enabled chat model, and only when no global row
  exists (cleared or not); Sync, timers, deletes and other edits never pin, so a Settings-tab
  Reset stays reset. Nothing is pushed; nodes read the setting with the model definitions, at a
  Sync or at their secret-store timer tick, which now reloads changed settings. Accepted gap: an
  unrelated settings push between the pin and the Sync sends the default early. The
  maintainer's principle: a console-managed cluster's default is uniform, so the setting
  outranking node config.toml is by design.
- D4: `judge.model` stays out of scope. The channel half was reversed the same day: Slack honors
  `channels.default_model_alias` like Discord (it never passed a model, though the Roles tab says
  the setting covers it), and a channel model that isn't loaded fails closed, in PR 1.
- Routing is read at use time (`registry.effective_default(config_store)` and friends), never
  baked into the registry: baking was the source of the stale-override bug.
- Unsynced aliases (same day): a workstream naming an alias its node hasn't loaded (added since
  the last Sync) fails; a settings change never loads models implicitly, and saves aren't refused.
- Health (same day, "Report degraded"): a node is `degraded` while its default model isn't
  loaded; one summary feeds `/health`, the snapshot and `health_changed`, and the console stores
  the node's verdict. `/health` stays 200 and the Docker probe accepts `degraded`.
- Review round 1 (same day): fixes done in-session; an `admin.models`-only principal setting the
  cluster default through the pin is accepted and documented (it can already change the default
  model's endpoint); health gets a backstop on the 10 s aggregate tick; the channel bots' cached
  channel model lives 30 s. Four nits dropped (route retry, pin race, guard scan, Slack DM fetch);
  the plan's "Review round 1" section lists every fix.
- Review round 2 (same day): coordinators ignore `resume_ws` (an opt-in `create_supports_resume`,
  set only on the node's interactive mount); the coordinator 503 is one neutral text; the CLI
  wires the reopen retry's default reader (the #979 race test stays); a fork whose source model's
  client can't be built fails, as a reopen does. The channel cold-cache substitution is #1377;
  the reopen hint for a retryable saved model waits for PR 2's hold.
- PR 1 is #1378; PR 2 is #1383 (one commit on dev after PR 1's rebase-merge). PR 2's work was
  listed in the issue body's PR 2 section and in the
  local plan's "PR 2 scope" and "PR 2 implementation design" sections; PR 2's branch is
  `fix/1359-session-hold` (off `d3dc6f3d`), its consumer map `docs/design/1359-pr2-hold-map.md`.
- PR 2 rulings (maintainer, 2026-10-13): (1) a fork whose source model isn't loaded runs on the
  model its request names (channels pass theirs; that counts as the switch), else it is held like
  a reopen; (2) when neither the saved model nor the default is loaded, the reopen refuses as PR 1
  does (no stand-in picker); (3) UI: the refusal message and `/model` are the indicator for now,
  and the "not loaded" chip goes to a follow-up issue, amending D2's "the UI shows it as
  unavailable". A side-agent note the maintainer relayed: the held session's binding must make
  calls impossible (a client that refuses), not rely on every call site checking
  ([[feedback_designs_that_need_no_memory]]). (4, during PR 2's review) chat channels' recovery
  forks almost never name a model (Discord and Slack thread recovery pass none; Slack DMs only
  the channel model when set), so they hold: keep the code and document that such chat
  conversations wait for their model (no "as the channels do" claim). History rule (maintainer):
  the ledger is append-only except that the chain may be cut and its tail dropped, so `/retry`
  (cut at the last user turn, re-send) stays valid. (5, 2026-10-14) chat users can't run `/model`,
  so a held chat conversation's refusal is channel-specific, like the channels' reply when a
  resumption fails ("Ask a Turnstone admin to check it in the Models tab").
- PR 2 fix-round review rulings (maintainer, 2026-10-14): (6) a fork naming a model adopts exactly
  as a reopen does, then switches by name through the `/model` path (`switch_to`); the
  `keep_built_model` flag is deleted (it needed a new race guard every round); (7) a fork whose
  source model is skipped only temporarily (retryable, e.g. secret store down) holds instead of
  switching, so a Slack DM doesn't move to the channel model for good during an outage; (8) the
  client type stays unpersisted (a chat workstream reopened outside channel recovery gets the
  web wording; accepted); (9) refresh the model at the start of every model round and before
  each creation retry, closing the mid-send stall on a closed client.
- PR 2 full-surface review rulings (maintainer, 2026-10-14): (10) a live session whose reloaded
  model's client can't be built holds (no sending on the client the reload closed; the rebind
  remedy branch of `_format_backend_error` goes, leaving one remedy table); (11) a held session
  retries a failed build once per registry change, not per send (an environment-only fix needs a
  model edit or restart: an unchanged Sync is a no-op that doesn't bump the generation); (12) the
  retry ladder re-reads the health tracker with the lane on a mid-ladder rebind and charges an
  exhausted ladder to the last attempt's tracker; (13) a row saved before model aliases were
  recorded (backend model id only) holds on that id instead of running on the default, with NO
  alias (follow-up after a side-agent note): nothing is matched to it, not even an alias named
  like the id, so only `/model` ends it, and saves keep the row's shape.
- Model-facing errors say why and suggest a retry only when retryable, never another model
  ([[feedback_model_errors_never_suggest_switching]]).
- Two PRs: PR 1 routing (one derivation, errors and their delivery, coordinator gate, CLI, boot,
  task model checked before approval, the upgrade pin); PR 2 sessions (delete the chain, the hold).

**Why:** the substitution predates 1.7 (#304) with no ruling, its rule was copied into about 14
places that already disagreed, and secret references (#1329) made a store outage or a refused
reference move sessions silently, possibly from a local model to a hosted one. The code map showed
that switching a reopened workstream to the default with a notice makes the move permanent (the
next settings save, including the model's own skill load, writes the default) and runs watch
restores unattended on a model nobody chose.

- The upgrade pin may override a host's config.toml default; accepted, with a CHANGELOG note.
- config.toml stays first-class: `[models.*]` and `[model] default` keep working on every host,
  and the maintainer stressed CLI users. The CLI reads no stored setting, so its default stays
  `[model] default`, else the alias `default`, else the first `[models.*]` entry in the file.

**How to apply:** start from the plan. User-facing errors carry no loader reason: reasons name
secret reference paths and mounts, some skips record none, and a node's skip reasons are frozen at
boot. The maintainer left the split to us (10-13); PR 1 also carries a guard (the console refuses
to delete, disable or rename a model that a fail-closed routing setting names, so a routine model
swap can't silently block every new Slack conversation) and a Slack/Discord reply for the new
`model_not_loaded` create code. The issue body's Plan section mirrors this. Related:
[[project_1292_alias_settings]],
[[feedback_designs_that_need_no_memory]], [[feedback_push_back]].
