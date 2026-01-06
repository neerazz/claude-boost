# Hooks System

## Table of Contents
- [Overview](#overview)
- [Hook Types](#hook-types)
- [Hook Files](#hook-files)
- [Agent Support](#agent-support)
- [Using Hooks](#using-hooks)
- [Hook Execution Order](#hook-execution-order)
- [Best Practices](#best-practices)
- [Debugging Hooks](#debugging-hooks)



> **Context narrowing and quality control** for AI commands across all agents.

## Overview

Hooks allow you to control what the AI sees and does at each stage of command execution. This significantly improves output quality by:

1. **Narrowing context** - Only relevant files/databases are loaded
2. **Validating prerequisites** - Ensure required data exists before proceeding
3. **Enforcing quality gates** - Block execution if standards aren't met
4. **Logging & auditing** - Track all command executions

## Hook Types

```
┌──────────────────────────────────────────────────────────────────┐
│                      COMMAND EXECUTION                           │
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PRE-READ    │    │ PRE-EXECUTE  │    │ POST-EXECUTE │
│              │    │              │    │              │
│ • Context    │ ──▶│ • Validate   │ ──▶│ • Log        │
│   boundaries │    │   prereqs    │    │ • Sync       │
│ • File       │    │ • Load DBs   │    │ • Notify     │
│   patterns   │    │ • Check      │    │ • Clean up   │
│ • Exclusions │    │   connections│    │              │
└──────────────┘    └──────────────┘    └──────────────┘
                              │
                              │ (on failure)
                              ▼
                    ┌──────────────┐
                    │   ON-ERROR   │
                    │              │
                    │ • Fallbacks  │
                    │ • Logging    │
                    │ • Recovery   │
                    └──────────────┘
```

## Hook Files

| File | Purpose | When |
|------|---------|------|
| `pre-read.md` | Define context boundaries | Before any file/DB reading |
| `pre-execute.md` | Validate prerequisites | Before command logic runs |
| `post-execute.md` | Clean up and sync | After successful execution |
| `on-error.md` | Handle failures | On any error during execution |

## Agent Support

| Agent | Pre-Read | Pre-Execute | Post-Execute | On-Error |
|-------|----------|-------------|--------------|----------|
| Claude Code | ✅ | ✅ | ✅ | ✅ |
| Cursor | ✅ | ✅ | ⚠️ Partial | ⚠️ Partial |
| Gemini CLI | ✅ | ✅ | ❌ | ❌ |
| Codex | ⚠️ Basic | ⚠️ Basic | ❌ | ❌ |

## Using Hooks

### In Command Definitions

```yaml
# COMMAND.md frontmatter
hooks:
  pre-read: true      # Enable pre-read hook
  pre-execute: true   # Enable pre-execute hook
  post-execute: true  # Enable post-execute hook
  on-error: true      # Enable error handler
```

### Custom Hook Configuration

```yaml
# Override default hooks
hooks:
  pre-read:
    include: ["commands/journal/**", "skills/journal-orchestrator/**"]
    exclude: ["node_modules/**", ".git/**", "**/*.log"]
  pre-execute:
    require: ["notion-connection", "persona-fetch"]
    warn: ["slack-connection", "aws-connection"]
```

## Hook Execution Order

```
1. Pre-Read Hook
   ├── Set include patterns
   ├── Set exclude patterns
   └── Define database scope

2. Context Loading
   ├── Load only matching files
   └── Connect to specified databases

3. Pre-Execute Hook
   ├── Validate required connections
   ├── Fetch mandatory data
   └── Check quality gates

4. Command Execution
   ├── Run command logic
   └── Generate output

5. Post-Execute Hook
   ├── Log to operational/
   ├── Sync to Notion
   └── Send notifications

6. On-Error Hook (if needed)
   ├── Log error details
   ├── Attempt fallbacks
   └── Notify user
```

## Best Practices

### 1. Be Specific with Patterns
```javascript
// Good - specific patterns
include: [
  "skills/journal-orchestrator/**",
  "commands/journal/**"
]

// Bad - too broad
include: ["**/*"]
```

### 2. Always Exclude Common Noise
```javascript
exclude: [
  "node_modules/**",
  ".git/**",
  "**/*.log",
  "**/*.lock",
  ".env*"
]
```

### 3. Gate on Critical Data
```javascript
// MUST have - stop if missing
require: ["persona", "journal-db"]

// SHOULD have - warn if missing
warn: ["slack", "github"]
```

### 4. Log Everything
```javascript
// Always log to operational/
postExecute: {
  log: true,
  logDir: "operational/{date}/",
  logFormat: "markdown"
}
```

## Debugging Hooks

### Check Hook Execution
```bash
# Claude Code
claude --verbose /journal daily-start

# Cursor (check output panel)
# Gemini CLI
gemini --debug /journal daily-start
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Context too large | Patterns too broad | Narrow include patterns |
| Missing data | Required fetch failed | Check connections |
| Slow execution | Too many exclusions | Simplify patterns |
| Hook not running | Wrong config format | Check YAML syntax |
