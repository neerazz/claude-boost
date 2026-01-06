# Skill Anatomy

A complete guide to understanding and creating skills.

## Skill Structure

```
skill-name/
├── SKILL.md         # Main definition (required)
├── examples/        # Usage examples (optional)
├── scripts/         # Python support code (optional)
└── reference/       # Additional docs (optional)
```

## SKILL.md Template

```markdown
---
name: skill-name
description: What the skill does
layer: L1-Atomic | L2-Composite | L3-Orchestrator
type: gate | utility | orchestrator
version: 1.0.0
---

# Skill Name

## Deterministic Execution Protocol

### Execution State Machine
[Define states and transitions]

### Mandatory Checklist
[Steps that must complete]

## Input Contract
[What the skill expects]

## Output Contract
[What the skill returns]

## Quality Metrics
[How success is measured]
```

## Execution Protocol

Every skill follows this pattern:

```
EXECUTION_STATE = {
  "phase_1_initialized": false,
  "phase_2_executed": false,
  "phase_3_validated": false,
  "output_validated": false,
  "quality_gate_passed": false
}

# DO NOT RETURN until ALL values are TRUE
```

## Layer Guidelines

### L1 - Atomic Skills
- Single responsibility
- No external dependencies
- Example: `clear-thinking-gate`, `self-critique-gate`

### L2 - Composite Skills
- Combine L1 skills
- Add business logic
- Example: `visualization`

### L3 - Orchestrators
- Complex multi-step workflows
- Coordinate multiple L2 skills
- Example: `journal-orchestrator`

## Quality Thresholds

| Layer | Minimum Score |
|-------|--------------|
| L1    | 90%          |
| L2    | 85%          |
| L3    | 80%          |

## Best Practices

1. **Clear contracts**: Define inputs/outputs precisely
2. **Mandatory checklists**: Ensure all steps complete
3. **Quality metrics**: Measure and report success
4. **Error handling**: Define failure actions
5. **Documentation**: Include examples and references
