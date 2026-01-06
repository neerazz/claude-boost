---
name: self-critique-gate
description: Validates and mandatory post-execution validation implementing Axiom #14 (Science Loop) and Axiom #15 (GOT). All L2/L3 skills MUST call this before returning output. Ensures quality, identifies errors, and validates evidence.
layer: L1-Atomic
type: validation-gate
version: 1.0.0
axioms: [14, 15, 10]
---

# Self-Critique Gate (Axiom #14 & #15 Implementation)

## Table of Contents
- [⛔ Deterministic Execution Protocol](#⛔-deterministic-execution-protocol)
- [Why This Matters](#why-this-matters)
- [The 5-Question Gate (MANDATORY)](#the-5-question-gate-mandatory)
- [Quality Score Interpretation](#quality-score-interpretation)
- [Red Team Challenge (MANDATORY for Complex Tasks)](#red-team-challenge-mandatory-for-complex-tasks)
- [Output Schema](#output-schema)
- [Integration Pattern](#integration-pattern)
- [Chain-of-Verification (CoVe) Integration](#chain-of-verification-cove-integration)
- [Learning Capture (Axiom #10)](#learning-capture-axiom-#10)
- [Life Domain Self-Critique (Extended)](#life-domain-self-critique-extended)
- [Examples](#examples)
- [Failure Actions](#failure-actions)
- [Skills That MUST Use This Gate](#skills-that-must-use-this-gate)
- [Integration with Clear Thinking Gate](#integration-with-clear-thinking-gate)
- [Version History](#version-history)



> **Layer**: L1 Atomic Skill (Foundational)  
> **Purpose**: Enforce critical self-review BEFORE returning any output  
> **Axiom Reference**: #14 (Science Loop), #15 (GOT), #10 (Meta/Self Update)  
> **Runtime**: All agents (mandatory post-check)

## Why This Matters

> "Hypothesis → Experiment → Measure → Iterate. Always be learning."

**Problem**: Most skill outputs contain errors because:
- Assumptions are never questioned
- Evidence is incomplete or weak
- Quality self-assessment is skipped
- Learnings are not captured

**Solution**: This gate BLOCKS output until 5 critical questions are answered honestly.

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
│ [ ] Step 1: Identify weakest areas
│ [ ] Step 2: Re-execute
│ [ ] Step 3: Gather more evidence
│ [ ] Step 4: Challenge assumptions
│ [ ] Step 5: Re-score
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
  "phase_1_identify_weakest_are": false,    # ⛔ MUST complete
  "phase_2_re_execute": false,    # ⛔ MUST complete
  "phase_3_gather_more_evidence": false,    # ⛔ MUST complete
  "phase_4_challenge_assumption": false,    # ⛔ MUST complete
  "phase_5_re_score": false,    # ⛔ MUST complete
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

## The 5-Question Gate (MANDATORY)

### Before returning ANY output, answer:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SELF-CRITIQUE GATE (5 QUESTIONS)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Q1. What could be WRONG with this output?                              │
│      → List potential errors, gaps, weaknesses                          │
│      → Be brutally honest. What would a critic say?                     │
│                                                                          │
│  Q2. What ASSUMPTIONS did I make?                                       │
│      → List all assumptions (explicit and implicit)                     │
│      → Which assumptions are most risky?                                │
│                                                                          │
│  Q3. What EVIDENCE supports this output?                                │
│      → Cite specific sources, data, or reasoning                        │
│      → Are there 3+ independent sources? (Axiom #15)                    │
│                                                                          │
│  Q4. What would INVALIDATE this output?                                 │
│      → Define falsification criteria                                    │
│      → What new information would make this wrong?                      │
│                                                                          │
│  Q5. What is my honest QUALITY score (1-10)?                            │
│      → 10 = Excellent, no improvements needed                           │
│      → 7 = Good, minor improvements possible                            │
│      → 5 = Acceptable, significant improvements possible                │
│      → 3 = Poor, major issues                                           │
│      → 1 = Failed, should not output                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quality Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 9-10 | Excellent | Proceed with confidence |
| 7-8 | Good | Proceed, note minor improvements |
| 5-6 | Acceptable | Proceed with warnings, log improvements |
| 3-4 | Poor | ITERATE - do not proceed |
| 1-2 | Failed | RESTART from beginning |

**Gate Threshold**: Score ≥ 7 to proceed without iteration

---

## Red Team Challenge (MANDATORY for Complex Tasks)

For any output with HIGH stakes or COMPLEX reasoning:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RED TEAM CHALLENGE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  COUNTERARGUMENT 1: [Why this output might be wrong]                    │
│  COUNTERARGUMENT 2: [Alternative interpretation]                        │
│  COUNTERARGUMENT 3: [Edge case where this fails]                        │
│                                                                          │
│  MITIGATIONS:                                                           │
│  - For C1: [How we addressed or why it's acceptable]                    │
│  - For C2: [How we addressed or why it's acceptable]                    │
│  - For C3: [How we addressed or why it's acceptable]                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Output Schema

```json
{
  "self_critique_gate": {
    "timestamp": "2026-01-01T10:30:00Z",
    "answers": {
      "q1_potential_errors": {
        "items": ["Error 1", "Error 2", "Error 3"],
        "severity": "LOW | MEDIUM | HIGH"
      },
      "q2_assumptions": {
        "items": ["Assumption 1", "Assumption 2"],
        "risky_assumptions": ["Assumption 1"]
      },
      "q3_evidence": {
        "sources": ["Source 1", "Source 2", "Source 3"],
        "has_3_source_validation": true
      },
      "q4_invalidation_criteria": {
        "items": ["If X is false", "If Y changes"]
      },
      "q5_quality_score": {
        "score": 8,
        "justification": "Good output with minor improvements possible"
      }
    },
    "red_team": {
      "completed": true,
      "counterarguments": 3,
      "mitigations": 3
    },
    "gate_status": "PASSED",
    "proceed": true,
    "learnings_captured": true
  }
}
```

---

## Integration Pattern

### For L2/L3 Skills

Add as FINAL PHASE before output:

```markdown
## PHASE [N]: Self-Critique Gate (MANDATORY)

**Before returning output, answer:**

| Question | Answer |
|----------|--------|
| Q1. What could be WRONG? | [Your honest assessment] |
| Q2. What ASSUMPTIONS? | [List them] |
| Q3. What EVIDENCE? | [Cite sources] |
| Q4. What would INVALIDATE? | [Falsification criteria] |
| Q5. Quality score (1-10)? | [X] - [Justification] |

**Red Team Challenge:**
- C1: [Counterargument]
- C2: [Counterargument]
- C3: [Counterargument]

**Mitigations:**
- For C1: [Response]
- For C2: [Response]
- For C3: [Response]

**Gate Status**: [PASSED/FAILED]

**Proceed**: [YES/NO - if NO, iterate]
```

---

## Chain-of-Verification (CoVe) Integration

For factual claims, apply CoVe:

```
For each CLAIM in output:
1. Extract claim text
2. Generate 3 verification questions:
   - Q1: Direct verification question
   - Q2: Contrary evidence question
   - Q3: Source credibility question
3. Search independently for each question
4. Score consistency (0-100):
   - All 3 support claim → 100
   - 2 support, 1 neutral → 80
   - 2 support, 1 contrary → 60
   - Mixed results → 40
5. Threshold: CoVe score < 70 → Flag claim
```

---

## Learning Capture (Axiom #10)

After EVERY self-critique, capture learnings:

```json
{
  "meta_learning": {
    "what_worked": ["Pattern 1", "Pattern 2"],
    "what_failed": ["Anti-pattern 1"],
    "improvements_for_next_time": ["Improvement 1"],
    "skill_specific_learnings": "[Insight about this skill]"
  }
}
```

**Storage**: Append to `data/learning/skill_learnings.jsonl`

---

## Life Domain Self-Critique (Extended)

For personal/life domain tasks, add:

### Extended Self-Critique Questions

| Question | Purpose |
|----------|---------|
| Q6. Does this align with values? | Check against Ethics Architecture (Axiom #24) |
| Q7. Impact on relationships? | Check Relationship Capital (Axiom #20) |
| Q8. Long-term consequences? | Check Legacy Thinking (Axiom #27) |
| Q9. Energy impact? | Check Health Foundation (Axiom #22) |
| Q10. Balance impact? | Check Holistic Balance (Axiom #17) |

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

### Example 1: Research Output (PASSES)

```json
{
  "q1_potential_errors": {
    "items": ["May have missed recent sources", "AWS docs may be outdated"],
    "severity": "LOW"
  },
  "q2_assumptions": {
    "items": ["User wants production-ready practices", "Terraform is the IaC tool"],
    "risky_assumptions": []
  },
  "q3_evidence": {
    "sources": ["AWS Documentation", "HashiCorp Best Practices", "Security Benchmark"],
    "has_3_source_validation": true
  },
  "q4_invalidation_criteria": {
    "items": ["AWS changes IAM model", "New security vulnerability discovered"]
  },
  "q5_quality_score": {
    "score": 8,
    "justification": "Solid research with 3-source validation, minor gaps in edge cases"
  }
}
```

**Gate Status**: PASSED (score 8 ≥ 7)

### Example 2: Shallow Analysis (FAILS)

```json
{
  "q1_potential_errors": {
    "items": ["Not sure"],
    "severity": "UNKNOWN"
  },
  "q2_assumptions": {
    "items": ["None identified"],
    "risky_assumptions": []
  },
  "q3_evidence": {
    "sources": ["One blog post"],
    "has_3_source_validation": false
  },
  "q4_invalidation_criteria": {
    "items": []
  },
  "q5_quality_score": {
    "score": 4,
    "justification": "Rushed, incomplete research"
  }
}
```

**Gate Status**: FAILED (score 4 < 7) → ITERATE

---

## Failure Actions

When gate FAILS (score < 7):

1. **Identify weakest areas** (Q1-Q4 answers)
2. **Re-execute** relevant phases
3. **Gather more evidence** if Q3 weak
4. **Challenge assumptions** if Q2 weak
5. **Re-score** after iteration
6. **Max 3 iterations** before escalating

---

## Skills That MUST Use This Gate

| Layer | Skills |
|-------|--------|
| L3 | journal-orchestrator, dynamic-roundtable, example-orchestrator |
| L2 | deep-reasoning, slack-intelligence, github-work-intelligence |
| L2 | aws-infrastructure-intelligence, notion-meeting-intelligence |
| L2 | personal-growth-tracker, career-development |
| L2 | all research and analysis skills |

---

## Integration with Clear Thinking Gate

```
SKILL EXECUTION FLOW:
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. CLEAR THINKING GATE (Pre-execution)                                 │
│     └─→ 6 questions answered → Score ≥80 → PROCEED                      │
│                                                                          │
│  2. SKILL EXECUTION (Main phases)                                       │
│     └─→ Execute all phases as designed                                  │
│                                                                          │
│  3. SELF-CRITIQUE GATE (Post-execution)                                 │
│     └─→ 5 questions answered → Score ≥7 → OUTPUT                        │
│     └─→ If score <7 → ITERATE (back to step 2)                          │
│                                                                          │
│  4. OUTPUT with quality_metrics                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-01 | Initial release implementing Axiom #14, #15, #10 |

