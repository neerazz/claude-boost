
# Contributor Guide: Building with Claude Boost

Thank you for your interest in contributing to **Claude Boost**! This guide details our repository structure, conventions, and development workflow for engineers and AI researchers.

## Repository Structure

- `skills/`: The heart of the framework. Contains self-contained AI capability definitions.
- `hooks/`: Interceptors that run before or after skill execution.
- `tools/`: Python automation scripts for orchestration and synchronization.
- `mcp-servers/`: Individual MCP server implementations for external tool access (Slack, GitHub, etc.).
- `data/`: Stores state, audit logs, and the skill DAG (Directed Acyclic Graph).
- `memory/`: Long-term context storage for agent weightage and learnings.
- `docs/`: Deep dive documentation and architectural diagrams.

## Creating a New Skill

A skill must be a self-contained directory in `skills/` with the following structure:

```
new-skill/
├── SKILL.md         # REQUIRED: The protocol and contract
├── examples/        # HIGHLY RECOMMENDED: Usage samples
├── scripts/         # OPTIONAL: Deterministic Python logic
└── reference/       # OPTIONAL: Supporting documentation
```

### The `SKILL.md` Contract

Every `SKILL.md` must follow the [Skill Anatomy](SKILL_ANATOMY.md) template, including:
1. **Frontmatter**: Name, description, layer, and type.
2. **Execution Protocol**: A deterministic state machine.
3. **Mandatory Checklist**: Steps the agent must verify.
4. **Input/Output Contracts**: Precise definitions of data structures.
5. **Quality Gates**: Success thresholds (e.g., ≥90%).

## Contribution Workflow

1. **Fork and Branch**: Create a feature branch for your changes.
2. **Develop Skill**: Follow the self-containment principle (no external file references).
3. **Run Pre-flight**: Ensure your environment is valid.
   ```bash
   python3 tools/preflight_gate.py
   ```
4. **Test Implementation**: Manually verify the skill behavior with an AI agent.
5. **Sync Metadata**: Run the mandatory post-hook to update the DAG and keywords.
   ```bash
   python3 tools/post_hook.py
   ```
6. **Lint and Validate**: Ensure your `SKILL.md` body is under 500 lines and follows best practices.

## Coding Standards (Axiom #4)

**Code Before Prompts**: Use Python scripts in `tools/` or a skill's `scripts/` directory for any deterministic data transformations or state management. Reserve natural language prompts for reasoning and synthesis.

## Integration with MCP

When your skill requires external data (e.g., from Slack or Notion), ensure the corresponding MCP server is configured in `mcp-servers/`. Use fully qualified tool names: `mcp_<ServerName>_<tool_name>`.

## Support and Feedback

- Report bugs or suggest improvements via issues.
- Join our community discussions to share your research and new skill patterns.
