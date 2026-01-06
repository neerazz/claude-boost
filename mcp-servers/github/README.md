# GitHub MCP Server

## Table of Contents
- [Why This Exists](#why-this-exists)
- [Setup](#setup)
- [Available Tools (35+)](#available-tools-35+)
- [Usage with Skills](#usage-with-skills)
- [Search Query Examples](#search-query-examples)
- [MCP Config](#mcp-config)
- [Security Notes](#security-notes)



A comprehensive, self-contained MCP server for GitHub operations. Works independently of any admin-controlled integrations - uses GitHub REST API directly with your Personal Access Token.

## Why This Exists

Unlike GitHub Apps or OAuth integrations that can be disabled by organization admins, this MCP uses your Personal Access Token (PAT) directly. This means:

- ✅ **Admin-independent**: Works even if org admins disable GitHub integrations
- ✅ **Full access**: Access all repos you can access via git/browser
- ✅ **Zero dependencies**: Pure Python, no external packages
- ✅ **Self-contained**: Everything in one file

## Setup

### 1. Create a Personal Access Token (PAT)

Go to [GitHub Settings → Tokens](https://github.com/settings/tokens) and create a new token.

**Classic PAT scopes needed:**
- `repo` - Full repository access
- `read:org` - Organization access
- `read:user` - User profile access
- `security_events` - Security alerts
- `workflow` - GitHub Actions
- `read:discussion` - Discussions (optional)

**Or use Fine-grained PAT with:**
- Contents: Read
- Pull requests: Read and Write
- Issues: Read and Write
- Security alerts: Read
- Actions: Read

### 2. Configure Environment

Add to `~/.config/mcp-servers/.env`:

```bash
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_ORG=your-org    # Optional: default org
GITHUB_USER=your-username  # Optional: default user
```

Then sync: `python3 tools/mcp_sync.py env-sync`

## Available Tools (35+)

### Pull Requests
| Tool | Description |
|------|-------------|
| `list_prs` | List PRs for a repository |
| `get_pr` | Get detailed PR info |
| `search_prs` | Search PRs across repos |
| `create_pr` | Create a pull request |
| `merge_pr` | Merge a PR |
| `pr_reviews` | Get PR reviews |
| `request_reviewers` | Request reviewers |

### Issues
| Tool | Description |
|------|-------------|
| `list_issues` | List issues |
| `get_issue` | Get issue details |
| `search_issues` | Search issues |
| `create_issue` | Create an issue |
| `update_issue` | Update an issue |
| `add_comment` | Add comment |

### Repositories
| Tool | Description |
|------|-------------|
| `list_repos` | List repos for user/org |
| `get_repo` | Get repo details |
| `list_commits` | List commits |
| `list_releases` | List releases |
| `get_file` | Get file contents |
| `list_branches` | List branches |

### Security Alerts
| Tool | Description |
|------|-------------|
| `dependabot_alerts` | Dependabot alerts |
| `code_scanning_alerts` | CodeQL alerts |
| `secret_scanning_alerts` | Secret alerts |

### Workflows/Actions
| Tool | Description |
|------|-------------|
| `list_workflows` | List workflows |
| `list_workflow_runs` | List workflow runs |
| `get_workflow_run` | Get run details |
| `rerun_workflow` | Re-run a workflow |

### User & Notifications
| Tool | Description |
|------|-------------|
| `get_user` | Get user profile |
| `get_authenticated_user` | Get your profile |
| `list_orgs` | List your organizations |
| `list_notifications` | List notifications |

### Search
| Tool | Description |
|------|-------------|
| `search_code` | Search code |
| `search_repos` | Search repositories |
| `search_users` | Search users |

## Usage with Skills

The `github-work-intelligence` skill can use this MCP:

```javascript
// Search PRs
mcp_github_search_prs({
  query: "is:open author:your-username org:your-org"
})

// Get security alerts
mcp_github_dependabot_alerts({
  owner: "your-org",
  repo: "your-repo",
  state: "open",
  severity: "critical"
})

// Check CI status
mcp_github_list_workflow_runs({
  owner: "your-org",
  repo: "your-repo",
  actor: "your-username",
  status: "failure"
})
```

## Search Query Examples

### PRs
```
is:open author:username org:orgname
is:open review-requested:username
is:merged merged:>2024-01-01
label:bug org:orgname
```

### Issues
```
is:open assignee:username org:orgname
is:issue label:bug org:orgname
mentions:username org:orgname
```

### Code
```
function_name repo:owner/repo
import requests language:python org:orgname
TODO extension:py org:orgname
```

## MCP Config

This server is configured in `mcp-servers/config.json`:

```json
"github": {
  "type": "stdio",
  "command": "python3",
  "args": ["mcp-servers/github/src/mcp_server.py"],
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",
    "GITHUB_ORG": "your-org",
    "GITHUB_USER": "your-username"
  }
}
```

## Security Notes

- PAT is sensitive - never commit to git
- Use fine-grained PATs when possible (more secure)
- PAT gives same access as your account - be careful with write operations
- Consider using a PAT with minimal required scopes
