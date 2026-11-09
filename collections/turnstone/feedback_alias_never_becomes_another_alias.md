---
name: feedback_alias_never_becomes_another_alias
description: "Any model role or alias path: a set alias never turns into another alias when it can't run; picking reads settings only; fix the shape, don't add a flag per consumer."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-01T20:22:54.585Z
---

A model alias never falls back to a different model alias. Choosing the alias reads settings only,
never what is loaded; the chosen alias then binds, or that role can't run. Nothing goes back and
picks again. An empty setting inheriting another role's or the session's alias is decided by
configuration alone, so it is a separate question, not a failover.

**Why:** the maintainer stopped a judge patch on #1529 (2026-10-31) as duct tape. It kept the
judge's shape, where the session binding is assigned first and a failed resolve leaves it in place,
and added an "unavailable" flag with early returns on top. This reverses #1359's D4, which left
`judge.model` out of scope ([[project_1359_default_fail_closed]]).

**How to apply:** when a role's alias can't run, look for a default-then-overwrite binding or a
`has_alias` check inside selection, and remove that shape rather than guarding each consumer. Prefer
the primitive held sessions use, `RefusingModelClient`, so calls are impossible by structure
([[feedback_designs_that_need_no_memory]]). Empty inheritance stays (ruling, 2026-10-31): empty
`judge.output_guard_model` uses `judge.model`, and empty `judge.model` uses the session's model.

Speech-to-text follows the rule (#1536; ruling 2026-11-08, on #1572): when the chat model can't
take audio and `audio.stt_model_alias` is set, an alias that can't run gives a placeholder naming
it, and an empty transcript gives a "found no speech" placeholder. Neither goes to perception, which
takes audio only when the STT setting is empty. The placeholder keeps the alias name even though
`model.hide_utility_aliases` hides it from the lists agents see.

Keeping an alias to one role stops at hiding (ruling, 2026-11-01): `model.hide_utility_aliases` keeps
it out of the lists agents see, and nothing refuses it at spawn. The maintainer judged that enough
for about 99% of cases and simpler than another branch, so don't propose a hard judge-only guard.

Trace a report against the current release only unless told otherwise; the #1529 reporter runs
1.9.2, where the old chain is already gone.

Check what a reported symptom traces to before promising that removing a fallback fixes it. On
#1529 no code moves a child to the judge alias: the coordinator model picks it from
`list_nodes.model_aliases`. That list holds healthy aliases only, so a backend marked degraded
after `health.failure_threshold` consecutive failures drops off it, which reads as a fall-over
without being one.
