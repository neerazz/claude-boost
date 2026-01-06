---
name: self-improvement-loop
description: Meta-skill that analyzes system data to identify improvement opportunities using hypothesis-driven analysis. Embodies continuous learning and evidence-based decision making.
layer: L2-L3
type: meta-orchestrator
version: 1.0.0
---

# Self-Improvement Loop Skill

> **Layer**: L2-L3 Meta Orchestrator
> **Purpose**: Continuous self-improvement through intelligent analysis
> **Core Axiom**: "Encode learnings - the system should get smarter over time"

---

## Core Principle

> The self-improvement loop is NOT about running on a schedule.
> It is about **deep analysis** of ALL data produced by the system to find **actionable improvements** with **evidence-based decision making**.

**What It Does**:
- Discovers patterns across all data directories
- Identifies problems with concrete evidence
- Generates evidence-based improvement proposals
- Tracks learning synthesis and adoption

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA COLLECTION                                    │
│ Scan all data sources: audit, operational, learning         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: PATTERN RECOGNITION                                │
│ Identify usage, success, and error patterns                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: PROBLEM DETECTION                                  │
│ Categorize problems with severity and evidence              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: LEARNING SYNTHESIS                                 │
│ Match learnings to skills, identify applicable patterns     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: DECISION FRAMEWORK                                 │
│ Score proposals: evidence + severity + effort + risk        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: PROPOSAL GENERATION                                │
│ Create actionable improvement proposals with evidence       │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Collection

Scan ALL data sources to build a complete picture:

```yaml
data_sources:
  audit:
    path: "data/audit/"
    content: "Execution trails, quality scores"

  operational:
    path: "data/operational/"
    content: "Runtime metrics, error logs"

  learning:
    path: "data/learning/"
    content: "External learnings, blog insights"

  memory:
    path: "memory/"
    content: "Historical patterns, trends"

  skills:
    path: "skills/"
    content: "Skill definitions, execution logs"
```

---

## Phase 2: Pattern Recognition

Classify patterns into actionable categories:

```yaml
usage_patterns:
  high_frequency:
    description: "Skills/workflows used daily"
    signal: "Core functionality - optimize for performance"

  declining:
    description: "Usage decreasing over time"
    signal: "May need refresh or replacement"

  growing:
    description: "Usage increasing over time"
    signal: "Consider enhancement"

success_patterns:
  consistently_passes:
    description: "Quality gates pass >95%"
    signal: "Model for other skills"

  frequently_fails:
    description: "Quality gates pass <70%"
    signal: "URGENT - needs rework"

error_patterns:
  transient:
    description: "Self-resolving on retry"
    signal: "Add retry logic"

  systematic:
    description: "Same error across runs"
    signal: "Root cause fix needed"

  cascading:
    description: "Skill A failure causes B to fail"
    signal: "Add isolation/dependency fix"
```

---

## Phase 3: Problem Detection

Every detected problem requires evidence:

```json
{
  "problem_id": "prob-2025-01-05-001",
  "category": "recurring_error",
  "description": "API timeout on large datasets",
  "evidence": [
    {
      "source": "data/audit/2025-01-04.jsonl",
      "line": 45,
      "quote": "Error: Request timeout after 30000ms"
    },
    {
      "source": "data/audit/2025-01-03.jsonl",
      "line": 52,
      "quote": "Error: Request timeout after 30000ms"
    }
  ],
  "occurrence_count": 3,
  "severity": "HIGH",
  "proposed_fix": "Implement pagination"
}
```

### Problem Categories

| Category | Detection | Severity |
|----------|-----------|----------|
| Recurring Errors | Same error 3+ times | HIGH |
| Quality Degradation | Score drop >10% | MEDIUM |
| Missing Capability | Manual workarounds | MEDIUM |
| Performance Issues | Increasing duration | LOW |

---

## Phase 4: Learning Synthesis

Match external learnings to applicable skills:

```json
{
  "learning_id": "learn-2025-01-05-001",
  "source": "anthropic.com/blog/extended-thinking",
  "summary": "Extended thinking improves complex reasoning",
  "applicable_skills": ["deep-reasoning", "research"],
  "adoption_effort": "low",
  "expected_impact": "high"
}
```

---

## Phase 5: Decision Framework

Score each improvement candidate:

```javascript
function calculateDecisionScore(candidate) {
  // Each factor 0-100
  const evidenceScore = candidate.evidence_sources * 30;      // Max 90
  const severityScore = getSeverityWeight(candidate.severity); // 30-100
  const effortImpact = candidate.impact / candidate.effort;    // Ratio
  const riskScore = 100 - candidate.risk_level;                // Lower is better

  return (
    evidenceScore * 0.25 +
    severityScore * 0.25 +
    effortImpact * 0.30 +
    riskScore * 0.20
  );
}

// Decision thresholds
if (score >= 70) return "TRY";      // Implement
if (score >= 50) return "DEFER";   // Wait for more evidence
return "REJECT";                    // Not worth pursuing
```

---

## Phase 6: Proposal Generation

Generate actionable proposals with full context:

```json
{
  "proposal_id": "imp-2025-01-05-001",
  "title": "Add pagination to API client",
  "priority": 1,
  "decision_score": 84,
  "affected_skills": ["api-client", "data-fetcher"],
  "evidence_summary": "3 timeout errors in 7 days",
  "implementation": {
    "files_to_modify": ["skills/api-client/SKILL.md"],
    "estimated_effort": "2 hours",
    "test_strategy": "Integration test with large dataset"
  },
  "expected_outcome": "Eliminate timeout errors for large accounts"
}
```

---

## Output Contract

```typescript
interface SelfImprovementOutput {
  analysis_scope: {
    directories_scanned: string[];
    files_analyzed: number;
    time_range: { start: string; end: string };
  };
  patterns_identified: Pattern[];
  problems_detected: Problem[];
  improvement_proposals: Proposal[];
  decision_framework_results: Decision[];
  quality_metrics: {
    coverage_score: number;      // Target: ≥95%
    evidence_quality: number;    // Target: ≥90%
    actionable_proposals: number;
  };
}
```

---

## Invocation Modes

### Full Analysis
```
"Run self-improvement-loop with full analysis"
→ Scans ALL data sources
→ Full pattern recognition
→ Complete learning synthesis
→ Output: Full report + proposals
```

### Focused Analysis
```
"Run self-improvement-loop focused on api-client"
→ Scans data related to specified skill
→ Targeted pattern recognition
→ Output: Focused report + proposals
```

### Problem Triage
```
"Run self-improvement-loop to identify problems"
→ Scans execution logs
→ Focus on error detection
→ Output: Prioritized problem list
```

---

## Quality Gates

| Gate | Threshold | Action on Failure |
|------|-----------|-------------------|
| Evidence Quality | ≥2 sources/proposal | Gather more evidence |
| Coverage Score | ≥80% directories | Expand scan scope |
| Decision Confidence | ≥70% for TRY | Defer pending evidence |

---

## Integration Points

- **Learning Aggregator**: Processes external learnings
- **Daily Planning**: Surfaces high-priority proposals
- **Skills Validation**: Proposals must pass validation

---

## Key Insight

> The self-improvement loop creates a **feedback cycle** where:
> 1. System produces data (audit, operational, learning)
> 2. Loop analyzes data for patterns and problems
> 3. Loop generates evidence-based proposals
> 4. Proposals improve skills
> 5. Better skills produce better data
> 6. Repeat
>
> This is how an AI system becomes **smarter over time**.
