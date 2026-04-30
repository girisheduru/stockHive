# StockHive + OpenClaw Setup Guide

This guide registers the StockHive agents using the Markdown files already present in the repo under `agent-system/`.

Important: `/agents register ./agent-system.json` is not used here. Instead, each agent is registered from its own Markdown identity file.

---

## 0. Required Inputs

Before setup, collect these values from the user:

```text
Please provide:

1. Alpha Vantage API key:
2. Nasdaq Data Link API key:
3. News API key:
4. Telegram bot token:
5. Telegram chat/channel ID:
6. Time zone for the 5 PM schedule, for example America/New_York or Europe/London:
```

Required environment variables:

```text
ALPHA_VANTAGE_API_KEY
NASDAQ_DATA_LINK_API_KEY
NEWS_API_KEY
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
TELEGRAM_MESSAGE_THREAD_ID   (optional; Telegram topics/thread id)
MAX_SUBAGENT_RUNTIME_MIN     (optional; defaults to 5)
TIMEZONE                     (for the schedule; example: Europe/London)
```

If any of these are missing at runtime, **stop and ask the user for the missing values** before proceeding.

---

## 1. Clone the Repository

```bash
git clone https://github.com/girisheduru/stockHive.git
cd stockHive
```

---

## 2. Install and Initialize OpenClaw

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

Check OpenClaw is available:

```bash
openclaw --help
openclaw status
```

---

## 3. Confirm Repo Files Exist

```bash
ls agent-system
ls agent-system/agents
ls agent-system/skills
ls agent-system/mcps
ls agent-system/scheduled-tasks
```

Expected agent Markdown files:

```text
agent-system/agents/stockhive-orchestrator.md
agent-system/agents/data-fetcher.md
agent-system/agents/technical-analyst.md
agent-system/agents/fundamental-analyst.md
agent-system/agents/sentiment-analyst.md
agent-system/agents/telegram-publisher.md
```

Expected skills:

```text
agent-system/skills/stock-data-fetcher/SKILL.md
agent-system/skills/technical-indicators/SKILL.md
agent-system/skills/fundamental-snapshot/SKILL.md
agent-system/skills/sentiment-analyzer/SKILL.md
agent-system/skills/telegram-formatter/SKILL.md
```

---

## 4. Configure Environment Variables

Create a local `.env` file from the repo example if available:

```bash
cp agent-system/config/.env.example agent-system/config/.env
```

Then edit it:

```bash
nano agent-system/config/.env
```

Or write it directly:

```bash
cat > agent-system/config/.env <<'EOF'
ALPHA_VANTAGE_API_KEY="PASTE_ALPHA_VANTAGE_API_KEY_HERE"
NASDAQ_DATA_LINK_API_KEY="PASTE_NASDAQ_DATA_LINK_API_KEY_HERE"
NEWS_API_KEY="PASTE_NEWS_API_KEY_HERE"
TELEGRAM_BOT_TOKEN="PASTE_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID="PASTE_TELEGRAM_CHAT_ID_HERE"
EOF
```

Load the variables into the current shell:

```bash
set -a
source agent-system/config/.env
set +a
```

### 4.1 If OpenClaw still says “missing env var …”

If you see warnings like:

```text
missing env var "ALPHA_VANTAGE_API_KEY" ...
```

it means the Gateway runtime cannot see your shell environment.

In OpenClaw `2026.4.21`, MCP server `env` values are plain strings, so SecretRefs may not be accepted there. The most compatible fix is:

1) **Ask the user** for the missing values.

2) Inline them into your OpenClaw MCP config (`~/.openclaw/openclaw.json`) under:

```text
mcp.servers.alpha-vantage-mcp.env.ALPHA_VANTAGE_API_KEY
mcp.servers.nasdaq-data-link-mcp.env.NASDAQ_DATA_LINK_API_KEY
mcp.servers.news-api-mcp.env.NEWS_API_KEY
mcp.servers.telegram-bot-mcp.env.TELEGRAM_BOT_TOKEN
mcp.servers.telegram-bot-mcp.env.TELEGRAM_CHAT_ID
mcp.servers.telegram-bot-mcp.env.TELEGRAM_MESSAGE_THREAD_ID   (optional)
```

Then reload the runtime snapshot:

```bash
openclaw secrets reload
```

