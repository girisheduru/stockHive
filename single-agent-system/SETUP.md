# Single Agent System Setup (Telegram Single-Ticker)

This setup follows the same registration style as `stockhive-openclaw-setup-fixed.md`.

## 1. Prerequisites

Make sure the base StockHive system is already present and configured:
- `agent-system/` exists
- MCP config exists at `agent-system/mcps/mcp-config.json`
- env vars are configured (Alpha Vantage, Nasdaq Data Link, News API, Telegram)
- OpenClaw daemon is running (persistent agent stays alive and waits for inbound events)

## 2. Install and Associate Telegram Credentials

Collect these values from the user first:

```text
Please provide:
1. SINGLE_TELEGRAM_BOT_TOKEN:
2. SINGLE_TELEGRAM_CHAT_ID:
3. SINGLE_TELEGRAM_MESSAGE_THREAD_ID (optional):
4. MAX_SUBAGENT_RUNTIME_MIN (optional; default 5):
```

Create the single-agent env file:

```bash
cp single-agent-system/.env.example single-agent-system/.env
```

From repo root run:

```bash
bash single-agent-system/install.sh
```

This installer asks for:
- `SINGLE_TELEGRAM_BOT_TOKEN`
- `SINGLE_TELEGRAM_CHAT_ID`

and writes:
- `single-agent-system/.env`

Note: the base system env file (`agent-system/config/.env`) is intentionally **not modified** so both systems can coexist.

## 3. Confirm files

```bash
ls single-agent-system
ls single-agent-system/agents
ls single-agent-system/runtime
ls single-agent-system/scripts
```

Expected key files:
- `single-agent-system/agent-system.json`
- `single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md`
- `single-agent-system/runtime/telegram-single-run-input.json`
- `single-agent-system/scripts/extract_ticker.py`
- `single-agent-system/install.sh`
- `single-agent-system/.env.example`

## 4. Load Env

```bash
set -a
source agent-system/config/.env
source single-agent-system/.env
set +a
```

Because the single-agent env uses `SINGLE_*` variable names, sourcing both files will not overwrite the base Telegram settings.

## 5. Register Components Individually (No `/agents register`)

This single-agent flow is designed to reuse existing components from the original `agent-system`.

First check what already exists:

```bash
openclaw agents list
openclaw mcp list
```

If any of these are missing, stop and register them before continuing:

- `stockhive-telegram-trigger-orchestrator`
- `technical-analyst`
- `fundamental-analyst`
- `sentiment-analyst`
- `telegram-publisher`
- `telegram-publisher-single`
- MCP servers: `yfinance-mcp`, `alpha-vantage-mcp`, `nasdaq-data-link-mcp`, `news-api-mcp`, `telegram-bot-mcp`

If these already exist, do not add them again:
- `technical-analyst`
- `fundamental-analyst`
- `sentiment-analyst`
- `telegram-publisher`
- MCP connections from `agent-system/mcps/mcp-config.json`

Always add only the new orchestrator:

```bash
openclaw agents add stockhive-telegram-trigger-orchestrator \
  --workspace "$PWD" \
  --non-interactive
```

Only if missing, add the shared specialists:

```bash
openclaw agents add technical-analyst \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add fundamental-analyst \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add sentiment-analyst \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add telegram-publisher \
  --workspace "$PWD" \
  --non-interactive
```

```bash
openclaw agents add telegram-publisher-single \
  --workspace "$PWD" \
  --non-interactive
```

Only if MCPs are not already connected, run:

```bash
python3 - <<'PY'
import json, subprocess

cfg = json.load(open('agent-system/mcps/mcp-config.json'))
for name, server in cfg['mcpServers'].items():
  subprocess.run(['openclaw', 'mcp', 'set', name, json.dumps(server)], check=True)
print('MCP servers registered:', ', '.join(cfg['mcpServers'].keys()))
PY
```

Optional: configure a **separate** Telegram MCP for the single-agent flow (recommended if you want a different bot token from the group/scheduled system).

> **Note:** You do NOT need a separate `mcp-config.json` inside `single-agent-system/`.
> MCP servers live in OpenClaw's global config and are registered by name (CLI). For the trigger flow we use: `telegram-bot-mcp-trigger`.

