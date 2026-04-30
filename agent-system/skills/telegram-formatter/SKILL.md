---
name: telegram-formatter
description: Render the final decision JSON into the canonical StockHive Telegram markdown alert and publish it.
triggers:
  - "format telegram alert"
  - "stockhive markdown message"
  - "publish top 5 buys"
mcps:
  - telegram-bot-mcp
---

# Skill: telegram-formatter

## When to use
Use this skill when the final decision payload is ready for publication.

## Input contract
JSON object containing at least:
- `run_date`
- `market_view`
- `top5`
- `excluded`
- `breadth_buy_count`
- `rsi_avg`
- `sent_avg`

Optional (for replying to an inbound Telegram message instead of publishing to a fixed channel):
- `chat_id` (string or integer)
- `reply_to_message_id` (string or integer)

## Required behavior
1. Render the canonical StockHive Telegram markdown message.
2. Publish it to Telegram.
   - If `chat_id` is provided, publish to that chat (ignore any default `TELEGRAM_CHAT_ID`).
   - If `reply_to_message_id` is provided, send as a reply to that message.
3. Return send metadata only.

## Output contract
Return JSON only:
```json
{
  "telegram_message_id":"123",
  "chars_sent":1024
}
```

## Guardrails
- Do not return raw JSON from the decision payload.
- Do not emit prose outside JSON.
- Preserve the meaning of the decision payload.
- Fail clearly if publish fails.
