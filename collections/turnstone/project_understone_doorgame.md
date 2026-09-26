---
name: project_understone_doorgame
description: "Understone (examples/door-game, on main via PR #667): server owns all numbers, model is DM only; never name the inspiring product; no migrations pre-1.0."
metadata: 
  node_type: memory
  type: project
  modified: 2026-07-20T17:02:55.342Z
---

A standalone BBS door-game MCP server built across this session as a turnstone **example** (NOT
core), living at `examples/door-game/`, package `understone`, on branch **`feat/door-game`**.
Started as an easter-egg (the idea that a dynamic BBS door game with a ui:// extension would be fun)
and grew into the canonical demonstration of the right LLM+tools factoring.

## The load-bearing architecture (the whole point)
- **Server owns ALL truth**: tile map, dice, combat, HP/gold/XP, inventory,
  daily turns, persistence (SQLite, single conn, WAL). Deterministic, no LLM
  inside. `combat.py` is PURE. engine/screen/world/persistence/watch/cli/sim are
  stdlib-only; `server.py` is the ONLY module importing mcp/starlette.
- **The model is the Dungeon Master, and ONLY that**: interprets natural
  language → `door_*` tool calls, narrates around the facts the server returns,
  voices NPCs, exercises bounded discretion (`door_bestow` = capped, audited
  largesse). It CANNOT mint a number (gold/xp/hp/dice/loot) the server didn't
  return — the anti-cheat that keeps the shared leaderboard honest. Principle:
  **the model owns fiction without limit; it owns consequence only through
  server adjudication.** The leash is proportional to SHARED stakes (a solo world
  could be far looser than the ranked multiplayer one).
- **Two model seats, separated by time + trust**: play-time DM (in-band,
  can't cheat) vs authoring-time world-builder (out-of-band, writes content packs
  a human reviews + the loader enforces). The Cinder Wastes pack was authored
  COLD by an LLM from AUTHORING.md alone — the dogfood proof.
- Tool surface (9 `door_*`, no per-feature param bloat): join/status/look/move/
  action/log/rank/bestow/help. DM guidance lives in the tool descriptions +
  `door_help` (zero-setup: the schema teaches the model to DM; no pasted prompt).


## Version arc (v0.1→v0.10, all committed on feat/door-game)
v0.1 server+engine; v0.2 the Wyrm (win→legacy reset+Hall+★) + forest events +
Herald feed; v0.3 the Watch (CRT spectator page via FastMCP custom_route) +
richer world; v0.4 authoring pipeline (newpack/validate + generated AUTHORING.md,
worlds-as-data); v0.5 social (ambush PvP w/ sleep rule, inn mailbox, dice);
v0.6 UTF-8 graphics + the WIDTH DISCIPLINE (is_grid_safe: one column, EAW not
W/F, no combining); v0.7 depth (multi-rung dungeon, satchel+death-save, forge,
rare beasts); v0.8 worlds-without-authors (cold-LLM-authored Cinder Wastes +
`worlds` listing + per-pack watch_theme + sim harness whose greedy bot proves
both worlds winnable end-to-end); v0.9 unified colour palette w/ distinct roles
per object type (the road-blends-into-grass fix; `scrub` added so volcanic
cinder isn't green); v0.10 stacking satchel + ore-gated forge (ore won in
combat, not bought) + the vault (ambush-safe, survives legacy reset) +
inventory/gold surfaced on /watch AND door_status.

## Standing state / obligations
- **PR #667 (2026-06-13)** (branch `feat/understone`, 10 commits v0.1→v0.10;
  old `feat/door-game` was rewritten + deleted — see below). Understone now lives
  on **`main`**, so follow-up work branches off main, not the dead feature branch.
- **Early-game balance pass — PR #729**, branch
  `fix/understone-early-balance` off main, BOTH packs. Diagnosed via a fight-economy
  probe over the real `combat.resolve_fight`: a fresh L1 LOST gold on nearly every
  fight it won (heal cost > kill reward), and tier-2 foes in the starter zone could
  ~end a 20-HP hero. Fixes: heal 2→1 g/HP; `starting_gold` 20→37 (exactly the
  cheapest armor + one potion, so the cushion is player-spent agency, not stat
  inflation); tier 2-4 COMMON atk −1 (rares/boss untouched); road glyph `=`→`▒`
  (the `=` only read as a road horizontally, broke into stacked dashes vertically);
  inn rest now refills turns when spent (only at 0, no new field/migration). Two
  reusable insights: (1) **per-pack glyph collision** — Cinder reskins the shade
  ramp (`░`=ash/ground, `▒`=cinder/scrub, `▓`=caldera/wall), so the Vale's `▒` road
  collides there; Cinder's basalt uses `▩` instead. A glyph free in one pack isn't
  free in another — check the pack palette. (2) **sim lone-fail reading** — a sweep's
  single non-clearing seed is a navigation artifact (0 deaths, ~17 fights vs ~290),
  NOT a difficulty wall, and WHICH seed fails shifts as any change reshuffles the RNG
  stream; don't chase 12/12 by nerfing. The rejected symmetric-jitter idea (measured)
  nerfs the player's offense as much as the monster's → lower win rates in even fights.
- **Product-name scrub (2026-06-13)**: the name of the game this pays homage to leaked
  into 4 files + 3 commit messages; the user caught it at the PR gate (it's the
  no-product-names rule, [[feedback_artifact_cleanliness]],
  genre/inspiration references included). Fixed by rewriting the whole branch
  history (filter-branch scoped to main..feat/door-game) → generic phrasing
  ("classic-door-game-style", "the BBS door-game tradition"), reflog-expire +
  gc-prune to purge old objects, new branch `feat/understone`, fresh push. DO
  NOT reintroduce the product name in code/commits/PR — describe the genre, not
  the game.
- **Schema mutates in place, stamp stays 1, NO migrations pre-1.0** (user's
  explicit ruling: no prior data to constrain). The recurring review finding
  "an existing DB crashes on a new column" is REFUTED on this ruling every time
  (v0.2/v0.5/v0.6/v0.10). **1.0 owes a real migration + save-compat story.**
- Build rhythm: each version = a /ship-style slice (implement → focused review
  w/ bug×2+quality finders → apply → gates → commit). Gates (run from
  examples/door-game, pipefail): `.venv/bin/python -m pytest tests/ -q` +
  ruff check + ruff format --check + `mypy understone/`. 419 tests at v0.10.
- Sandbox kills listening servers → render /watch SERVERLESSLY (inline the real
  world.json/state.json payloads into WATCH_HTML as data: URLs, screenshot via
  `google-chrome --headless` on file://). NB foreground `sleep` is blocked.

## Multi-node connection diagnosis

Treat these as separate checks when a containerized node cannot reach an MCP service:

1. **Bind address:** a loopback-only listener is unreachable from another network namespace.
   Configure the listener for the intended isolated test network.
2. **Host validation:** the server's allowed Host headers must match the address and port the
   client uses. Changing the bind address alone may leave an import-time allowlist unchanged.
3. **Container routing:** test from inside the calling container. A configured host-gateway
   alias, service name, and host LAN address can follow different routes.
4. **Firewall:** a timeout and a refused connection indicate different failure paths. Compare
   the failing endpoint with a known reachable test service before changing rules. Any rule
   should be limited to the intended test source and destination.

Use deployment-specific endpoints and explicit Host allowances. An unauthenticated example
server belongs on an isolated test network. These checks describe a debugging method, not the
current configuration of a particular host.
