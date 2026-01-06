# Commands and Hooks Reference

This directory contains definitions and examples for the CLI commands and execution hooks that orchestrate the framework.

## CLI Commands

Commands are the primary way to interact with the framework from the terminal or an AI agent.

| Command | Description | Implementation |
|---------|-------------|----------------|
| `/skill <name>` | Invoke a specific skill by name | `tools/upo_router.py` |
| `/journal` | Start a planning cycle (daily/weekly/monthly) | `skills/journal-orchestrator/` |
| `/self-learn` | Analyze data and generate improvements | `skills/self-learn/` |
| `/help` | Display usage information | Built-in |

### Example Usage

```bash
# Run a gap analysis on your profile
/skill gap-analyzer

# Start your daily planning routine
/journal daily-start
```

## Execution Hooks

Hooks intercept execution to enforce rules or synchronize state.

### 1. Pre-execution Gates
Implemented in `tools/preflight_gate.py`.
- **Purpose**: Verify environment variables, MCP server status, and user auth before work starts.
- **Rule**: Must be called at the beginning of every session.

### 2. Post-execution Sync (Mandatory)
Implemented in `tools/post_hook.py`.
- **Purpose**: Synchronize the Skill DAG, update metadata, and log execution metrics.
- **MANDATORY**: Run after every skill modification or significant task.

### 3. Response Enhancement
Hooks in `hooks/HOOKS.md` detail how to enhance AI responses with abstraction layers and validation stages.

## Protocol for Adding a Command

1. Create a new directory in `commands/` (e.g., `commands/my-command/`).
2. Add a `COMMAND.md` file following the standard template.
3. Register any required keywords in `data/dag/keyword_skill_mapping.json`.
4. Update this `README.md` with the new command.

## Quality Gates

All commands and hooks must meet a **95% quality bar**. Failure to include required audit logs or skip mandatory validation will result in a `GATE_FAIL` signal.