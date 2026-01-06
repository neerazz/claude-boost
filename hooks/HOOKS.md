# Hooks - Single Source of Truth

> **Domain Owner**: hooks/
> **Syncs to**: .claude/, .gemini/, .cursor/, .codex/, .agent/

## Structure

```
hooks/
├── scripts/                    ← Shell scripts for AI tool events
│   ├── session_start.sh        ← Runs preflight gate
│   ├── session_end.sh          ← Reminds post_hook
│   └── before_prompt.sh        ← Injects UPO reminder
│
├── pre-execute.md              ← Conceptual: Before task execution
├── pre-execute-deterministic.md ← Conceptual: Deterministic pre-checks
├── post-execute.md             ← Conceptual: After task execution
├── on-error.md                 ← Conceptual: Error handling behavior
├── got-init.md                 ← Conceptual: Graph of Thoughts init
├── upo-init.md                 ← Conceptual: UPO initialization
├── agent-governance.md         ← Conceptual: Agent governance rules
├── skill-architect-hook.md     ← Conceptual: Skill architect triggers
├── roundtable-enforcement.md   ← Conceptual: Roundtable enforcement
│
├── sync.py                     ← Syncs shell hooks to AI tools
├── README.md                   ← Hook system overview
└── HOOKS.md                    ← This file
```

## Two Types of Hooks

### 1. Shell Script Hooks (scripts/)
Actual executable scripts that AI tools run at specific events.

| Script | Purpose | Claude Code Event | Gemini CLI Event |
|--------|---------|-------------------|------------------|
| `session_start.sh` | Run preflight gate, block if incomplete | SessionStart | SessionStart |
| `session_end.sh` | Remind to run post_hook.py | SessionEnd | SessionEnd |
| `before_prompt.sh` | Inject UPO routing reminder | UserPromptSubmit | BeforeAgent |

### 2. Conceptual Behavior Hooks (*.md)
Documentation defining agent behavior at conceptual execution phases.

| Hook | Purpose | When Applied |
|------|---------|--------------|
| `pre-execute.md` | Task decomposition, planning | Before any task |
| `pre-execute-deterministic.md` | Deterministic checks, validation | Before execution |
| `post-execute.md` | Verification, cleanup | After task completion |
| `on-error.md` | Error handling, recovery | On failures |
| `got-init.md` | Initialize Graph of Thoughts | Research/reasoning tasks |
| `upo-init.md` | Initialize Universal Prompt Orchestrator | Session start |
| `agent-governance.md` | Governance rules, constraints | All interactions |
| `skill-architect-hook.md` | Skill modification triggers | Skill changes |
| `roundtable-enforcement.md` | Multi-agent enforcement | Roundtable sessions |

## Exit Code Convention (Shell Hooks)

- `0` = Success (stdout shown as context)
- `2` = Blocking error (stderr shown, operation blocked)
- Other = Non-blocking warning

## Sync Targets

| AI Tool | Has Native Hooks | Settings Location | Hooks Location |
|---------|-----------------|-------------------|----------------|
| **Claude Code** | ✅ Yes | `.claude/settings.json` | (inline in settings) |
| **Gemini CLI** | ✅ Yes | `.gemini/settings.json` | `.gemini/hooks/` |
| **Cursor IDE** | ❌ No | `.cursor/rules/*.mdc` | N/A (rules only) |
| **Codex CLI** | ⚠️ Limited | `.codex/` | N/A |
| **Antigravity** | ❌ No | `.agent/rules/` | N/A (rules only) |

## Commands

```bash
# Sync shell hooks to all AI tools
python3 hooks/sync.py sync

# Check if sync needed
python3 hooks/sync.py check

# Show status
python3 hooks/sync.py status

# Or via post_hook (syncs EVERYTHING)
python3 tools/post_hook.py
```

## How Sync Works

1. **Source**: Shell scripts in `hooks/scripts/`
2. **Transform**: Generates tool-specific config format
3. **Destination**: Writes to each tool's settings location

For tools WITH native hooks (Claude Code, Gemini CLI):
- Settings JSON is updated with hooks configuration
- Scripts are copied to tool-specific locations (Gemini)

For tools WITHOUT native hooks (Cursor, Codex, Antigravity):
- No automatic enforcement
- Relies on dispatcher files and session lock

## Adding New Hooks

### Shell Script Hook
1. Create script in `hooks/scripts/` (use `.sh` extension)
2. Add mapping to `HOOK_MAPPING` in `sync.py`
3. Run `python3 hooks/sync.py sync`

### Conceptual Behavior Hook
1. Create `.md` file in `hooks/`
2. Document the behavior pattern
3. Reference from relevant skills/commands

---

*Self-contained domain. Sync script travels WITH this directory.*
