---
name: gap-analyzer
description: Processes and compares current skill state vs best practices to identify gaps. Single responsibility - gap analysis only.
version: 1.0.0
layer: L1
category: meta
single_responsibility: true
code_before_prompt: true
got_integration: true
axioms: [4, 5, 6, 14, 15]
---


# Gap Analyzer

## Table of Contents
- [⛔ Deterministic Execution Protocol](#⛔-deterministic-execution-protocol)
- [Input Contract](#input-contract)
- [Output Contract](#output-contract)
- [Deterministic Gap Detection](#deterministic-gap-detection)
- [Impact/Effort Classification](#impacteffort-classification)
- [Priority Assignment](#priority-assignment)
- [Execution Steps](#execution-steps)
- [Quality Gates](#quality-gates)
- [Non-Negotiables](#non-negotiables)
- [Dependencies](#dependencies)
- [Version History](#version-history)


> **Purpose**: Compare current skill implementation vs best practices to identify gaps.
> **Layer**: L1 (Atomic Skill)
> **Unix Philosophy**: One thing well - gap analysis only.
> **Approach**: Code Before Prompt - deterministic gap detection.

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
│ [ ] Step 1: Calculate Current State (Code)
│ [ ] Step 2: Compare to Target (Code)
│ [ ] Step 3: Identify Gaps (Code)
│ [ ] Step 4: Classify and Prioritize (Code)
│ [ ] Step 5: Build Matrix (Code)
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
  "phase_1_calculate_current_st": false,    # ⛔ MUST complete
  "phase_2_compare_to_target_c": false,    # ⛔ MUST complete
  "phase_3_identify_gaps_code": false,    # ⛔ MUST complete
  "phase_4_classify_and_priorit": false,    # ⛔ MUST complete
  "phase_5_build_matrix_code": false,    # ⛔ MUST complete
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

## Input Contract

```typescript
interface GapAnalyzerInput {
  skill_name: string;
  classification: SkillClassification;
  principle_analysis: PrincipleAnalysis;
  evidence_collection: EvidenceCollection;
  claim_validation: ClaimValidation;
}
```

## Output Contract

```typescript
interface GapAnalysis {
  session_id: string;
  skill_name: string;
  current_state: CurrentState;
  target_state: TargetState;
  gaps: Gap[];
  gap_summary: GapSummary;
  improvement_matrix: ImprovementMatrix;
  timestamp: string;
}

interface CurrentState {
  got_compliance: number;       // 0-100
  principle_alignment: number;  // 0-100
  documentation_score: number;  // 0-100
  quality_gate_score: number;   // 0-100
  overall_score: number;        // 0-100
}

interface TargetState {
  got_compliance: 98;           // Fixed target
  principle_alignment: 90;      // Fixed target
  documentation_score: 95;      // Fixed target
  quality_gate_score: 98;       // Fixed target
  overall_score: 95;            // Fixed target
}

interface Gap {
  id: string;                   // G001, G002...
  category: GapCategory;
  description: string;
  current_value: number;
  target_value: number;
  delta: number;
  impact: "HIGH" | "MEDIUM" | "LOW";
  effort: "HIGH" | "MEDIUM" | "LOW";
  priority: "P1" | "P2" | "P3";
  related_principles: string[];
  evidence_sources: string[];
}

type GapCategory =
  | "got_compliance"
  | "principle_alignment"
  | "documentation"
  | "quality_gates"
  | "validation"
  | "artifacts";

interface GapSummary {
  total_gaps: number;
  p1_count: number;
  p2_count: number;
  p3_count: number;
  estimated_improvement: number;  // Percentage points
}

interface ImprovementMatrix {
  quick_wins: Gap[];      // Low effort, High impact
  strategic: Gap[];       // High effort, High impact
  fill_ins: Gap[];        // Low effort, Low impact
  avoid: Gap[];           // High effort, Low impact
}
```

---

## Deterministic Gap Detection

```javascript
/**
 * GOT COMPLIANCE GAPS
 * Deterministic checks for GoT components
 */
const GOT_COMPONENT_CHECKS = {
  hypothesis_formation: {
    check: (content) => content.includes('hypothesis') ||
                        content.includes('H1:') ||
                        content.includes('Hypothesis'),
    weight: 20,
    priority: 'P1'
  },
  evidence_gathering: {
    check: (content) => content.includes('source_catalog') ||
                        content.includes('Source') ||
                        content.includes('evidence'),
    weight: 15,
    priority: 'P1'
  },
  source_quality: {
    check: (content) => content.includes('tier') ||
                        content.includes('A-tier') ||
                        content.includes('quality_rating'),
    weight: 15,
    priority: 'P2'
  },
  three_source_validation: {
    check: (content) => content.includes('3-source') ||
                        content.includes('three source') ||
                        content.includes('3 sources'),
    weight: 15,
    priority: 'P1'
  },
  cove_validation: {
    check: (content) => content.includes('CoVe') ||
                        content.includes('Chain of Verification'),
    weight: 15,
    priority: 'P2'
  },
  quality_gates: {
    check: (content) => content.includes('quality_gate') ||
                        content.includes('98%') ||
                        content.includes('threshold'),
    weight: 10,
    priority: 'P1'
  },
  got_artifacts: {
    check: (content) => content.includes('got_state.json') ||
                        content.includes('evidence_ledger'),
    weight: 10,
    priority: 'P3'
  }
};

const calculateGotCompliance = (skillContent) => {
  let score = 0;
  const gaps = [];

  for (const [component, config] of Object.entries(GOT_COMPONENT_CHECKS)) {
    if (config.check(skillContent)) {
      score += config.weight;
    } else {
      gaps.push({
        category: 'got_compliance',
        description: `Missing ${component.replace(/_/g, ' ')}`,
        current_value: 0,
        target_value: config.weight,
        delta: config.weight,
        priority: config.priority
      });
    }
  }

  return { score, gaps };
};
```

---

## Impact/Effort Classification

```javascript
/**
 * IMPACT/EFFORT MATRIX
 * Deterministic classification based on gap type
 */
const classifyImpactEffort = (gap) => {
  const CLASSIFICATIONS = {
    // GoT components
    hypothesis_formation: { impact: 'HIGH', effort: 'MEDIUM' },
    evidence_gathering: { impact: 'HIGH', effort: 'LOW' },
    source_quality: { impact: 'MEDIUM', effort: 'LOW' },
    three_source_validation: { impact: 'HIGH', effort: 'HIGH' },
    cove_validation: { impact: 'MEDIUM', effort: 'MEDIUM' },
    quality_gates: { impact: 'HIGH', effort: 'LOW' },
    got_artifacts: { impact: 'LOW', effort: 'LOW' },

    // Documentation
    missing_examples: { impact: 'MEDIUM', effort: 'LOW' },
    missing_reference: { impact: 'LOW', effort: 'LOW' },
    excessive_lines: { impact: 'MEDIUM', effort: 'MEDIUM' },

    // Principles
    principle_gap: { impact: 'MEDIUM', effort: 'MEDIUM' }
  };

  const gapType = gap.description.toLowerCase()
    .replace(/missing /g, '')
    .replace(/ /g, '_');

  return CLASSIFICATIONS[gapType] ||
         { impact: 'MEDIUM', effort: 'MEDIUM' };
};

const buildImprovementMatrix = (gaps) => {
  return {
    quick_wins: gaps.filter(g =>
      g.effort === 'LOW' && g.impact === 'HIGH'
    ),
    strategic: gaps.filter(g =>
      g.effort === 'HIGH' && g.impact === 'HIGH'
    ),
    fill_ins: gaps.filter(g =>
      g.effort === 'LOW' && g.impact === 'LOW'
    ),
    avoid: gaps.filter(g =>
      g.effort === 'HIGH' && g.impact === 'LOW'
    )
  };
};
```

---

## Priority Assignment

```javascript
/**
 * PRIORITY RULES
 * Deterministic based on principle analysis
 */
const assignPriority = (gap, principleAnalysis) => {
  // Rule 1: mustApply principle gaps are always P1
  if (gap.related_principles.some(p =>
    principleAnalysis.mustApply.find(mp => mp.id === p)
  )) {
    return 'P1';
  }

  // Rule 2: HIGH impact gaps are P1 or P2
  if (gap.impact === 'HIGH') {
    return gap.effort === 'HIGH' ? 'P2' : 'P1';
  }

  // Rule 3: shouldApply principle gaps are P2
  if (gap.related_principles.some(p =>
    principleAnalysis.shouldApply.find(sp => sp.id === p)
  )) {
    return 'P2';
  }

  // Rule 4: Everything else is P3
  return 'P3';
};
```

---

## Execution Steps

### Step 1: Calculate Current State (Code)
```javascript
const gotResult = calculateGotCompliance(skillContent);
const principleGaps = findPrincipleGaps(classification, principleAnalysis);
const docScore = calculateDocumentationScore(skillContent, metadata);

const currentState = {
  got_compliance: gotResult.score,
  principle_alignment: calculatePrincipleAlignment(principleAnalysis),
  documentation_score: docScore,
  quality_gate_score: extractQualityScore(skillContent),
  overall_score: calculateOverall(...)
};
```

### Step 2: Compare to Target (Code)
```javascript
const targetState = {
  got_compliance: 98,
  principle_alignment: 90,
  documentation_score: 95,
  quality_gate_score: 98,
  overall_score: 95
};
```

### Step 3: Identify Gaps (Code)
```javascript
const gaps = [];
// GoT gaps
gaps.push(...gotResult.gaps);
// Principle gaps
gaps.push(...principleGaps);
// Documentation gaps
if (currentState.documentation_score < targetState.documentation_score) {
  gaps.push(createDocGap(...));
}
```

### Step 4: Classify and Prioritize (Code)
```javascript
for (const gap of gaps) {
  const { impact, effort } = classifyImpactEffort(gap);
  gap.impact = impact;
  gap.effort = effort;
  gap.priority = assignPriority(gap, principleAnalysis);
}
```

### Step 5: Build Matrix (Code)
```javascript
const matrix = buildImprovementMatrix(gaps);
```

---

## Quality Gates

| Gate | Threshold | Type |
|------|-----------|------|
| All dimensions scored | 5 dimensions | HARD FAIL |
| Target state defined | All fixed targets | HARD FAIL |
| Gaps prioritized | All P1/P2/P3 | HARD FAIL |
| Matrix built | 4 quadrants | HARD FAIL |

---

## Non-Negotiables

1. **Fixed Targets** - Target state is immutable (98% quality)
2. **Deterministic Classification** - Impact/Effort from rules
3. **Priority from Principles** - mustApply = P1
4. **No Recommendations** - Analysis only, not solutions

---

## Dependencies

- **skill-classifier** - Classification input
- **principle-analyzer** - Principle analysis input
- **evidence-gatherer** - Evidence collection
- **claim-validator** - Validation results

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-31 | Initial release - deterministic gap detection |

## Feedback Loop

```
1. EXECUTE → Run skill workflow
2. VALIDATE → Check quality gates
   └── IF FAIL → Iterate with feedback
3. IMPROVE → Apply corrections
4. VERIFY → Re-check quality
```