```bash
python3 - <<'PY'
import os, json, subprocess
from pathlib import Path

def load_env(path):
  out={}
  for line in Path(path).read_text().splitlines():
    line=line.strip()
    if not line or line.startswith('#') or '=' not in line:
      continue
    k,v=line.split('=',1)
    out[k.strip()]=v.strip().strip('"').strip("'")
  return out

e=load_env('single-agent-system/.env')
server={
  "command":"npx",
  "args":["-y","@openclaw/telegram-bot-mcp"],
  "env":{
    "TELEGRAM_BOT_TOKEN": e.get('SINGLE_TELEGRAM_BOT_TOKEN',''),
    "TELEGRAM_CHAT_ID": e.get('SINGLE_TELEGRAM_CHAT_ID',''),
    **({"TELEGRAM_MESSAGE_THREAD_ID": e.get('SINGLE_TELEGRAM_MESSAGE_THREAD_ID','')} if e.get('SINGLE_TELEGRAM_MESSAGE_THREAD_ID') else {})
  },
  "description":"Publishes one-shot chat replies for stockhive-telegram-trigger-orchestrator (personal bot)."
}
subprocess.run(["openclaw","mcp","set","telegram-bot-mcp-trigger",json.dumps(server)], check=True)
print('Saved telegram-bot-mcp-trigger')
PY
```

Note: If running the MCP registration step causes MCP env values to revert to placeholders like `${ALPHA_VANTAGE_API_KEY}`, re-apply the real values in your OpenClaw config (`~/.openclaw/openclaw.json`) under:

```text
mcp.servers.alpha-vantage-mcp.env.ALPHA_VANTAGE_API_KEY
mcp.servers.nasdaq-data-link-mcp.env.NASDAQ_DATA_LINK_API_KEY
mcp.servers.news-api-mcp.env.NEWS_API_KEY
mcp.servers.telegram-bot-mcp.env.TELEGRAM_BOT_TOKEN
mcp.servers.telegram-bot-mcp.env.TELEGRAM_CHAT_ID
mcp.servers.telegram-bot-mcp.env.TELEGRAM_MESSAGE_THREAD_ID  (optional)
```

Verify:

```bash
openclaw agents list
openclaw mcp list
```

## 6. Runtime behavior (always-on, no schedule)

When a Telegram message arrives, trigger `stockhive-telegram-trigger-orchestrator` immediately with event payload:
- `chat_id`
- `message_id`
- `from_user_id`
- `message_text`

This flow is event-driven and replies to the same chat/person context. It does not use polling or cron.

### 6.1 Bind Telegram inbound messages to this agent (auto-trigger)

To route inbound Telegram messages to this agent:

```bash
openclaw agents bind --agent stockhive-telegram-trigger-orchestrator --bind telegram
```

## 7. Tag Skills on Agents (so the dashboard shows associations)

Update the agent entries in your OpenClaw config:

```bash
python3 - <<'PY'
import json, os

p = os.environ.get('OPENCLAW_CONFIG_PATH') or os.path.expanduser('~/.openclaw/openclaw.json')
cfg = json.load(open(p))

skills_by_agent = {
  'technical-analyst': ['technical-indicators'],
  'fundamental-analyst': ['fundamental-snapshot'],
  'sentiment-analyst': ['sentiment-analyzer'],
  'telegram-publisher': ['telegram-formatter'],
  'telegram-publisher-single': ['telegram-formatter'],
  # helpful for visibility:
  'stockhive-telegram-trigger-orchestrator': [
    'technical-indicators',
    'fundamental-snapshot',
    'sentiment-analyzer',
    'telegram-formatter',
  ],
}

for a in cfg.get('agents', {}).get('list', []):
  aid = a.get('id')
  if aid in skills_by_agent:
    a['skills'] = skills_by_agent[aid]

json.dump(cfg, open(p, 'w'), indent=2)
print('Updated agent.skills in', p)
PY
```

## 8. Manual test

Send a message in Telegram like:
- `Analyze NVDA`
- `AAPL`
- `check msft`

Then trigger:

```bash
openclaw agent --agent stockhive-telegram-trigger-orchestrator \
  --message 'Read and follow single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md.

{"trigger":"telegram_webhook_event","event_payload":{"chat_id":"YOUR_CHAT_ID","message_id":"12345","from_user_id":"777777","message_text":"Analyze NVDA"}}' \
  --json
```

## 9. Runtime compatibility note

If your OpenClaw version does not fully apply markdown identity on `agents add`, prefix the run prompt with:

```text
Read and follow single-agent-system/agents/stockhive-telegram-trigger-orchestrator.md.
```

This is the same compatibility fallback used in `stockhive-openclaw-setup-fixed.md`.

Do the same for specialists if needed:

```text
Read and follow agent-system/agents/technical-analyst.md.
Read and follow agent-system/agents/fundamental-analyst.md.
Read and follow agent-system/agents/sentiment-analyst.md.
Read and follow agent-system/agents/telegram-publisher.md.
Read and follow agent-system/agents/telegram-publisher-single.md.
```