Optional check:

```bash
echo "$ALPHA_VANTAGE_API_KEY"
echo "$NASDAQ_DATA_LINK_API_KEY"
echo "$NEWS_API_KEY"
echo "$TELEGRAM_BOT_TOKEN"
echo "$TELEGRAM_CHAT_ID"
```

---

## 5. Register the Agents from Repo Markdown Files

Run these commands from the repo root.

### 5.1 Register the persistent orchestrator

```bash
openclaw agents add stockhive-orchestrator \
  --workspace "$PWD" \
  --non-interactive
```

### 5.2 Register subagents

```bash
openclaw agents add data-fetcher \
  --workspace "$PWD" \
  --non-interactive
```

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

### 5.3 IMPORTANT (CLI compatibility): apply the Markdown agent instructions at runtime

Some OpenClaw versions (including `2026.4.21`) do **not** support `openclaw agents add --identity ...`.

In that case, keep the agent Markdown files in the repo and make the agent read them at the start of each run by prefacing your message like:

```text
Read and follow agent-system/agents/stockhive-orchestrator.md.
```

### 5.4 Allow the orchestrator to call its subagents

If your orchestrator can’t spawn/call other agents, add a subagent allow-list to the orchestrator entry in your OpenClaw config.

Run:

```bash
python3 - <<'PY'
import json, os

# Usually ~/.openclaw/openclaw.json, but OpenClaw may be configured elsewhere.
p = os.environ.get('OPENCLAW_CONFIG_PATH') or os.path.expanduser('~/.openclaw/openclaw.json')

cfg = json.load(open(p))
for a in cfg.get('agents', {}).get('list', []):
  if a.get('id') == 'stockhive-orchestrator':
    a.setdefault('subagents', {})['allowAgents'] = [
      'data-fetcher',
      'technical-analyst',
      'fundamental-analyst',
      'sentiment-analyst',
      'telegram-publisher',
    ]
json.dump(cfg, open(p, 'w'), indent=2)
print('Updated subagents allow-list for stockhive-orchestrator in', p)
PY
```

Verify:

```bash
openclaw agents list
openclaw agents list --verbose
```

---

## 6. Install / Copy Skills from the Repo

Create the skills directory in the *same workspace* as the StockHive agents.

(In this guide, we created the StockHive agents with `--workspace "$PWD"`, so the skills should live under `$PWD/skills`.)

```bash
mkdir -p "$PWD/skills"
```

Copy the repo skills:

```bash
cp -R agent-system/skills/stock-data-fetcher "$PWD/skills/"
cp -R agent-system/skills/technical-indicators "$PWD/skills/"
cp -R agent-system/skills/fundamental-snapshot "$PWD/skills/"
cp -R agent-system/skills/sentiment-analyzer "$PWD/skills/"
cp -R agent-system/skills/telegram-formatter "$PWD/skills/"
```

Verify:

```bash
find "$PWD/skills" -name "SKILL.md"
```

### 6.1 Tag skills onto the StockHive agents (so the dashboard shows them)

OpenClaw can show which skills are associated with each agent. Update the agent entries in your OpenClaw config:

```bash
python3 - <<'PY'
import json, os

p = os.environ.get('OPENCLAW_CONFIG_PATH') or os.path.expanduser('~/.openclaw/openclaw.json')
cfg = json.load(open(p))

skills_by_agent = {
  'data-fetcher': ['stock-data-fetcher'],
  'technical-analyst': ['technical-indicators'],
  'fundamental-analyst': ['fundamental-snapshot'],
  'sentiment-analyst': ['sentiment-analyzer'],
  'telegram-publisher': ['telegram-formatter'],
  # Optional but helpful for visibility:
  'stockhive-orchestrator': [
    'stock-data-fetcher',
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
print('Updated agent.skills for StockHive agents in', p)
PY
```

Verify in CLI:

```bash
openclaw agents list --json
openclaw skills info stock-data-fetcher
```

---

## 7. Register MCP Configuration

Use the MCP config already in the repo (`agent-system/mcps/mcp-config.json`).

This file contains multiple MCP server definitions. Register each one:

