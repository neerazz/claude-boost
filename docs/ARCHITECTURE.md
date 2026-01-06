# Architecture Overview

## System Design

The Claude Boost framework follows a layered architecture for AI agent capabilities.

```
┌─────────────────────────────────────────────────────────────┐
│                     User Request                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Hooks Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Pre-Execute │  │  On-Error   │  │    Post-Execute     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Skills Layer                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │    L3 Orchestrators (complex multi-step flows)      │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │    L2 Composite (combine L1 skills)                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │    L1 Atomic (single-purpose gates, validators)     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Tools Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Preflight  │  │  Post-hook  │  │      Utilities      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Hooks Layer
- Intercept execution at key points
- Validate inputs and outputs
- Enforce quality gates

### Skills Layer
- **L1 (Atomic)**: Single-purpose, no dependencies
- **L2 (Composite)**: Combine L1 skills with logic
- **L3 (Orchestrator)**: Complex workflows with multiple skills

### Tools Layer
- Python automation scripts
- State management
- External integrations

## Data Flow

1. User request enters through hooks
2. Pre-execute hook validates and routes
3. Skill executes with quality gates
4. Post-execute hook validates output
5. Tools sync state if needed

## Key Principles

1. **Determinism**: Every execution follows a predictable pattern
2. **Quality Gates**: Pre and post validation on every skill
3. **Composability**: Build complex behaviors from simple parts
4. **Observability**: Track execution state and metrics
