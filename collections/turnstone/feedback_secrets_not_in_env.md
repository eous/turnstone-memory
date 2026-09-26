---
name: Secrets belong in config.toml, not env
description: "Placing turnstone-server/console secrets (JWT, DB URL, API keys): config.toml, never env since the in-process agent can dump env; channel CLI env accepted."
type: feedback
---
JWT secret, Postgres URL (with password), and LLM API keys must be configured via TOML — `[auth]
jwt_secret`, `[database] url`, `[api] api_key` — not through EnvironmentFile / `os.environ`.

**Why:** turnstone-server runs an LLM agent with tool access. A prompt-injection attack against that agent gets to anything in the process env via a single tool call (`bash -c 'env'`, `subprocess.check_output(['env'])`, `cat /proc/self/environ`). Subprocesses inherit env automatically — there's no opt-out. Putting secrets in a TOML file the application reads at startup keeps them out of `os.environ`. The attacker now has to know the path AND have a tool that reads files AND choose to read it instead of dumping env. Substantially higher bar.

**How to apply:**
- For systemd / production deployments, *always* put secrets in `config.toml` (mode `0640 root:turnstone`).
- The shipped systemd units in `deploy/systemd/` already do this — don't regress them.
- If a user asks "can we just put the JWT secret in the env file?" — push back with the threat model. Don't quietly comply.
- **Correction (verified 2026-07-06):** the channel CLI (`turnstone/channels/cli.py`) is env-var-only across the board — JWT secret, DB backend/url/path, AND Discord/Slack tokens all come from `os.environ.get(...)` (`TURNSTONE_JWT_SECRET`, `TURNSTONE_DB_URL`, `TURNSTONE_DB_BACKEND`, `TURNSTONE_DB_PATH`, `TURNSTONE_DISCORD_TOKEN`, `TURNSTONE_SLACK_TOKEN`/`_APP_TOKEN`); there is no `config.toml` reading path in that file, and no commit history shows one ever existing. (An earlier version of this memory claimed a May-2026 patch moved JWT/DB to TOML for the channel CLI — that claim doesn't match the code or the git log; treat it as wrong, not stale.)
- The env path stays in code as a fallback for docker-compose deploys (operator preference). Don't
  remove it.
