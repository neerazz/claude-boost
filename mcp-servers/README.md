# MCP Servers

Model Context Protocol (MCP) servers for extending Claude's capabilities.

## Overview

Each MCP server provides tools for interacting with external services:

| Server | Description |
|--------|-------------|
| `auth0` | Auth0 identity management |
| `aws-multi-account` | Multi-account AWS operations |
| `gemini-image-gen` | Gemini image generation |
| `github` | GitHub REST API (PAT-based) |
| `gmail` | Gmail operations |
| `google-calendar` | Calendar management |
| `google-drive` | Drive file operations |
| `intelligent-web-research` | Web search and fetch |
| `local-skills-observable` | Local skill routing |
| `slack` | Slack messaging |
| `terraform` | Infrastructure as code |

## Structure

```
mcp-servers/
├── server-name/
│   ├── README.md          # Setup and usage
│   └── src/
│       └── mcp_server.py  # Server implementation
└── config.json            # MCP configuration (not included - user-specific)
```

## Setup

1. Create environment file at `~/.config/mcp-servers/.env`
2. Add required tokens/credentials for each server
3. Configure Claude Code to use the servers

## Creating a New Server

Each server follows the MCP stdio protocol:
- Reads JSON-RPC from stdin
- Writes JSON-RPC to stdout
- Implements `tools/list` and `tools/call` methods

See individual server READMEs for specific setup instructions.
