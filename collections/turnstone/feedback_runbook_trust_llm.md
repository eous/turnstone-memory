---
name: Runbooks should state requirements, not inline shell/Python scripts
description: "Writing agent-readable runbook prose (deploy/systemd/README.md): state the requirement and trust the LLM; inline code only for what it would miss."
type: feedback
---
When writing prose meant to be read by an LLM agent driving a workflow (install runbooks, multi-node
procedures, etc.), state the requirement and let the LLM compose the implementation. Don't inline:

- Shell loops to fetch files (LLM knows curl, dirname, for-loops)
- Full Python scripts to generate configs (LLM can write `secrets.token_hex(32)` etc. given the goal)
- Distro-specific firewall syntax for `ufw` / `firewalld` / `nft` / `iptables` (mention the families exist, list the failure mode, let the LLM pick)
- SSH / rsync command sequences (LLM knows the idioms)
- TOML escape function source (state the constraints, e.g. "escape control chars", don't reproduce the function)

**Why:** the LLM following the runbook is going to derive the right command from the goal anyway — inlining the script just adds bytes to the runbook without changing the outcome. It also makes the runbook brittle (distro variation, version drift, host-specific paths) and trains the LLM to copy-paste rather than think.

**How to apply:**
- Default to "describe the requirement in 1–2 sentences."
- Inline code ONLY when there's something subtle the LLM is likely to miss (e.g., the exact `host turnstone turnstone 127.0.0.1/32 scram-sha-256` line for `pg_hba.conf` is concrete enough to be worth stating verbatim — but the surrounding "open the file, add the line, reload postgres" is obvious).
- The user has corrected this pattern in turnstone's `deploy/systemd/README.md` three times: firewall commands, the inlined `install_config.py` script, and a curl loop for fetching unit files. Each correction was right.
- Watchword: if the runbook section is shorter than the corresponding code block, the code block is doing the wrong job.
