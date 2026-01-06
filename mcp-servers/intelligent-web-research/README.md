# Intelligent Web Research MCP Server

## Table of Contents
- [Features](#features)
- [Tools](#tools)
- [Data Freshness Protocol](#data-freshness-protocol)
- [Environment Variables](#environment-variables)
- [Usage](#usage)



Intelligent routing for web search and browser-based research. Detects available capabilities and routes to the best method for obtaining fresh web data.

## Features

- **Capability Detection**: Automatically detect WebSearch, WebFetch, and browser availability
- **Browser Integration**: Open Comet, Arc, or system browser for deep research
- **AI Search Engines**: Route to Perplexity, ChatGPT, You.com for AI-synthesized research
- **Search Strategy**: Get optimal search approach based on query type
- **Data Freshness Protocol**: Enforce consistent data quality standards

## Tools

### detect_capabilities
Check what web search and browsing capabilities are available.

```json
{}
```

### open_research_browser
Open an AI-powered search engine for comprehensive research.

```json
{
  "query": "latest machine learning research papers 2024",
  "search_engine": "perplexity",
  "topic_domain": "technology"
}
```

Supported engines: `perplexity`, `chatgpt`, `google`, `duckduckgo`, `bing`, `you`

### get_search_strategy
Get recommended search strategy for a query.

```json
{
  "query": "latest AWS Lambda pricing changes",
  "purpose": "validation",
  "freshness": "recent"
}
```

### get_data_freshness_protocol
Get the complete Data Freshness Protocol for consistent web data handling.

```json
{}
```

### open_url
Open a specific URL in the browser.

```json
{
  "url": "https://docs.python.org/3/",
  "browser": "comet"
}
```

## Data Freshness Protocol

The server enforces a strict hierarchy for obtaining web data:

1. **Tier 1: WebSearch** - Always try first for any external data
2. **Tier 2: WebFetch** - Fetch specific authoritative URLs
3. **Tier 3: Browser** - Deep research with AI synthesis (Perplexity, ChatGPT)
4. **Tier 4: Training** - ONLY as last resort, mark as `[TRAINING DATA - VERIFY]`

### Validation Rules

- Critical claims require 3+ independent sources
- Dates/events must have dated source
- Statistics must cite original study/report
- Policies must cite official source

### Freshness Thresholds

- Trending topics: < 7 days
- Policy/regulatory: < 30 days
- Stable facts: Verify still accurate

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COMET_BROWSER_PATH` | `/Applications/Comet.app/Contents/MacOS/Comet` | Path to Comet browser |
| `DEFAULT_BROWSER` | `comet` | Default browser to use |

## Usage

### In Skills

```markdown
## Data Freshness Protocol (MANDATORY)

Before using training knowledge, execute web search:
1. Use `WebSearch` for initial query
2. Use `WebFetch` for authoritative URLs
3. Use `open_research_browser` for deep research
4. ONLY use training data as last resort, marked as [UNVERIFIED]
```

### In Hooks

```markdown
## Pre-Execute Hook

Check if web search is available before executing research tasks:
- Call `detect_capabilities` to understand available tools
- Route to appropriate method based on query type
```
