---
name: sentiment-analyzer
description: Score recent news sentiment for a ticker in [-1, +1] by reasoning over headlines from the last 7 days.
triggers:
  - "news sentiment"
  - "headline sentiment score"
  - "ticker sentiment"
mcps:
  - news-api-mcp
---

# Skill: sentiment-analyzer

## When to use
A ticker needs a qualitative narrative/momentum read to complement technicals & fundamentals.

## Steps
1. `news-api-mcp.everything(q="<TICKER> OR <company_name>", from=NOW-7d, language="en", pageSize=10, sortBy="relevancy")`.
2. Read headline + description for each article.
3. Reason qualitatively (no external LLM MCP call):
   - Count strong-positive themes (earnings beat, upgrade, new contract, AI-tailwind, etc.) vs strong-negative (downgrade, probe, guidance cut, layoff, lawsuit).
   - Normalize to a score in [-1, +1] with 1 decimal of precision.
4. Capture a `top_theme` — the dominant narrative in 4–8 words.

## Output shape
```json
{"ticker":"AVGO","score":0.55,"top_theme":"AI silicon demand accelerating","n_headlines":10}
```

## Guardrails
- If `n_headlines < 3`, set `score:0.0` and `confidence:"low"`.
- Never treat a ticker symbol that collides with a common word (e.g. `ON`, `ALL`) without company-name disambiguation in the query.
