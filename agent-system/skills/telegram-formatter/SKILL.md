---
name: telegram-formatter
description: Render the orchestrator's decision JSON into the canonical StockHive markdown alert for Telegram.
triggers:
  - "format telegram alert"
  - "stockhive markdown message"
  - "publish top 5 buys"
mcps:
  - telegram-bot-mcp
---

# Skill: telegram-formatter

## When to use
You have the final decision JSON (`market_view`, `top5`, `excluded`) and need to deliver it to the Telegram channel.

## Template
Render exactly this shape (Markdown, Telegram-safe):

```
** Nasdaq 100 — Daily Top 5 Buys **
Date: {{DD Mon YYYY}}  |  Close + 1h

Market view:  [ {{market_view}} ]
Breadth {{buy_count}}/10 up, RSI avg {{rsi_avg}}, sentiment {{sent_avg_signed}}

Top 5 Buy Candidates
--------------------
{{#each top5}}
{{idx}}. {{ticker}}  {{return_4w_pct}}  RSI {{rsi}}  PE {{pe}}
   Tech: {{tech_note}}. Fund: {{fund_note}}.
{{/each}}

{{#if excluded}}
Excluded: {{#each excluded}}{{ticker}} ({{reason}}){{#unless @last}}, {{/unless}}{{/each}}.
{{/if}}
--
OpenClaw  |  Daily 17:00 ET
```

## Steps
1. Compute aggregates: `buy_count`, `rsi_avg` (int), `sent_avg_signed` (e.g. `+0.42`).
2. Substitute into the template.
3. Keep total length < 3500 characters (Telegram caption-safe buffer).
4. Call `telegram-bot-mcp.sendMessage(chat_id, text, parse_mode="Markdown")`.
5. Return the message id.

## Guardrails
- Never embed raw JSON — only the rendered markdown.
- Escape `_`, `*`, `[` in ticker notes (unlikely but defensive).
