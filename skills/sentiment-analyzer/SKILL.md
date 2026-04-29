---
name: sentiment-analyzer
description: Score recent news sentiment for each ticker in [-1, +1] and summarize the dominant theme.
triggers:
  - "news sentiment"
  - "headline sentiment score"
  - "ticker sentiment"
mcps:
  - news-api-mcp
---

# Skill: sentiment-analyzer

## When to use
Use this skill when the orchestrator sends a ticker list for sentiment analysis.

## Input contract
```json
[
  {"ticker":"AAPL"},
  {"ticker":"MSFT"}
]
```

## Required behavior
For each ticker:
1. Fetch recent relevant headlines.
2. Reason over the coverage.
3. Return:
   - `ticker`
   - `score` in [-1, +1]
   - `top_theme`
   - `n_headlines`

## Output contract
Return JSON only:
```json
[
  {
    "ticker":"AAPL",
    "score":0.42,
    "top_theme":"AI demand in focus",
    "n_headlines":10
  }
]
```
One row per input ticker.

## Guardrails
- Never fabricate news coverage.
- If coverage is thin, use a neutral/low-confidence result.
- Keep `top_theme` short and specific.
- Do not emit prose outside JSON.