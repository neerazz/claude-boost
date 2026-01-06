#!/usr/bin/env python3
"""
Intelligent Web Research MCP Server

Detects available web/search capabilities and routes to the best method:
1. Built-in WebSearch/WebFetch (if model has internet access)
2. Comet browser for deep research (Perplexity, ChatGPT search, Google)
3. Fallback strategies when primary methods unavailable

This server provides intelligent routing and capability detection to ensure
skills always have access to fresh web data.
"""

from __future__ import annotations

import json
import sys
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Dict, List
from urllib.parse import quote_plus

# ============================================================================
# CONFIGURATION
# ============================================================================
# Browser configuration
COMET_BROWSER_PATH = os.environ.get(
    "COMET_BROWSER_PATH",
    "/Applications/Comet.app/Contents/MacOS/Comet"
)
DEFAULT_BROWSER = os.environ.get("DEFAULT_BROWSER", "comet")  # comet, chrome, safari, firefox

# Search engine URLs
SEARCH_ENGINES = {
    "perplexity": "https://www.perplexity.ai/search?q={query}",
    "chatgpt": "https://chatgpt.com/?q={query}",
    "google": "https://www.google.com/search?q={query}",
    "duckduckgo": "https://duckduckgo.com/?q={query}",
    "bing": "https://www.bing.com/search?q={query}",
    "you": "https://you.com/search?q={query}",
}

# AI-powered search engines (prioritize for research)
AI_SEARCH_ENGINES = ["perplexity", "chatgpt", "you"]

# Research domains for specific topics
RESEARCH_DOMAINS = {
    "government": ["usa.gov", "whitehouse.gov", "congress.gov", "regulations.gov"],
    "tech": ["github.com", "stackoverflow.com", "dev.to", "hackernews.com"],
    "academic": ["scholar.google.com", "arxiv.org", "semanticscholar.org"],
    "news": ["reuters.com", "apnews.com", "bbc.com"],
    "business": ["sec.gov", "bloomberg.com", "crunchbase.com"],
}
# ============================================================================


def detect_capabilities() -> Dict[str, Any]:
    """
    Detect available web search and browsing capabilities.

    Checks:
    1. Built-in WebSearch/WebFetch availability (via Claude model)
    2. Browser availability (Comet, Chrome, Safari, Firefox)
    3. CLI tools (curl, wget)
    4. Search engine accessibility

    Returns:
        Dict with capability status and recommended methods
    """
    capabilities = {
        "timestamp": datetime.now().isoformat(),
        "builtin_tools": {
            "web_search": True,  # Assume Claude has WebSearch if this MCP is called
            "web_fetch": True,   # Assume Claude has WebFetch
            "note": "Built-in tools available - use WebSearch and WebFetch directly"
        },
        "browsers": {},
        "cli_tools": {},
        "recommended_method": "builtin",
        "ai_search_available": False,
    }

    # Check browsers
    browsers_to_check = {
        "comet": COMET_BROWSER_PATH,
        "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "safari": "/Applications/Safari.app/Contents/MacOS/Safari",
        "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
        "arc": "/Applications/Arc.app/Contents/MacOS/Arc",
    }

    for browser, path in browsers_to_check.items():
        exists = os.path.exists(path) or shutil.which(browser) is not None
        capabilities["browsers"][browser] = {
            "available": exists,
            "path": path if exists else None
        }
        if exists and browser in ["comet", "arc"]:
            capabilities["ai_search_available"] = True

    # Check CLI tools
    cli_tools = ["curl", "wget", "open"]
    for tool in cli_tools:
        capabilities["cli_tools"][tool] = shutil.which(tool) is not None

    # Determine recommended method
    if capabilities["browsers"].get("comet", {}).get("available"):
        capabilities["recommended_method"] = "comet_browser"
        capabilities["reason"] = "Comet browser available - supports Perplexity AI search"
        capabilities["primary_strategy"] = "agentic_browser_navigation"
    elif capabilities["browsers"].get("arc", {}).get("available"):
        capabilities["recommended_method"] = "arc_browser"
        capabilities["reason"] = "Arc browser available - supports AI features"
        capabilities["primary_strategy"] = "agentic_browser_navigation"
    elif any(capabilities["browsers"].get(b, {}).get("available") for b in ["chrome", "safari", "firefox"]):
        capabilities["recommended_method"] = "standard_browser"
        capabilities["reason"] = "Standard browser available for web research"
        capabilities["primary_strategy"] = "agentic_browser_navigation"
    else:
        capabilities["recommended_method"] = "builtin"
        capabilities["reason"] = "No external browser detected - using built-in tools"
        capabilities["primary_strategy"] = "web_search_only"

    # Add usage instructions
    if "browser" in capabilities["recommended_method"]:
        capabilities["usage"] = {
            "primary": "ALWAYS use open_research_browser/open_url to mirror actions for the user",
            "data_collection": "Use WebFetch/WebSearch to get information for the AI",
            "navigation": "Control the browser by opening successive URLs based on findings"
        }
    else:
        capabilities["usage"] = {
            "primary": "Use WebSearch tool directly for quick queries",
            "validate_with": "Use multi_source_search for critical claims (3-source validation)"
        }

    return capabilities


