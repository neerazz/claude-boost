# Commands

Commands are user-invocable workflows that orchestrate multiple skills.

## Structure

```
commands/
├── command-name/
│   ├── COMMAND.md      # Main definition
│   ├── sessions/       # Session-specific configs
│   └── scripts/        # Supporting code
└── README.md
```

## Command vs Skill

| Aspect | Command | Skill |
|--------|---------|-------|
| Invocation | `/command-name` | Internal |
| Purpose | User workflow | Reusable capability |
| Scope | Full session | Single task |

## Sample Command

See `sample-workflow/` for a basic example.
