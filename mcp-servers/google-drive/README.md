# Google Drive MCP Server

## Table of Contents
- [Features](#features)
- [Available Tools](#available-tools)
- [Files](#files)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [File Reading](#file-reading)
- [Usage Examples](#usage-examples)
- [MCP Config](#mcp-config)
- [Security Notes](#security-notes)



A self-contained MCP server for Google Drive operations. Uses YOUR own OAuth credentials - no external package dependencies.

## Features

- **Self-contained**: Uses only Python standard library (no pip dependencies)
- **Your own OAuth credentials**: Uses your GCP project's OAuth client
- **Full MCP protocol support**: Works with Cursor, Claude Desktop, Claude Code, Gemini CLI
- **Complete file operations**: List, read, create, update, delete, share files
- **Shared Drive support**: Access files in Google Workspace Team Drives / Shared Drives

## Available Tools

| Tool | Description |
|------|-------------|
| `list_files` | List files and folders |
| `get_file` | Get file metadata |
| `search_files` | Search for files by name or content |
| `read_file` | Read file content (text, Google Docs/Sheets/Slides) |
| `create_file` | Create a new file |
| `create_folder` | Create a new folder |
| `update_file` | Update file content or metadata |
| `delete_file` | Delete (trash) a file |
| `move_file` | Move file to different folder |
| `copy_file` | Copy a file |
| `share_file` | Share file with users |
| `get_file_permissions` | Get sharing permissions |

## Files

```
google-drive/
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

### 2. Enable Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **APIs & Services** → **Library**
3. Search for "Google Drive API"
4. Click **Enable**

### 3. OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Add Drive scopes:
   - `drive` (full access)
   - `drive.file` (files created by app)
   - `drive.metadata.readonly`
3. Add your email to **Test users** (if in Testing mode)

### 4. First Authentication

The first time you use the MCP server, it will open a browser for OAuth.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_OAUTH_CREDENTIALS` | Path to OAuth credentials JSON | `../google-calendar/gcp-oauth.keys.json` |
| `GOOGLE_DRIVE_TOKEN_PATH` | Path to store tokens | `./tokens.json` |

## File Reading

The `read_file` tool handles different file types:

| File Type | Export Format |
|-----------|---------------|
| Google Docs | Plain text |
| Google Sheets | CSV |
| Google Slides | Plain text |
| Text files | UTF-8 text |
| Binary files | Base64 encoded |

## Usage Examples

### List files in root
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_files","arguments":{"max_results":20}}}' | python3 src/mcp_server.py
```

### Search for files
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_files","arguments":{"query":"project report","file_type":"document"}}}' | python3 src/mcp_server.py
```

### Read a Google Doc
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_file","arguments":{"file_id":"1a2b3c4d5e"}}}' | python3 src/mcp_server.py
```

### Create a file
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"create_file","arguments":{"name":"notes.txt","content":"My notes here"}}}' | python3 src/mcp_server.py
```

### Share a file
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"share_file","arguments":{"file_id":"1a2b3c4d5e","email":"user@example.com","role":"reader"}}}' | python3 src/mcp_server.py
```

## MCP Config

This server is configured in `mcp-servers/config.json`:

```json
"google-drive": {
  "type": "stdio",
  "command": "python3",
  "args": ["/Users/neeraj/Project/claude-boost/mcp-servers/google-drive/src/mcp_server.py"],
  "env": {
    "GOOGLE_OAUTH_CREDENTIALS": "/Users/neeraj/Project/claude-boost/mcp-servers/google-calendar/gcp-oauth.keys.json",
    "GOOGLE_DRIVE_TOKEN_PATH": "/Users/neeraj/Project/claude-boost/mcp-servers/google-drive/tokens.json"
  }
}
```

## Security Notes

- `tokens.json` contains access tokens - keep it private (600 permissions set automatically)
- Token file is gitignored and should never be committed
- OAuth credentials are shared with Google Calendar MCP
- Be careful with `delete_file` using `permanent=true` - there's no undo!

