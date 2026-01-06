# Claude Boost - AI Agent Framework Samples

A collection of sample skills, hooks, and tools demonstrating how to build deterministic AI agent workflows with Claude Code.

## Overview

This repository showcases patterns for creating structured, reproducible AI agent behaviors using:

- **Skills**: Reusable, composable AI capabilities with clear contracts
- **Hooks**: Pre/post execution gates for quality control
- **Tools**: Automation scripts for workflow orchestration

## Directory Structure

```
claude-boost-public/
├── skills/              # Sample AI skill definitions
│   ├── clear-thinking-gate/   # Pre-execution validation
│   ├── self-critique-gate/    # Post-execution quality check
│   ├── visualization/         # Intelligent diagram/chart routing
│   └── gap-analyzer/          # Gap analysis utility
├── hooks/               # Execution hooks documentation
│   ├── README.md
│   └── HOOKS.md
├── tools/               # Automation scripts
│   ├── post_hook.py     # Post-execution sync
│   └── preflight_gate.py
├── docs/                # Documentation
│   ├── ARCHITECTURE.md
│   ├── SKILL_ANATOMY.md
│   └── QUICKSTART.md
└── AGENTS.md            # Agent behavior rules
```

## Key Concepts

### Skills

Skills are self-contained AI capabilities with:
- Clear input/output contracts
- Deterministic execution protocols
- Quality gates and validation

### Hooks

Hooks intercept execution at key points:
- **Pre-execute**: Validate inputs, check constraints
- **Post-execute**: Verify outputs, sync state

### Tools

Python scripts for:
- State synchronization
- Pre-flight validation
- Workflow automation

## Getting Started

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for setup instructions.

## License

MIT License - See LICENSE file for details.
