# StockHive — Registration Runbook (reworked)

This runbook describes a clear, ordered sequence to register every component declared in this repository with OpenClaw and to validate the runtime. Run each step in sequence. When a command must be sent from the OpenClaw Web UI (slash commands), the runbook notes that explicitly.

Important: the workspace root for these commands is /data/.openclaw/workspace. The agent composition manifest is at stockHive/agent-system.json.

---

## Quick checklist (before you start)

- Confirm the manifest exists: /data/.openclaw/workspace/stockHive/agent-system.json
- Confirm secrets file is present and filled with real values: /data/.openclaw/workspace/stockHive/agent-system/config/.env
  - Required: ALPHA_VANTAGE_API_KEY, NASDAQ_DATA_LINK_API_KEY, NEWS_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (must start with -100)
- Have your Gateway URL and token ready (default HTTP UI: http://localhost:18789, WS: ws://127.0.0.1:18789). Keep OPENCLAW_GATEWAY_TOKEN handy.

If any of the above are missing, pause and provide them now.

---

## Step A — Load .env into the environment (optional but recommended)

If you plan to run registration from a container or the host shell, export the repo .env so MCPs and CLI see the keys.

Option: load into current shell (no container):

set -a
. /data/.openclaw/workspace/stockHive/agent-system/config/.env
set +a

Or pass the file into a container with --env-file (examples later).

---

## Step B — Register MCP server definitions into OpenClaw config

This step writes the declared MCP servers into OpenClaw's config so you can later `mcp serve` or `mcp connect` them. This is safe to run from the host shell.

Run (host shell):

openclaw mcp set yfinance-mcp '$(cat stockHive/agent-system/mcps/mcp-config.json | jq .mcpServers.yfinance-mcp)'
openclaw mcp set alpha-vantage-mcp '$(cat stockHive/agent-system/mcps/mcp-config.json | jq .mcpServers."alpha-vantage-mcp")'
openclaw mcp set nasdaq-data-link-mcp '$(cat stockHive/agent-system/mcps/mcp-config.json | jq .mcpServers."nasdaq-data-link-mcp")'
openclaw mcp set news-api-mcp '$(cat stockHive/agent-system/mcps/mcp-config.json | jq .mcpServers."news-api-mcp")'
openclaw mcp set telegram-bot-mcp '$(cat stockHive/agent-system/mcps/mcp-config.json | jq .mcpServers."telegram-bot-mcp")'

Notes:
- These commands store the MCP server entries. They do not start the servers. Starting relies on `mcp serve` or OpenClaw's `mcp connect` helper later.
- If jq is not available, use the equivalent JSON object from the file or run openclaw mcp set with an editor.

---

## Step C — Register the agent system manifest (use the Web UI)

This step registers orchestrator, subagents, skills, scheduled tasks, and script references. It must be invoked from the OpenClaw Chat (Web UI) as a slash command so the Gateway performs the correct authenticated flow.

How to run (recommended):

1. Ensure your SSH tunnel (if remote) is open: ssh -L 18789:localhost:18789 user@vps
2. Open the Gateway UI in a browser: http://localhost:18789
3. Authenticate using your OPENCLAW_GATEWAY_TOKEN when prompted.
4. In the OpenClaw Chat message box (not the shell), paste exactly:

/agents register /data/.openclaw/workspace/stockHive/agent-system.json

5. Send the message and copy the UI response. Paste it here for verification.

Why the Web UI: programmatic JSON-RPC registration attempts must complete a Gateway challenge/response; the UI already handles that. If you must register programmatically, use register_manifest_ws.py from within a session that can satisfy the Gateway handshake (advanced).

---

## Step D — Verify registration

After the manifest registers successfully, run these in the host shell and paste outputs:

openclaw agents list --json
openclaw skills list --json
openclaw tasks list --json
openclaw mcp list --json

Expect to see the orchestrator (stockhive-orchestrator), the ephemeral subagents, the five skills, the scheduled task, and the five MCP entries.

---

## Step E — Start / connect MCP servers

If the MCP definitions are present and your .env contains keys, start them:

openclaw mcp serve --claude-channel-mode auto

Or connect the configured MCPs (declarative):

openclaw mcp connect ./stockHive/agent-system/mcps/mcp-config.json

Verify:

openclaw mcp list

Each server should show status: running. If a server fails, check its env vars in /data/.openclaw/openclaw.json and agent-system/config/.env.

---

## Step F — Smoke-test ephemeral subagents

Run these from the host shell (they spawn ephemeral subagents and return JSON):

openclaw agent run data-fetcher --input '{"universe_file":"stockHive/agent-system/config/nasdaq100-tickers.json","selection_mode":"deterministic_daily_random_sample","target_count":10,"must_return_exactly":true}'

openclaw agent run technical-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'

openclaw agent run fundamental-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'

openclaw agent run sentiment-analyst --input '[{"ticker":"AVGO"},{"ticker":"AMD"}]'

Check outputs follow the SKILL.md contracts (JSON only, fields present).

---

## Step G — Run the full orchestrator pipeline (one-shot)

openclaw task run nasdaq-daily-top5-buys

Watch the orchestrator logs in the UI or fetch the task run output. Confirm the run completes through all pipeline stages and returns the JSON summary including telegram_message_id (if published).

If you prefer a dry run without Telegram publish, edit the scheduled task or pass a flag to disable publish in the orchestrator input.

---

## Step H — Enable the schedule (optional)

openclaw schedule enable nasdaq-daily-top5-buys

This will run the pipeline at the configured cron (weekday 17:00 America/New_York).

---

## Teardown (unregister everything)

openclaw schedule disable nasdaq-daily-top5-buys
openclaw mcp disconnect --all-from ./stockHive/agent-system/mcps/mcp-config.json
openclaw agents unregister ./stockHive/agent-system.json

---

## If something fails — tell me these outputs

- The exact UI response when you ran the slash command (/agents register …)
- openclaw mcp list --json
- openclaw agents list --json
- /data/.openclaw/workspace/stockHive/agent-system/config/.env (confirm which keys are present; do NOT paste secrets here)

If you want, I can run the host CLI registration attempt for you now (programmatic registration usually fails due to Gateway handshake — UI route recommended). Ask me to proceed and indicate whether I should start MCPs and run the orchestrator automatically after registration.

---

End of runbook.