def build_search_url(query: str, engine: str = "perplexity") -> str:
    """Build a search URL for the specified engine."""
    if engine not in SEARCH_ENGINES:
        engine = "perplexity"

    encoded_query = quote_plus(query)
    return SEARCH_ENGINES[engine].format(query=encoded_query)


def open_browser(url: str, browser: str = "default") -> Dict[str, Any]:
    """
    Open a URL in the specified browser.

    Args:
        url: URL to open
        browser: Browser to use (default, comet, chrome, safari, firefox)

    Returns:
        Dict with success status and details
    """
    try:
        if browser == "default" or browser == "comet":
            # Check if Comet is available
            if os.path.exists(COMET_BROWSER_PATH):
                subprocess.Popen([COMET_BROWSER_PATH, url],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                return {
                    "success": True,
                    "browser": "comet",
                    "url": url,
                    "note": "Opened in Comet browser - supports AI-powered search"
                }

        # Fallback to system default
        if sys.platform == "darwin":
            subprocess.Popen(["open", url],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", url],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["start", url], shell=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

        return {
            "success": True,
            "browser": "system_default",
            "url": url
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


def open_research_browser(
    query: str,
    search_engine: str = "perplexity",
    topic_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Open browser for comprehensive research on a topic.

    This tool opens an AI-powered search engine (Perplexity, ChatGPT) for deep research.
    Use this when:
    - Built-in WebSearch needs more comprehensive results
    - Topic requires AI reasoning/synthesis
    - User wants to explore sources interactively

    Args:
        query: Search query or research question
        search_engine: Search engine (perplexity, chatgpt, google, etc.)
        topic_domain: Optional domain hint (government, tech, academic, etc.)

    Returns:
        Dict with browser status and research guidance
    """
    # Build the search URL
    url = build_search_url(query, search_engine)

    # Open browser
    result = open_browser(url)

    # Add research guidance
    result["query"] = query
    result["search_engine"] = search_engine

    # Add domain-specific sources to check
    if topic_domain and topic_domain in RESEARCH_DOMAINS:
        result["recommended_sources"] = RESEARCH_DOMAINS[topic_domain]
        result["guidance"] = f"After AI search, validate with domain sources: {', '.join(RESEARCH_DOMAINS[topic_domain])}"

    result["next_steps"] = [
        "1. Review AI-synthesized answer in browser",
        "2. Check cited sources for accuracy",
        "3. Use WebFetch to capture specific URLs",
        "4. Cross-validate critical claims with 3+ sources"
    ]

    return result


def get_search_strategy(
    query: str,
    purpose: str = "general",
    freshness: str = "any",
) -> Dict[str, Any]:
    """
    Get recommended search strategy for a query.

    Analyzes the query and returns the optimal search approach:
    - Which tool to use (WebSearch, WebFetch, browser)
    - Which search engines to try
    - Domain-specific sources to check
    - Validation requirements

    Args:
        query: The search query or research question
        purpose: Purpose of search (general, validation, deep_research, fact_check)
        freshness: Data freshness requirement (any, recent, today)

    Returns:
        Dict with search strategy and step-by-step instructions
    """
    strategy = {
        "query": query,
        "purpose": purpose,
        "freshness": freshness,
        "steps": [],
        "primary_method": "websearch",
        "fallback_methods": [],
    }

    # Determine query type
    query_lower = query.lower()

    # Check for specific domains
    detected_domain = None
    for domain, keywords in {
        "government": ["policy", "regulation", "federal", "state", "legislation", "compliance"],
        "tech": ["api", "code", "programming", "github", "bug", "feature"],
        "academic": ["paper", "research", "study", "journal", "arxiv"],
        "news": ["today", "yesterday", "breaking", "recent", "latest"],
        "business": ["company", "startup", "funding", "sec", "earnings"],
    }.items():
        if any(kw in query_lower for kw in keywords):
            detected_domain = domain
            break

    strategy["detected_domain"] = detected_domain

    # Build search steps based on purpose
    if purpose == "validation" or "verify" in query_lower or "fact check" in query_lower:
        strategy["primary_method"] = "multi_source"
        strategy["steps"] = [
            {
                "step": 1,
                "action": "open_research_browser",
                "description": "Open search in browser for visibility",
                "params": {"query": query, "search_engine": "perplexity"}
            },
            {
                "step": 2,
                "action": "websearch",
                "description": "Use WebSearch for initial results (AI view)",
                "params": {"query": query}
            },
            {
                "step": 3,
                "action": "websearch",
                "description": "Search for counter-evidence",
                "params": {"query": f"{query} criticism OR debunked OR false"}
            },
            {
                "step": 4,
                "action": "webfetch",
                "description": "Fetch authoritative sources",
                "params": {"note": "Fetch top 3 most authoritative URLs from step 2"}
            },
            {
                "step": 5,
                "action": "validate",
                "description": "Cross-reference claims",
                "params": {"requirement": "3+ independent sources must agree"}
            }
        ]
        strategy["validation_required"] = True
        strategy["min_sources"] = 3

    elif purpose == "deep_research" or purpose == "general":
        # Agentic Browser Navigation Strategy
        strategy["primary_method"] = "agentic_browser"
        strategy["steps"] = [
            {
                "step": 1,
                "action": "open_research_browser",
                "description": "Start research session in browser (User View)",
                "params": {"search_engine": "perplexity", "query": query}
            },
            {
                "step": 2,
                "action": "websearch",
                "description": "Get initial search results (AI View)",
                "params": {"query": query}
            },
            {
                "step": 3,
                "action": "analyze_and_navigate",
                "description": "Analyze results and select next URL",
                "params": {"note": "Identify most promising link to explore"}
            },
            {
                "step": 4,
                "action": "browser_navigate",
                "description": "Open selected URL in browser AND fetch content",
                "params": {
                    "actions": [
                        "open_url(url=selected_url)",
                        "webfetch(url=selected_url)"
                    ]
                }
            },
            {
                "step": 5,
                "action": "synthesize",
                "description": "Synthesize findings or continue navigation",
                "params": {"note": "Repeat steps 3-4 if more info needed"}
            }
        ]

    elif freshness == "today" or freshness == "recent":
        strategy["steps"] = [
            {
                "step": 1,
                "action": "websearch",
                "description": f"Search with recency filter",
                "params": {"query": f"{query} {datetime.now().year}"}
            },
            {
                "step": 2,
                "action": "verify_date",
                "description": "Verify publication dates",
                "params": {"requirement": "Results must be from last 7 days"}
            }
        ]
        strategy["freshness_warning"] = "Reject any sources older than 7 days for this query"

    else:
        # General search
        strategy["steps"] = [
            {
                "step": 1,
                "action": "websearch",
                "description": "Primary web search",
                "params": {"query": query}
            },
            {
                "step": 2,
                "action": "webfetch",
                "description": "Fetch relevant URLs for details",
                "params": {"note": "If needed, fetch specific pages for deeper content"}
            }
        ]

    # Add domain-specific sources
    if detected_domain and detected_domain in RESEARCH_DOMAINS:
        strategy["domain_sources"] = RESEARCH_DOMAINS[detected_domain]
        strategy["domain_guidance"] = f"For {detected_domain} queries, prioritize: {', '.join(RESEARCH_DOMAINS[detected_domain])}"

    # Add fallback methods
    strategy["fallback_methods"] = [
        {"method": "browser", "when": "WebSearch returns limited results"},
        {"method": "manual", "when": "Critical data not found via automated search"}
    ]

    return strategy


def get_data_freshness_protocol() -> Dict[str, Any]:
    """
    Return the Data Freshness Protocol for consistent web search usage.

    This protocol ensures all skills follow the same pattern for
    obtaining and validating fresh web data.

    Returns:
        Dict with the complete data freshness protocol
    """
    return {
        "name": "Data Freshness Protocol v1.1",
        "description": "Mandatory protocol for obtaining and validating web data",
        "hierarchy": {
            "tier_1": {
                "source": "Agentic Browser (Open + Fetch)",
                "when": "ALWAYS try first. Open browser for user visibility, use WebSearch/WebFetch for AI data.",
                "example": "open_research_browser(...) AND WebSearch(...)"
            },
            "tier_2": {
                "source": "WebSearch (Real-time fallback)",
                "when": "If browser unavailable or for quick fact checks.",
                "example": "WebSearch('Python 3.12 new features 2024')"
            },
            "tier_3": {
                "source": "WebFetch (Targeted)",
                "when": "Fetch specific authoritative URLs found in Tier 1/2",
                "example": "WebFetch('https://docs.python.org/3/')"
            },
            "tier_4": {
                "source": "Training knowledge",
                "when": "ONLY as last resort, ONLY for stable facts",
                "warning": "Mark as [TRAINING DATA - VERIFY] if used"
            }
        },
        "validation_rules": {
            "critical_claims": "Require 3+ independent sources",
            "dates_events": "Must have dated source (reject 'generally' or 'usually')",
            "statistics": "Must cite original study/report",
            "policies": "Must cite official source (gov, org official docs)"
        },
        "freshness_thresholds": {
            "trending_topics": "< 7 days",
            "policy_regulatory": "< 30 days for 'current' claims",
            "stable_facts": "No strict requirement, but verify still accurate"
        },
        "rejection_criteria": [
            "Source has no date",
            "Source is > 1 year old for time-sensitive topics",
            "Cannot find 3 sources agreeing",
            "Only AI-generated content without citations"
        ],
        "output_format": {
            "verified_claim": "[VERIFIED] Claim text (Source: URL, Date: YYYY-MM-DD)",
            "unverified": "[UNVERIFIED - LOW CONFIDENCE] Claim text",
            "stale_data": "[STALE - VERIFY] Claim text (Last verified: YYYY-MM-DD)"
        }
    }


# ============================================================================
# MCP Protocol Implementation
# ============================================================================

def handle_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle incoming MCP request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "intelligent-web-research",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "detect_capabilities",
                        "description": """Detect available web search and browsing capabilities.

Use this FIRST to understand what tools are available:
- Built-in WebSearch/WebFetch
- Browsers (Comet, Chrome, Safari, Firefox, Arc)
- CLI tools (curl, wget)

Returns recommended method based on availability.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "open_research_browser",
                        "description": """Open an AI-powered search engine for comprehensive research.

Use this when:
- Built-in WebSearch needs more comprehensive results
- Topic requires AI reasoning/synthesis (complex questions)
- User wants to explore sources interactively
- Deep research on unfamiliar topics

Supports: Perplexity (recommended), ChatGPT, Google, DuckDuckGo, Bing, You.com

The browser opens with the search query, allowing the user to:
1. Review AI-synthesized answers
2. Explore cited sources
3. Follow up with related questions""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query or research question"
                                },
                                "search_engine": {
                                    "type": "string",
                                    "description": "Search engine: perplexity (default), chatgpt, google, duckduckgo, bing, you",
                                    "default": "perplexity"
                                },
                                "topic_domain": {
                                    "type": "string",
                                    "description": "Optional domain hint: government, tech, academic, news, business"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_search_strategy",
                        "description": """Get recommended search strategy for a query.

Analyzes your query and returns the optimal approach:
- Which tools to use (WebSearch, WebFetch, browser)
- Which search engines to try
- Domain-specific sources to check
- Validation requirements
- Step-by-step instructions

Use this when planning a research task to get the best approach.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query or research question"
                                },
                                "purpose": {
                                    "type": "string",
                                    "description": "Purpose: general, validation, deep_research, fact_check",
                                    "default": "general"
                                },
                                "freshness": {
                                    "type": "string",
                                    "description": "Data freshness: any, recent, today",
                                    "default": "any"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_data_freshness_protocol",
                        "description": """Get the Data Freshness Protocol for consistent web search usage.

Returns the complete protocol that all skills should follow:
- Search hierarchy (WebSearch → WebFetch → Browser → Training)
- Validation rules (3-source validation, date requirements)
- Freshness thresholds (7 days for trends, 30 days for policy)
- Rejection criteria (no date, too old, can't verify)
- Output format ([VERIFIED], [UNVERIFIED], [STALE])

Use this to ensure consistent data quality across all research tasks.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "open_url",
                        "description": """Open a specific URL in the browser.

Use this to open specific websites for research or reference.
Prefers Comet browser if available (AI-powered features).""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "URL to open"
                                },
                                "browser": {
                                    "type": "string",
                                    "description": "Browser: default, comet, chrome, safari, firefox",
                                    "default": "default"
                                }
                            },
                            "required": ["url"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "detect_capabilities":
            result = detect_capabilities()
        elif tool_name == "open_research_browser":
            result = open_research_browser(
                query=arguments.get("query", ""),
                search_engine=arguments.get("search_engine", "perplexity"),
                topic_domain=arguments.get("topic_domain"),
            )
        elif tool_name == "get_search_strategy":
            result = get_search_strategy(
                query=arguments.get("query", ""),
                purpose=arguments.get("purpose", "general"),
                freshness=arguments.get("freshness", "any"),
            )
        elif tool_name == "get_data_freshness_protocol":
            result = get_data_freshness_protocol()
        elif tool_name == "open_url":
            result = open_browser(
                url=arguments.get("url", ""),
                browser=arguments.get("browser", "default"),
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        }

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


def main():
    """Main MCP server loop using stdio."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = handle_request(request)

            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
