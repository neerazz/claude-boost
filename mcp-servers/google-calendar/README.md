# Google Calendar MCP Server

## Table of Contents
- [Features](#features)
- [Available Tools](#available-tools)
- [Files](#files)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Usage Examples](#usage-examples)
- [MCP Config](#mcp-config)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)



A self-contained MCP server for Google Calendar operations. Uses YOUR own OAuth credentials - no external package dependencies.

## Features

- **Self-contained**: Uses only Python standard library (no pip dependencies)
- **Your own OAuth credentials**: Uses your GCP project's OAuth client, not a third-party
- **Full MCP protocol support**: Works with Cursor, Claude Desktop, Claude Code, Gemini CLI
- **Complete calendar operations**: List, create, update, delete, search events

## Available Tools

| Tool | Description |
|------|-------------|
| `list_calendars` | List all accessible Google Calendars |
| `list_events` | List events from a calendar (with time range filtering) |
| `get_event` | Get details of a specific event |
| `create_event` | Create a new calendar event |
| `update_event` | Update an existing event |
| `delete_event` | Delete an event |
| `search_events` | Search events by text query |
| `get_free_busy` | Get free/busy information for calendars |

## Files

```
google-calendar/
├── src/
│   └── mcp_server.py     # MCP server implementation
├── gcp-oauth.keys.json   # Your OAuth credentials (from GCP Console)
├── tokens.json           # OAuth tokens (auto-generated)
├── requirements.txt      # Dependencies (none required)
└── README.md            # This file
```

## Setup

### 1. Create OAuth Credentials in GCP

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth client ID**
5. Select **Desktop app** as application type
6. Download the JSON file
7. Save it as `gcp-oauth.keys.json` in this directory

### 2. Enable Google Calendar API

1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Calendar API"
3. Click **Enable**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Add your email to **Test users** (if in Testing mode)

### 4. First Authentication

The first time you use the MCP server, it will:
1. Open a browser for Google OAuth login
2. Ask you to grant calendar permissions
3. Save the tokens to `tokens.json`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_OAUTH_CREDENTIALS` | Path to OAuth credentials JSON | `./gcp-oauth.keys.json` |
| `GOOGLE_CALENDAR_TOKEN_PATH` | Path to store tokens | `./tokens.json` |

## Usage Examples

### List calendars
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_calendars","arguments":{}}}' | python3 src/mcp_server.py
```

### List upcoming events
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_events","arguments":{"max_results":10}}}' | python3 src/mcp_server.py
```

### Create an event
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"create_event","arguments":{"summary":"Team Meeting","start":"2024-01-15T10:00:00-08:00","end":"2024-01-15T11:00:00-08:00","description":"Weekly sync"}}}' | python3 src/mcp_server.py
```

### Search events
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_events","arguments":{"query":"meeting"}}}' | python3 src/mcp_server.py
```

## MCP Config

This server is configured in `mcp-servers/config.json`:

```json
"google-calendar": {
  "type": "stdio",
  "command": "python3",
  "args": ["/Users/neeraj/Project/claude-boost/mcp-servers/google-calendar/src/mcp_server.py"],
  "env": {
    "GOOGLE_OAUTH_CREDENTIALS": "/Users/neeraj/Project/claude-boost/mcp-servers/google-calendar/gcp-oauth.keys.json",
    "GOOGLE_CALENDAR_TOKEN_PATH": "/Users/neeraj/Project/claude-boost/mcp-servers/google-calendar/tokens.json"
  }
}
```

## Troubleshooting

### "OAuth credentials file not found"
Make sure `gcp-oauth.keys.json` exists and is readable.

### "Token expired" or refresh errors
Delete `tokens.json` and re-authenticate.

### "Access blocked: This app is blocked"
This shouldn't happen with your own credentials, but if it does:
1. Make sure you're using YOUR OWN GCP project credentials
2. Ensure your email is added as a Test User in OAuth consent screen
3. Or publish your OAuth app for production use

### "Invalid grant" error
The refresh token may have expired or been revoked. Delete `tokens.json` and re-authenticate.

## Security Notes

- `gcp-oauth.keys.json` contains your OAuth client secret - keep it private
- `tokens.json` contains access tokens - keep it private (600 permissions set automatically)
- Both files are gitignored and should never be committed

