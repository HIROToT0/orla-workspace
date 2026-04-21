---
name: tavily-search
description: "Web search using Tavily AI Search API. Use when you need fresh web search results with AI-grounded answers. Requires TAVILY_API_KEY env var. Sign up at https://tavily.com for an API key. Trigger: user asks to search the web, find online info, look up something, or any search request."
---

# Tavily Search

Web search via Tavily AI — returns AI-synthesized answer + ranked results with snippets.

## Setup

The `TAVILY_API_KEY` is already configured in `skills.entries.tavily-search.env`.
No setup needed — just call the script directly.

## Tool: tavily_search

**When:** User asks to search the web, find information online, look something up, etc.

**Script path:** `/vol2/@apphome/trim.openclaw/data/workspace/skills/tavily-search/scripts/tavily.sh`

**Usage:**
```bash
TAVILY_API_KEY="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" \
bash /vol2/@apphome/trim.openclaw/data/workspace/skills/tavily-search/scripts/tavily.sh "<query>" <max_results> [basic|advanced]
```

**Parameters:**
- `query` (required) — search query string
- `max_results` (optional, default: 5) — number of results (1-10)
- `search_depth` (optional, default: basic) — "basic" or "advanced"

**Example call:**
```bash
TAVILY_API_KEY="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" \
bash /vol2/@apphome/trim.openclaw/data/workspace/skills/tavily-search/scripts/tavily.sh "OpenClaw AI assistant" 5 basic
```

**Output format (JSON):**
```json
{
  "query": "...",
  "answer": "AI-generated answer",
  "results": [
    { "title": "...", "url": "...", "snippet": "...", "published": "..." }
  ]
}
```

## Direct curl alternative

If the script has issues, use curl directly:
```bash
curl -s --max-time 15 -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"<query>\",\"max_results\":5,\"search_depth\":\"basic\",\"include_answer\":true}"
```

## When to use this vs web_fetch

- **tavily_search**: AI-grounded search with synthesized answer, best for research
- **web_fetch**: Direct page content extraction, best for specific URLs you already have
