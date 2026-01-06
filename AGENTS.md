# AGENTS.md - Agent Behavior Rules

> **Version**: 1.0.0 (Public Sample)
> **Purpose**: Define deterministic agent execution patterns

---

## Core Principles

### 1. Deterministic Execution
Every skill execution follows a predictable pattern:
1. Input validation
2. Pre-execution gate (clear-thinking-gate)
3. Main execution
4. Post-execution validation (self-critique-gate)
5. Output with quality metrics

### 2. Skill Architecture

```
┌─────────────────────────────────────────┐
│           L3 - Orchestrators            │
│  (Complex workflows, multi-skill chains)│
├─────────────────────────────────────────┤
│           L2 - Composite Skills         │
│    (Combine L1 skills, add logic)       │
├─────────────────────────────────────────┤
│           L1 - Atomic Skills            │
│   (Single-purpose, reusable building    │
│    blocks like gates and validators)    │
└─────────────────────────────────────────┘
```

### 3. Quality Gates

Every execution must pass:
- **Pre-gate**: Clear thinking validation (goal clarity, success criteria)
- **Post-gate**: Self-critique (output validation, quality metrics)

---

## Execution Protocol

### Step 1: Pre-flight Check
```bash
python3 tools/preflight_gate.py
```

### Step 2: Execute Skill
Follow the skill's deterministic execution protocol.

### Step 3: Post-execution Sync
```bash
python3 tools/post_hook.py
```

---

## Skill Contract

Every skill must define:
1. **Name**: Unique identifier
2. **Description**: What it does
3. **Layer**: L1, L2, or L3
4. **Inputs**: Expected parameters
5. **Outputs**: Return schema
6. **Quality threshold**: Minimum acceptable score

---

## Example Workflow

```
User Request
    │
    ▼
┌─────────────────┐
│ Clear Thinking  │  ← L1 Gate (validates goal clarity)
│     Gate        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Main Skill     │  ← L2/L3 (actual work)
│   Execution     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Self-Critique   │  ← L1 Gate (validates output quality)
│     Gate        │
└────────┬────────┘
         │
         ▼
    Output + Metrics
```

---

*This is a simplified public sample. Full implementation includes additional axioms and patterns.*
