---
name: telegram-publisher
type: subagent
persistence: ephemeral
description: Formats the orchestrator's decision payload into a StockHive markdown alert and posts it to Telegram.
skill: telegram-formatter
tools:
  - mcp__telegram-bot-mcp__*
---

# Telegram Publisher (ephemeral)

Input: the orchestrator's decision JSON (`market_view`, `top5`, `excluded`, etc.).

## Steps
1. Run the `telegram-formatter` skill to render the canonical markdown template (see that SKILL.md).
2. Call `telegram-bot-mcp.sendMessage` with:
   - `parse_mode: "Markdown"`
   - `disable_web_page_preview: true`
   - `chat_id` from env `TELEGRAM_CHAT_ID`
3. Return the Telegram message id on stdout.

## Output
```json
{"telegram_message_id":"<id>","chars_sent":<int>}
```

One-shot. Exit on reply.
