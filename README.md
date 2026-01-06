# Claude Boost - AI Agent Framework Samples

A collection of sample skills, hooks, and tools demonstrating how to build deterministic AI agent workflows with Claude Code.

## 🚀 Getting Started

- **[User Guide](docs/user-guide.md)**: New to AI agents? Start here.
- **[Quick Start](docs/quickstart.md)**: 5-minute setup guide.
- **[Architecture Deep Dive](docs/architecture.md)**: How the system works under the hood.
- **[Contributor Guide](docs/contributor-guide.md)**: Join us in building better agent patterns.

## Overview

This repository showcases patterns for creating structured, reproducible AI agent behaviors using:

- **Skills**: Reusable, composable AI capabilities with clear contracts.
- **Hooks**: Pre/post execution gates for quality control.
- **Tools**: Automation scripts for workflow orchestration.

## 📁 Directory Structure

```
claude-boost/
├── skills/              # Sample AI skill definitions
│   ├── clear-thinking-gate/   # Pre-execution validation
│   ├── self-critique-gate/    # Post-execution quality check
│   ├── visualization/         # Intelligent diagram/chart routing
│   └── gap-analyzer/          # Gap analysis utility
├── commands/            # CLI usage and command reference
│   └── README.md
├── hooks/               # Execution hooks documentation
│   └── HOOKS.md
├── tools/               # Automation scripts
│   ├── post_hook.py     # Post-execution sync
│   └── preflight_gate.py
├── docs/                # Deep-dive documentation
│   ├── architecture.md
│   ├── user-guide.md
│   ├── contributor-guide.md
│   └── skill-anatomy.md
└── AGENTS.md            # Agent behavior rules (Source of Truth)
```

## 🌐 External Resources

As this repository focuses on framework samples, some foundational concepts are better covered in official documentation:

- **[Claude Code Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code)**: Learn about the CLI tool that powers these workflows.
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)**: The open standard for connecting AI models to data sources.
- **[Anthropic Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)**: Official guidelines for building high-quality agent skills.

## License

MIT License - See LICENSE file for details.
