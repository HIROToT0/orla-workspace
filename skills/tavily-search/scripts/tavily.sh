#!/bin/bash
set -e

QUERY="${1?Usage: $0 <query> [max_results] [search_depth]}"
MAX_RESULTS="${2:-5}"
SEARCH_DEPTH="${3:-basic}"

# Try env var first, then fall back to credentials file
if [ -n "$TAVILY_API_KEY" ]; then
  API_KEY="$TAVILY_API_KEY"
else
  KEY_FILE="/vol2/@apphome/trim.openclaw/data/home/.openclaw/credentials/tavily.key"
  if [ -f "$KEY_FILE" ]; then
    API_KEY=$(cat "$KEY_FILE")
  else
    echo "Error: TAVILY_API_KEY not set and $KEY_FILE not found" >&2
    exit 1
  fi
fi

PAYLOAD=$(jq -cn \
  --arg q "$QUERY" \
  --argjson mr "$MAX_RESULTS" \
  --arg sd "$SEARCH_DEPTH" \
  --arg key "$API_KEY" \
  '{
    api_key: $key,
    query: $q,
    max_results: $mr,
    search_depth: $sd,
    include_answer: true,
    include_raw_content: false
  }')

curl -s --max-time 20 -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | jq '{
    query: .query,
    answer: .answer,
    results: [.results[] | {
      title: .title,
      url: .url,
      snippet: .content,
      published: .published_date
    }]
  }'
