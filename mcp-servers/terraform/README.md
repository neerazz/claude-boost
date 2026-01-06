# Terraform MCP Server

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Available Tools](#available-tools)
- [Environment Variables](#environment-variables)
- [Safety Features](#safety-features)
- [Usage Examples](#usage-examples)
- [MCP Config](#mcp-config)
- [Security Notes](#security-notes)



A self-contained MCP server for Terraform operations. Executes Terraform CLI commands directly - no Docker required.

## Features

- **No Docker needed**: Direct Terraform CLI execution
- **Zero Python dependencies**: Uses only standard library
- **Full Terraform workflow**: init, plan, apply, destroy, state, workspaces
- **Safety guards**: apply and destroy require explicit `auto_approve=true`

## Prerequisites

Install Terraform CLI:

```bash
# macOS
brew install terraform

# Or download from:
# https://developer.hashicorp.com/terraform/install
```

## Available Tools

| Tool | Description |
|------|-------------|
| `version` | Show Terraform version |
| `init` | Initialize working directory |
| `validate` | Validate configuration |
| `fmt` | Format configuration files |
| `plan` | Generate execution plan |
| `apply` | Apply changes (requires auto_approve) |
| `destroy` | Destroy infrastructure (requires auto_approve) |
| `output` | Show outputs |
| `state_list` | List resources in state |
| `state_show` | Show resource details |
| `workspace_list` | List workspaces |
| `workspace_select` | Select workspace |
| `workspace_new` | Create workspace |
| `providers` | List providers |
| `refresh` | Refresh state |
| `import` | Import existing infrastructure |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TERRAFORM_WORKING_DIR` | Default working directory | Current directory |

## Safety Features

The `apply` and `destroy` commands require `auto_approve=true`:

```json
// ❌ This will fail (safety check)
{"name": "apply", "arguments": {"working_dir": "/path/to/tf"}}

// ✅ This will work
{"name": "apply", "arguments": {"working_dir": "/path/to/tf", "auto_approve": true}}
```

## Usage Examples

### Check version
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"version","arguments":{}}}' | python3 src/mcp_server.py
```

### Initialize and plan
```bash
# Init
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"init","arguments":{"working_dir":"/path/to/terraform"}}}' | python3 src/mcp_server.py

# Plan
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"plan","arguments":{"working_dir":"/path/to/terraform"}}}' | python3 src/mcp_server.py
```

### Apply with variables
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"apply","arguments":{"working_dir":"/path/to/terraform","var":{"region":"us-east-1"},"auto_approve":true}}}' | python3 src/mcp_server.py
```

## MCP Config

This server is configured in `mcp-servers/config.json`:

```json
"terraform": {
  "type": "stdio",
  "command": "python3",
  "args": ["/Users/neeraj/Project/claude-boost/mcp-servers/terraform/src/mcp_server.py"],
  "env": {
    "TERRAFORM_WORKING_DIR": "/Users/neeraj/Project"
  }
}
```

## Security Notes

- Always review `plan` output before `apply`
- The `destroy` command is extremely dangerous
- Consider using targets to limit scope of changes
- Use variable files for sensitive values

