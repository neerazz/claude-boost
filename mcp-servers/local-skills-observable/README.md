# Observable Local Skills MCP Server

A custom MCP server that wraps skill retrieval with **real-time observability events**.

## Why This Exists

The standard `local-skills-mcp` package serves skill files but has **no observability hooks**. When AI agents (Gemini CLI, Claude Code, Cursor) retrieve skills, there's no way to track:
- Which skills are being used
- How often each skill is invoked
- Success/failure rates
- Response times

This server solves that by emitting events to `/tmp/claude-boost/observability/events.jsonl` for every skill retrieval.

## Features

- **Skill Retrieval**: Same functionality as `local-skills-mcp`
- **Real-Time Events**: Emits SKILL_START and SKILL_END events
- **Token Tracking**: Counts approximate tokens in skill content
- **Error Handling**: Emits SKILL_ERROR events on failures
- **Listing**: List all available skills with event tracking

## Installation

```bash
cd mcp-servers/local-skills-observable
pip install -r requirements.txt
```

## Configuration

Update your MCP config to use this server instead of `local-skills-mcp`:

```json
{
  "local-skills": {
    "type": "stdio",
    "command": "python3",
    "args": ["/path/to/mcp-servers/local-skills-observable/src/mcp_server.py"],
    "env": {
      "SKILLS_DIR": "~/.claude/skills"
    }
  }
}
```

## Events Emitted

| Event Type | When |
|------------|------|
| `SKILL_START` | When a skill retrieval begins |
| `SKILL_END` | When a skill is successfully retrieved |
| `SKILL_ERROR` | When skill retrieval fails |

## Viewing Events

Events are written to `/tmp/claude-boost/observability/events.jsonl` and can be viewed in:
1. The Observability Dashboard UI (`http://localhost:3000` → Observability)
2. Real-time via the streaming server (`ws://localhost:8765`)
3. Direct file inspection: `tail -f /tmp/claude-boost/observability/events.jsonl`

## Integration with Observability Dashboard

Start the streaming server to broadcast events to the UI:

```bash
python3 tools/start_observability_server.py
```

The server watches the events file and broadcasts new events via WebSocket.

