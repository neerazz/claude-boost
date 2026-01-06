# /sample-workflow Command

> **Version**: 1.0.0
> **Type**: Example workflow command
> **Pre-hook**: `hooks/pre-execute.md`
> **Post-hook**: `python3 tools/post_hook.py`

---

## Usage

```bash
/sample-workflow start
/sample-workflow analyze
/sample-workflow report
```

## Workflow

```
┌─────────────────┐
│  Pre-Execute    │
│     Hook        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clear Thinking  │  ← Validate goal
│     Gate        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Main Analysis  │  ← Core work
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Self-Critique   │  ← Validate output
│     Gate        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post-Execute   │
│     Hook        │
└─────────────────┘
```

## Sessions

| Session | Purpose |
|---------|---------|
| `start` | Initialize workflow |
| `analyze` | Run analysis |
| `report` | Generate report |

---

*This is a sample command demonstrating the command structure.*
