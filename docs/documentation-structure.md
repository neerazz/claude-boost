
# Documentation Structure

This document outlines the standard hierarchical structure for project documentation, ensuring clarity for both new users and contributors. All documentation should adhere to this convention.

## Core Documents

### README.md
- **Purpose**: Top-level entry point and overview.
- **Audience**: All users (beginners, contributors, stakeholders).
- **Content**: Quick start guide, project mission, main features, navigation to deeper docs.

### docs/
- **Purpose**: Deep dive into specific aspects of the project.
- **Subdirectories**:
    - `architecture.md`: High-level system design, data flow, agent interactions, MCP integration.
    - `user-guide.md`: For end-users unfamiliar with AI/Claude. Explains core concepts, basic commands, and tool usage.
    - `contributor-guide.md`: For new contributors. Details repo structure, file conventions, contribution workflow, testing, and dev environment setup.
    - `reference/`: Supporting data, schemas, templates.
    - `examples/`: Practical usage walkthroughs and demonstrations.
    - `workflow-diagrams.md`: Visualizations of key processes.

### skills/*/SKILL.md
- **Purpose**: Detailed instructions and metadata for each individual skill.
- **Content**: Skill description, parameters, output contract, quality gates, dependencies, invocation examples.
- **Example**: `skills/slack-intelligence/SKILL.md`

### commands/
- **Purpose**: Reference for CLI commands and hooks.
- **Structure**:
    - `README.md`: Overview of command-line usage.
    - `hooks/`: Post-response hooks and pre-execution gates.
    - `examples/`: Usage examples for commands.

### agents/
- **Purpose**: Defines specialist agent personas and behaviors.
- **Content**: Each agent has a Markdown file detailing its role, weight, veto power, and focus.
- **Example**: `agents/researcher.md`, `agents/critique-agent.md`

## File Conventions

- Use Markdown (`.md`) for all documentation.
- Use Mermaid diagrams for architecture and flow visualization.
- Adhere to `AGENTS.md` for agent personas and behavior guidelines.
- Version control all documentation changes.

## Foundational Documents

- **AGENTS.md**: The ultimate source of truth for agent behavior and governance.
- **docs/AXIOMS.md**: Detailed explanation of core operating principles.
- **LICENSE**: Project licensing information.
- **README.md**: High-level project overview.
