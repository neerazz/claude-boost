# Auth0 MCP Server

## Table of Contents
- [Features](#features)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Available Tools](#available-tools)
- [Search Syntax](#search-syntax)
- [Usage Examples](#usage-examples)
- [MCP Config](#mcp-config)
- [Security Notes](#security-notes)



A self-contained MCP server for Auth0 Management API operations. Uses client credentials flow for authentication.

## Features

- **Zero dependencies**: Uses only Python standard library
- **Token caching**: Automatic token refresh
- **Complete Management API**: Users, applications, connections, roles, logs

## Setup

### 1. Create Machine-to-Machine Application

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. **Applications** → **Create Application**
3. Select **Machine to Machine Applications**
4. Name it (e.g., "MCP Server")

### 2. Authorize for Management API

1. In the new application, go to **APIs** tab
2. Find **Auth0 Management API**
3. Toggle to **Authorized**
4. Select scopes you need:
   - `read:users`, `update:users`, `create:users`, `delete:users`
   - `read:clients`
   - `read:connections`
   - `read:roles`, `update:roles`
   - `read:logs`
   - `read:stats`

### 3. Configure Environment Variables

Add to `~/.config/mcp-servers/.env`:

```bash
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
```

Then sync: `python3 tools/mcp_sync.py env-sync`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AUTH0_DOMAIN` | Your Auth0 domain | Yes |
| `AUTH0_CLIENT_ID` | M2M application client ID | Yes |
| `AUTH0_CLIENT_SECRET` | M2M application client secret | Yes |

## Available Tools

| Tool | Description |
|------|-------------|
| `list_users` | List users with search and pagination |
| `get_user` | Get user details |
| `create_user` | Create a new user |
| `update_user` | Update user properties |
| `delete_user` | Delete a user |
| `list_applications` | List Auth0 applications |
| `get_application` | Get application details |
| `list_connections` | List identity connections |
| `list_roles` | List defined roles |
| `get_role` | Get role details |
| `assign_roles` | Assign roles to user |
| `list_apis` | List API/Resource Servers |
| `get_logs` | Get authentication logs |
| `get_stats` | Get tenant statistics |

## Search Syntax

The `list_users` and `get_logs` tools support Lucene query syntax:

```
# Users by email domain
email:*@example.com

# Users created after date
created_at:[2024-01-01 TO *]

# Users with specific metadata
app_metadata.role:admin

# Combine with AND/OR
email:*@example.com AND blocked:false
```

## Usage Examples

### List users
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_users","arguments":{"per_page":10}}}' | python3 src/mcp_server.py
```

### Search users
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_users","arguments":{"query":"email:*@example.com","per_page":20}}}' | python3 src/mcp_server.py
```

### Get user
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user","arguments":{"user_id":"auth0|123456789"}}}' | python3 src/mcp_server.py
```

### Get recent logs
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_logs","arguments":{"per_page":20}}}' | python3 src/mcp_server.py
```

## MCP Config

This server is configured in `mcp-servers/config.json`:

```json
"auth0": {
  "type": "stdio",
  "command": "python3",
  "args": ["/Users/neeraj/Project/claude-boost/mcp-servers/auth0/src/mcp_server.py"],
  "env": {
    "AUTH0_DOMAIN": "${AUTH0_DOMAIN}",
    "AUTH0_CLIENT_ID": "${AUTH0_CLIENT_ID}",
    "AUTH0_CLIENT_SECRET": "${AUTH0_CLIENT_SECRET}"
  }
}
```

## Security Notes

- Client secret is sensitive - never commit to git
- Use minimal scopes for the M2M application
- Review logs regularly for unauthorized access
- The `delete_user` action is permanent