```bash
python3 - <<'PY'
import json, subprocess

cfg = json.load(open('agent-system/mcps/mcp-config.json'))
for name, server in cfg['mcpServers'].items():
  subprocess.run(['openclaw', 'mcp', 'set', name, json.dumps(server)], check=True)
print('MCP servers registered:', ', '.join(cfg['mcpServers'].keys()))
PY
```

Verify:

```bash
openclaw mcp list
```

If your OpenClaw version does not support `mcp set`, inspect supported MCP commands:

```bash
openclaw mcp --help
```

---

## 8. Add the 5 PM Weekday Schedule

This creates a weekday 5 PM run.

Replace `Europe/London` with the user’s preferred time zone if needed.

```bash
openclaw cron add \
  --name "StockHive Nasdaq Daily Run" \
  --agent "stockhive-orchestrator" \
  --cron "0 17 * * 1-5" \
  --tz "Europe/London" \
  --session isolated \
  --message "Read and follow agent-system/agents/stockhive-orchestrator.md. Then run the StockHive Nasdaq-100 top movers workflow using agent-system/runtime/ORCHESTRATOR_RUNTIME.md and agent-system/runtime/orchestrator-run-input.json. Publish the final top 5 to Telegram." \
  --announce \
  --channel telegram \
  --to "$TELEGRAM_CHAT_ID"
```

Schedule explanation:

```text
0 17 * * 1-5 = every Monday through Friday at 17:00 / 5:00 PM
```

Check the cron job:

```bash
openclaw cron list
openclaw cron status
```

---

## 9. If You Already Created the Wrong Schedule

List cron jobs:

```bash
openclaw cron list
```

Remove or edit the old job depending on what your CLI supports:

```bash
openclaw cron remove "StockHive Nasdaq Daily Run"
```

If `remove` does not work, inspect available commands:

```bash
openclaw cron --help
```

Then add the corrected 5 PM job from Step 8.

---

## 10. Manual Test Run

Run the orchestrator manually:

```bash
openclaw agent --agent stockhive-orchestrator \
  --message "Read and follow agent-system/agents/stockhive-orchestrator.md. Then run the full StockHive workflow using agent-system/runtime/ORCHESTRATOR_RUNTIME.md and agent-system/runtime/orchestrator-run-input.json. Output the top 5 buy candidates and publish to Telegram." \
  --json
```

If `openclaw run` is not available in your version:

```bash
openclaw --help
openclaw agents --help
```

Then use the run/invoke command your CLI exposes.

---

## 11. Verification Checklist

```bash
openclaw agents list --verbose
openclaw mcp list
openclaw cron list
openclaw status
openclaw doctor
```

Confirm:

```text
stockhive-orchestrator exists
data-fetcher exists
technical-analyst exists
fundamental-analyst exists
sentiment-analyst exists
telegram-publisher exists
StockHive Nasdaq Daily Run exists
Schedule is 0 17 * * 1-5
Timezone is correct
MCP config is loaded
.env values are present
```

---

## 12. Troubleshooting

### `/agents register ./agent-system.json` does not work

That slash command is not part of the OpenClaw CLI. Use:

```bash
openclaw agents add <agent-name> --identity <path-to-agent-md> --workspace "$PWD"
```

### Agent already exists

Either remove the existing agent or use a new name.

Check existing agents:

```bash
openclaw agents list
```

### Invalid agent name

Use lowercase letters, numbers, and hyphens only.

Valid examples:

```text
stockhive-orchestrator
data-fetcher
technical-analyst
```

Invalid examples:

```text
StockHive_Orchestrator
data_fetcher
technical analyst
```

### Workspace directory not found

Make sure you are in the repo root:

```bash
pwd
ls agent-system.json
```

Then re-run the command.

### Cron does not fire

Check:

```bash
openclaw cron status
openclaw cron list
openclaw status
```

Also confirm the timezone:

```bash
date
```

The schedule should include:

```bash
--tz "Europe/London"
```

or your preferred timezone.

### Telegram does not publish

Check:

```bash
echo "$TELEGRAM_BOT_TOKEN"
echo "$TELEGRAM_CHAT_ID"
```

Make sure:

- The bot was created with `@BotFather`
- The bot is added to the channel or group
- The bot is an admin if posting to a channel
- Channel IDs usually begin with `-100`

---

## Done

StockHive is now registered using the Markdown files under `agent-system/agents` and the skills under `agent-system/skills`.

The weekday schedule is set to 5 PM.
