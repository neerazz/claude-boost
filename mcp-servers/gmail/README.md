# Gmail MCP Server

## Table of Contents
- [Features](#features)
- [Available Tools](#available-tools)
- [Files](#files)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Gmail Search Syntax](#gmail-search-syntax)
- [Usage Examples](#usage-examples)
- [MCP Config](#mcp-config)
- [Security Notes](#security-notes)



A self-contained MCP server for Gmail operations. Uses YOUR own OAuth credentials - no external package dependencies.

## Features

- **Self-contained**: Uses only Python standard library (no pip dependencies)
- **Your own OAuth credentials**: Uses your GCP project's OAuth client
- **Full MCP protocol support**: Works with Cursor, Claude Desktop, Claude Code, Gemini CLI
- **Complete email operations**: Read, send, search, reply, manage labels

## Available Tools

| Tool | Description |
|------|-------------|
| `list_messages` | List messages with optional filters |
| `get_message` | Get full message content with body and attachments |
| `send_message` | Send a new email |
| `reply_to_message` | Reply to an existing thread |
| `search_messages` | Search using Gmail query syntax |
| `list_labels` | List all Gmail labels |
| `modify_labels` | Add/remove labels (mark read/unread, star, etc.) |
| `create_draft` | Create a draft email |
| `delete_message` | Delete (trash) a message |
| `get_thread` | Get all messages in a thread |

## Files

```
gmail/
├── src/
│   └── mcp_server.py     # MCP server implementation
├── tokens.json           # OAuth tokens (auto-generated)
├── requirements.txt      # Dependencies (none required)
└── README.md            # This file
```

## Setup

### 1. OAuth Credentials

This server shares OAuth credentials with Google Calendar MCP:
- Credentials: `../google-calendar/gcp-oauth.keys.json`
- Each service has its own token file for different scopes

### 2. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **APIs & Services** → **Library**
3. Search for "Gmail API"
4. Click **Enable**

### 3. OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Add Gmail scopes:
   - `gmail.readonly`
   - `gmail.send`
   - `gmail.compose`
   - `gmail.modify`
3. Add your email to **Test users** (if in Testing mode)

### 4. First Authentication

The first time you use the MCP server, it will open a browser for OAuth.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_OAUTH_CREDENTIALS` | Path to OAuth credentials JSON | `../google-calendar/gcp-oauth.keys.json` |
| `GMAIL_TOKEN_PATH` | Path to store tokens | `./tokens.json` |

## Gmail Search Syntax

Use these in `search_messages` or `list_messages` query:

| Query | Description |
|-------|-------------|
| `from:user@example.com` | From specific sender |
| `to:user@example.com` | To specific recipient |
| `subject:meeting` | Subject contains word |
| `is:unread` | Unread messages |
| `is:starred` | Starred messages |
| `has:attachment` | Has attachments |
| `after:2024/01/01` | After date |
| `before:2024/12/31` | Before date |
| `label:important` | Has label |
| `in:inbox` | In inbox |
| `in:sent` | In sent folder |

## Usage Examples

### List unread messages
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_messages","arguments":{"query":"is:unread","max_results":10}}}' | python3 src/mcp_server.py
```

### Send an email
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send_message","arguments":{"to":"user@example.com","subject":"Hello","body":"Hi there!"}}}' | python3 src/mcp_server.py
```

### Search messages
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_messages","arguments":{"query":"from:boss@company.com has:attachment"}}}' | python3 src/mcp_server.py
```

## MCP Config

This server is configured in `mcp-servers/config.json`:

```json
"gmail": {
  "type": "stdio",
  "command": "python3",
  "args": ["/Users/neeraj/Project/claude-boost/mcp-servers/gmail/src/mcp_server.py"],
  "env": {
    "GOOGLE_OAUTH_CREDENTIALS": "/Users/neeraj/Project/claude-boost/mcp-servers/google-calendar/gcp-oauth.keys.json",
    "GMAIL_TOKEN_PATH": "/Users/neeraj/Project/claude-boost/mcp-servers/gmail/tokens.json"
  }
}
```

## Security Notes

- `tokens.json` contains access tokens - keep it private (600 permissions set automatically)
- Token file is gitignored and should never be committed
- OAuth credentials are shared with Google Calendar MCP

