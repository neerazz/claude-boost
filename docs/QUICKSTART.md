# Quick Start Guide

Get started with the Claude Boost framework in 5 minutes.

## Prerequisites

- Python 3.10+
- Claude Code CLI or compatible AI agent

## Setup

1. Clone this repository
2. Review the skill structure in `skills/`
3. Understand the hook system in `hooks/`

## Your First Skill Execution

### 1. Check Pre-flight
```bash
python3 tools/preflight_gate.py
```

### 2. Invoke a Skill

Skills are invoked through the AI agent. Example:
```
/skill clear-thinking-gate
```

### 3. Run Post-hook
```bash
python3 tools/post_hook.py
```

## Understanding Skills

Each skill has:
- `SKILL.md` - Main definition with execution protocol
- `examples/` - Usage examples (optional)
- `scripts/` - Supporting Python code (optional)
- `reference/` - Additional documentation (optional)

## Key Skills to Explore

| Skill | Purpose |
|-------|---------|
| `clear-thinking-gate` | Pre-execution validation |
| `self-critique-gate` | Post-execution quality check |
| `visualization` | Smart diagram/chart routing |
| `gap-analyzer` | Gap analysis utility |

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Read [SKILL_ANATOMY.md](SKILL_ANATOMY.md) for skill structure
- Explore the sample skills in `skills/`
