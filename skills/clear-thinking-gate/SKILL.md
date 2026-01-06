---
name: clear-thinking-gate
description: Processes and mandatory pre-execution gate implementing Axiom #1 (Clear Thinking). All L2/L3 skills MUST call this before execution. Ensures goal clarity, success criteria, constraints, and stakeholders are defined before any action.
layer: L1-Atomic
type: validation-gate
version: 1.0.0
axioms: [1, 3, 9]
---

# Clear Thinking Gate (Axiom #1 Implementation)

## Table of Contents
- [⛔ Deterministic Execution Protocol](#⛔-deterministic-execution-protocol)
- [Why This Matters](#why-this-matters)
- [The 6-Question Gate (MANDATORY)](#the-6-question-gate-mandatory)
- [Quality Score Calculation](#quality-score-calculation)
- [Output Schema](#output-schema)
- [Integration Pattern](#integration-pattern)
- [Life Domain Integration (Axiom #17)](#life-domain-integration-axiom-#17)
- [Examples](#examples)
- [Failure Actions](#failure-actions)
- [Skills That MUST Use This Gate](#skills-that-must-use-this-gate)
- [Version History](#version-history)



> **Layer**: L1 Atomic Skill (Foundational)  
> **Purpose**: Enforce clear thinking BEFORE any skill execution  
> **Axiom Reference**: #1 (Clear Thinking + Prompting is King), #3 (Deterministic), #9 (Decision Hierarchy)  
> **Runtime**: All agents (mandatory pre-check)

## Why This Matters

> "Good prompts come from clear thinking. Think before you prompt."

**Problem**: Most skill executions fail or produce low-quality output because:
- Goals are vague or implicit
- Success criteria undefined
- Constraints unknown
- Wrong scope (too broad or too narrow)

**Solution**: This gate BLOCKS execution until 6 critical questions are answered.

---

---

## ⛔ Deterministic Execution Protocol

> **CRITICAL**: This skill uses MANDATORY checklists. Every step must be executed and verified.
> Skipping steps = quality_score: 0% and downstream skill failures.

### Execution State Machine

```
┌─────────────────────────────────────────────────────────────┐
│ STATE: INIT                                                  │
│ ✓ Load input parameters                                     │
│ ✓ Initialize execution_state = {}                          │
│ ✓ Initialize quality_checklist = ALL FALSE                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STATE: PHASE_EXECUTION (BLOCKING)                           │
│ [ ] Step 1: Clear Thinking Gate (MANDATORY)
│ ⛔ GATE: All steps MUST complete before proceeding          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ STATE: OUTPUT_VALIDATION (BLOCKING)                         │
│ [ ] Output schema is valid                                  │
│ [ ] All required fields present                             │
│ [ ] Quality metrics included                                │
│ [ ] status is SUCCESS | PARTIAL | FAILED                    │
│ ⛔ GATE: ALL checks MUST pass before return                 │
└─────────────────────────────────────────────────────────────┘
```

### Mandatory Execution Checklist

**Copy this checklist. Mark each step as you execute. DO NOT RETURN until all marked.**

```
EXECUTION_STATE = {
  "phase_1_clear_thinking_gate_": false,    # ⛔ MUST complete
  "output_validated": false,          # ⛔ Contract check passed
  "quality_gate_passed": false,       # ⛔ All gates passed
}

# ⛔ DO NOT RETURN until ALL values are TRUE
```

### Self-Verification Before Return

```python
# ⛔ MANDATORY: Execute before EVERY return
def verify_execution_complete(execution_state, output):
    errors = []
    
    # Check execution state
    for key, value in execution_state.items():
        if value == False:
            errors.append(f"INCOMPLETE: {key} not executed")
    
    # Check output has required fields
    if "status" not in output:
        errors.append("MISSING: status field")
    if output.get("status") not in ["SUCCESS", "PARTIAL", "FAILED"]:
        errors.append("INVALID: status must be SUCCESS|PARTIAL|FAILED")
    
    if errors:
        return False, errors  # ⛔ DO NOT RETURN - fix first
    return True, []
```


---

## The 6-Question Gate (MANDATORY)

### Before ANY skill execution, answer:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLEAR THINKING GATE (6 QUESTIONS)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Q1. What is the EXACT goal?                                            │
│      → NOT vague. Specific, measurable outcome.                         │
│      → Example: "Create a LinkedIn post about X" not "write something"  │
│                                                                          │
│  Q2. What does SUCCESS look like?                                       │
│      → Measurable criteria. How will we know we succeeded?              │
│      → Example: "Post gets 100+ reactions" or "Task completed in DB"    │
│                                                                          │
│  Q3. What are the CONSTRAINTS?                                          │
│      → Time, resources, energy, scope limits                            │
│      → Example: "30 minutes max" or "Use existing data only"            │
│                                                                          │
│  Q4. Who are the STAKEHOLDERS?                                          │
│      → Who cares about this? Who needs to know?                         │
│      → Example: "Manager needs update" or "Team uses the output"        │
│                                                                          │
│  Q5. What is the SIMPLEST path?                                         │
│      → Minimum viable approach. Don't over-engineer.                    │
│      → Example: "Direct query" not "build a system"                     │
│                                                                          │
│  Q6. What should we NOT do?                                             │
│      → Explicit anti-goals. What's out of scope?                        │
│      → Example: "Don't refactor" or "Skip edge cases for now"           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quality Score Calculation

Each question is scored 0-20:

| Score | Criteria |
|-------|----------|
| 20 | Specific, measurable, actionable |
| 15 | Clear but could be more specific |
| 10 | Vague, needs refinement |
| 5 | Very unclear |
| 0 | Not answered |

**Gate Threshold**: Total score ≥80/120 (66%) to proceed

---

## Output Schema

```json
{
  "clear_thinking_gate": {
    "timestamp": "2026-01-01T10:00:00Z",
    "answers": {
      "q1_exact_goal": {
        "answer": "[Specific goal statement]",
        "score": 20
      },
      "q2_success_criteria": {
        "answer": "[Measurable success definition]",
        "score": 18
      },
      "q3_constraints": {
        "answer": "[List of constraints]",
        "score": 15
      },
      "q4_stakeholders": {
        "answer": "[Who cares]",
        "score": 20
      },
      "q5_simplest_path": {
        "answer": "[MVP approach]",
        "score": 17
      },
      "q6_anti_goals": {
        "answer": "[What NOT to do]",
        "score": 15
      }
    },
    "total_score": 105,
    "threshold": 80,
    "gate_status": "PASSED",
    "proceed": true
  }
}
```

---

## Integration Pattern

### For L2/L3 Skills

Add to PHASE 0 of any skill:

```markdown
## PHASE 0: Clear Thinking Gate (MANDATORY)

**Before proceeding, answer the 6 questions:**

| Question | Answer |
|----------|--------|
| Q1. EXACT goal? | [Your answer] |
| Q2. SUCCESS criteria? | [Your answer] |
| Q3. CONSTRAINTS? | [Your answer] |
| Q4. STAKEHOLDERS? | [Your answer] |
| Q5. SIMPLEST path? | [Your answer] |
| Q6. What NOT to do? | [Your answer] |

**Gate Score**: [X]/120 → [PASSED/FAILED]

**Proceed**: [YES/NO - if NO, refine answers]
```

### Inline Invocation

```
BEFORE skill execution:
1. Load clear-thinking-gate skill
2. Answer 6 questions
3. Calculate score
4. IF score < 80: REFINE answers
5. IF score >= 80: PROCEED to skill execution
```

---

## Life Domain Integration (Axiom #17)

When the task involves personal/life domains, add these questions:

### Extended Gate (Personal/Life Tasks)

| Question | Purpose |
|----------|---------|
| Q7. Which life domain(s)? | Career, Family, Health, Financial, Growth, etc. |
| Q8. Does this align with goals? | Check against Personal Goals page |
| Q9. Energy level appropriate? | Match task to current energy state |
| Q10. Balance impact? | Will this hurt other domains? |

---


## Feedback Loop

```
1. EXECUTE → Run skill workflow
2. VALIDATE → Check quality gates
   └── IF FAIL → Iterate with feedback
3. IMPROVE → Apply corrections
4. VERIFY → Re-check quality
```

## Examples

### Example 1: Daily Planning

```json
{
  "q1_exact_goal": "Generate today's prioritized task list with top 3 items",
  "q2_success_criteria": "List created with P0/P1/P2 labels, time estimates",
  "q3_constraints": "Use data from last 3 days only, 15 minutes max",
  "q4_stakeholders": "Self (primary), manager (aware)",
  "q5_simplest_path": "Query Slack + Notion, rank by urgency",
  "q6_anti_goals": "Don't reschedule meetings, don't start tasks"
}
```

**Score**: 110/120 → **PASSED**

### Example 2: Research Task

```json
{
  "q1_exact_goal": "Research AWS IAM best practices for Terraform",
  "q2_success_criteria": "5+ validated practices with citations",
  "q3_constraints": "1 hour max, focus on production use",
  "q4_stakeholders": "Platform team (uses output), Security (reviews)",
  "q5_simplest_path": "Search AWS docs + HashiCorp docs first",
  "q6_anti_goals": "Don't build implementation, don't review existing code"
}
```

**Score**: 115/120 → **PASSED**

### Example 3: Vague Request (FAILS)

```json
{
  "q1_exact_goal": "Help with something",
  "q2_success_criteria": "It works",
  "q3_constraints": "None",
  "q4_stakeholders": "Unknown",
  "q5_simplest_path": "Not sure",
  "q6_anti_goals": "Nothing"
}
```

**Score**: 30/120 → **FAILED** - Must refine before proceeding

---

## Failure Actions

When gate FAILS (score < 80):

1. **Identify weak answers** (score < 15)
2. **Ask clarifying questions** to user
3. **Suggest defaults** based on context
4. **Re-score** after refinement
5. **Do NOT proceed** until score ≥ 80

---

## Skills That MUST Use This Gate

| Layer | Skills |
|-------|--------|
| L3 | journal-orchestrator, dynamic-roundtable, example-orchestrator |
| L2 | deep-reasoning, slack-intelligence, github-work-intelligence |
| L2 | aws-infrastructure-intelligence, notion-meeting-intelligence |
| L2 | personal-growth-tracker, career-development |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-01 | Initial release implementing Axiom #1 |

