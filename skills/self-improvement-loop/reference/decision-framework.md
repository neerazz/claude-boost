# Decision Framework Reference

## Overview

The decision framework provides evidence-based scoring for improvement candidates.

## Score Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Evidence | 25% | Number and quality of supporting sources |
| Severity | 25% | Impact of the problem/opportunity |
| Effort/Impact | 30% | Return on investment ratio |
| Risk | 20% | Probability of negative outcomes |

## Evidence Scoring

```
0 sources  → 0 points
1 source   → 30 points
2 sources  → 60 points
3+ sources → 90 points
```

## Severity Weights

| Level | Weight |
|-------|--------|
| CRITICAL | 100 |
| HIGH | 80 |
| MEDIUM | 50 |
| LOW | 30 |

## Decision Thresholds

| Score | Decision | Action |
|-------|----------|--------|
| ≥70 | TRY | Implement now |
| 50-69 | DEFER | Wait for evidence |
| <50 | REJECT | Don't pursue |

## Example Calculation

**Candidate**: Add retry logic to API client

- Evidence: 3 sources → 90 points
- Severity: HIGH → 80 points
- Effort: 2 hours, Impact: HIGH → ratio 85
- Risk: LOW → 90 points

**Score**: (90×0.25) + (80×0.25) + (85×0.30) + (90×0.20) = **86**

**Decision**: TRY ✅
