# StockHive + OpenClaw Registration (Single Source of Truth)

Use this file to register and run StockHive with OpenClaw.

It covers two *separate* flows:
1) **Group / scheduled daily run** (Nasdaq batch workflow → posts to Telegram group + thread)
2) **Single-agent trigger** (Telegram DM trigger → replies back via a separate bot/MCP)

> Rule: **Never mingle Telegram credentials** between these flows.

---

## 0) Required inputs (group/scheduled run)

Set these in `agent-system/config/.env` (do not paste secrets into chats/logs):

Required:
- `ALPHA_VANTAGE_API_KEY`
- `NASDAQ_DATA_LINK_API_KEY`
- `NEWS_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID` (group id like `-100...`)
- `TELEGRAM_MESSAGE_THREAD_ID` (topic/thread id)

Optional:
- `TIMEZONE` (default `Europe/London`)
- `MAX_SUBAGENT_RUNTIME_MIN` (default `5`)

---

## 1) Register MCP servers (group/scheduled)

MCP server templates live in: `agent-system/mcps/mcp-config.json`.

Register them into OpenClaw (global config) using:

```bash
python3 - <<'PY'
import json, subprocess

cfg = json.load(open('agent-system/mcps/mcp-config.json'))
for name, server in cfg['mcpServers'].items():
  subprocess.run(['openclaw', 'mcp', 'set', name, json.dumps(server)], check=True)
print('MCP servers registered:', ', '.join(cfg['mcpServers'].keys()))
PY
```

Then reload secrets snapshot:

```bash
openclaw secrets reload
```

---

## 2) Register agents (group/scheduled)

From repo root:

```bash
openclaw agents add stockhive-orchestrator --workspace "$PWD" --non-interactive
openclaw agents add data-fetcher --workspace "$PWD" --non-interactive
openclaw agents add technical-analyst --workspace "$PWD" --non-interactive
openclaw agents add fundamental-analyst --workspace "$PWD" --non-interactive
openclaw agents add sentiment-analyst --workspace "$PWD" --non-interactive
openclaw agents add telegram-publisher --workspace "$PWD" --non-interactive
```

Verify:

```bash
openclaw agents list
openclaw mcp list
```

---

## 3) Scheduled job (group/scheduled)

Create/verify cron job named **StockHive Nasdaq Daily Run** to run as agent `stockhive-orchestrator` and announce to your **Telegram group**.

Important:
- Cron `delivery.announce` targets the group chat id.
- The *actual* publish into the configured thread is done by `telegram-publisher` via `telegram-bot-mcp` using `TELEGRAM_MESSAGE_THREAD_ID`.

---

## 4) Single-agent trigger (Telegram DM → reply)

Single-agent config lives in `single-agent-system/.env` using *separate* vars:

- `SINGLE_TELEGRAM_BOT_TOKEN`
- `SINGLE_TELEGRAM_CHAT_ID`
- `SINGLE_TELEGRAM_MESSAGE_THREAD_ID` (optional)

Register a separate MCP (global) for this flow:

```bash
python3 - <<'PY'
import json, subprocess
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
  "description":"Telegram MCP for stockhive-telegram-trigger-orchestrator (personal bot)."
}
subprocess.run(["openclaw","mcp","set","telegram-bot-mcp-trigger",json.dumps(server)], check=True)
print('Saved telegram-bot-mcp-trigger')
PY
openclaw secrets reload
```

Bind inbound Telegram messages to the trigger agent (one-time):

```bash
openclaw agents bind --agent stockhive-telegram-trigger-orchestrator --bind telegram
```

> Note: You do **not** need a separate `mcp-config.json` inside `single-agent-system/`.

---

## 5) Python env loading helper (no runtime prompting)

If you have Python scripts that must read a repo `.env`, use:

`agent-system/scripts/require_env.py`

This ensures:
- `.env` is loaded from `agent-system/config/.env`
- missing keys fail fast with a clear error
- no scheduled run ever prompts a Telegram group for secrets
