# Universal Prompt Orchestrator (UPO) Architecture

The Universal Prompt Orchestrator (UPO) is an L3 Meta-Orchestrator that serves as the intelligent routing layer for all prompts in the Claude Boost framework. It ensures every request is analyzed through multiple perspectives before execution, providing holistic, balanced responses.

## Overview

UPO transforms simple prompts into well-orchestrated, multi-agent workflows by:

1. **Analyzing** the prompt to understand intent and domain coverage
2. **Selecting** relevant agents (4-12) based on keywords and context
3. **Executing** agents in parallel for diverse perspectives
4. **Synthesizing** weighted outputs into actionable recommendations
5. **Validating** quality through a Round Table Council
6. **Learning** from execution to improve future routing

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER PROMPT                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              UNIVERSAL PROMPT ORCHESTRATOR                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Context   │  │   Agent     │  │  Synthesis  │             │
│  │   Loading   │─▶│  Selection  │─▶│   Engine    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                │                │                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   4-12      │  │   Round     │  │   Memory    │             │
│  │   Agents    │─▶│   Table     │─▶│   Update    │             │
│  │  (Parallel) │  │  Council    │  │  (Async)    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           SKILL EXECUTION + AUDIT ARTIFACTS                      │
└─────────────────────────────────────────────────────────────────┘
```

## The 12-Agent Architecture

UPO employs 12 specialized domain agents, each bringing a unique perspective to every prompt. This ensures no critical aspect is overlooked.

### Agent Categories

| Category | Agents | Combined Weight |
|----------|--------|-----------------|
| **Career & Professional** | EB1A & Visibility, Career & Leadership, Technical Excellence | 37% |
| **Relationships** | Family & Relationships | 12% |
| **Health & Wellness** | Health & Energy | 10% |
| **Financial** | Financial | 8% |
| **Personal Growth** | Learning & Growth, Goals & OKRs | 13% |
| **Emotional & Social** | Emotional Intelligence | 5% |
| **Recreation** | Fun & Recreation | 5% |
| **Legacy** | Contribution & Legacy | 5% |
| **Discovery** | Skills Discovery | 5% |

### Agent Details

```
┌────────────────────────────────────────────────────────────────────────┐
│                          12 DOMAIN AGENTS                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CAREER & PROFESSIONAL (37%)                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ EB1A &          │  │ Career &        │  │ Technical       │        │
│  │ Visibility (15%)│  │ Leadership (12%)│  │ Excellence (10%)│        │
│  │                 │  │                 │  │                 │        │
│  │ - Immigration   │  │ - Promotions    │  │ - Code quality  │        │
│  │ - Publications  │  │ - Leadership    │  │ - Architecture  │        │
│  │ - Recognition   │  │ - Influence     │  │ - Performance   │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  LIFE BALANCE (35%)                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Family &        │  │ Health &        │  │ Financial       │        │
│  │ Relationships   │  │ Energy (10%)    │  │ (8%)            │        │
│  │ (12%)           │  │                 │  │                 │        │
│  │ - Work-life     │  │ - Physical      │  │ - Budget        │        │
│  │ - Spouse/Kids   │  │ - Mental        │  │ - Investments   │        │
│  │ - Friends       │  │ - Sleep         │  │ - Planning      │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  GROWTH & DISCOVERY (28%)                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Learning &      │  │ Goals & OKRs    │  │ Skills          │        │
│  │ Growth (8%)     │  │ (5%) [MANDATORY]│  │ Discovery (5%)  │        │
│  │                 │  │                 │  │ [MANDATORY]     │        │
│  │ - Courses       │  │ - Priorities    │  │ - Skill match   │        │
│  │ - Certifications│  │ - Milestones    │  │ - Tool routing  │        │
│  │ - Reading       │  │ - OKR alignment │  │ - Automation    │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Emotional       │  │ Fun &           │  │ Contribution &  │        │
│  │ Intelligence(5%)│  │ Recreation (5%) │  │ Legacy (5%)     │        │
│  │                 │  │                 │  │                 │        │
│  │ - Communication │  │ - Hobbies       │  │ - Mentoring     │        │
│  │ - Empathy       │  │ - Travel        │  │ - Community     │        │
│  │ - Relationships │  │ - Entertainment │  │ - Open source   │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

## Execution Phases

UPO processes every prompt through 6 distinct phases, ensuring thorough analysis and quality output.

### Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UPO EXECUTION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────┘

Phase -1          Phase 0           Phase 0.5          Phase 1
┌──────────┐     ┌──────────┐      ┌──────────┐       ┌──────────┐
│ CONTEXT  │────▶│  INIT    │─────▶│  AGENT   │──────▶│ PARALLEL │
│ LOADING  │     │          │      │ SELECTION│       │EXECUTION │
└──────────┘     └──────────┘      └──────────┘       └──────────┘
     │                │                 │                  │
     │ User Goals     │ Weightage      │ Keywords +       │ 4-12 Agents
     │ User Profile   │ Skill DAG      │ Dependencies     │ Concurrent
     │ EB1A Status    │ History        │                  │
     ▼                ▼                 ▼                  ▼

Phase 2            Phase 3           Phase 4            Phase 5
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│SYNTHESIS │─────▶│  ROUND   │─────▶│   GOT    │─────▶│  MEMORY  │
│  ENGINE  │      │  TABLE   │      │ARTIFACTS │      │  UPDATE  │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
     │                 │                 │                  │
     │ Weighted        │ 6 Council      │ query_log.csv   │ Weight
     │ Aggregation     │ Agents         │ evidence.csv    │ Calibration
     │ Skill Ranking   │ ≤4 Rounds      │ got_state.json  │ (EMA)
     ▼                 ▼                 ▼                  ▼
```

### Phase -1: Context Loading (Mandatory)

**Purpose**: Load user-specific context for personalized routing.

```python
# Pseudocode
def load_user_context():
    # Check cache (6-hour TTL)
    cache = load_cache("persona-cache.json")
    if cache.is_fresh():
        return cache.data

    # Fetch from Notion
    context = {
        "role": fetch_notion("personal_page"),
        "goals": fetch_notion("goals_page"),  # NEVER cached
        "eb1a_status": search_notion("eb1a") if has_keywords("eb1a")
    }

    update_cache(context)
    return context
```

**Trigger Keywords**: `eb1a`, `visa`, `career`, `job`, `role`, `company`, `profile`, `personal`, `goals`

### Phase 0: Initialization

**Purpose**: Load system configuration and prepare execution state.

- Load agent weightage from `memory/agent-weightage/default-weightage.json`
- Apply active goal priorities (e.g., EB1A = P0)
- Load skill DAG for skill discovery
- Load conversation history for monotonic growth enforcement

### Phase 0.5: Intelligent Agent Selection

**Purpose**: Select 4-12 relevant agents based on prompt analysis.

```
┌────────────────────────────────────────────────────────────────────────┐
│                     AGENT SELECTION ALGORITHM                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. MANDATORY AGENTS (Always Included)                                 │
│     ┌─────────────────┐  ┌─────────────────┐                          │
│     │ Goals & OKRs    │  │ Skills Discovery│                          │
│     └─────────────────┘  └─────────────────┘                          │
│                                                                         │
│  2. KEYWORD MATCHING                                                   │
│     Prompt: "Help me write an EB1A article"                           │
│     ┌─────────────┐                                                    │
│     │  Keywords   │──▶ "eb1a" ──▶ EB1A Agent                          │
│     │  Extracted  │──▶ "write" ──▶ (no match)                         │
│     │             │──▶ "article" ──▶ EB1A Agent                        │
│     └─────────────┘                                                    │
│                                                                         │
│  3. CHAIN DEPENDENCIES                                                 │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│     │    EB1A     │────▶│   Career    │────▶│  Technical  │          │
│     └─────────────┘     └─────────────┘     └─────────────┘          │
│           │                                       │                    │
│           ▼                                       ▼                    │
│     ┌─────────────┐                        ┌─────────────┐            │
│     │   Family    │                        │  Learning   │            │
│     └─────────────┘                        └─────────────┘            │
│                                                                         │
│  4. MONOTONIC GROWTH                                                   │
│     agents(turn N+1) >= agents(turn N)                                │
│                                                                         │
│  5. MINIMUM THRESHOLD: 4 agents                                        │
│                                                                         │
│  6. DOUBT = INCLUDE (if >30% relevance possible, add agent)           │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

**Keyword → Agent Mapping Examples**:

| Agent | Trigger Keywords |
|-------|------------------|
| EB1A & Visibility | `eb1a`, `immigration`, `visa`, `article`, `publish`, `recognition` |
| Career & Leadership | `career`, `promotion`, `leadership`, `manager`, `staff`, `principal` |
| Technical Excellence | `code`, `technical`, `kubernetes`, `aws`, `performance`, `architecture` |
| Family & Relationships | `family`, `spouse`, `kids`, `balance`, `personal`, `wife`, `husband` |
| Financial | `money`, `invest`, `budget`, `salary`, `stock`, `savings` |
| Health & Energy | `health`, `exercise`, `sleep`, `stress`, `fitness`, `gym` |
| Fun & Recreation | `travel`, `vacation`, `trip`, `fun`, `hobby`, `japan`, `europe` |

### Phase 1: Parallel Agent Execution

**Purpose**: Run selected agents concurrently for diverse perspectives.

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PARALLEL AGENT EXECUTION                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Promise.all([                                                         │
│    agent_eb1a(prompt, context),        ──┐                             │
│    agent_career(prompt, context),        │                             │
│    agent_technical(prompt, context),     ├── Concurrent                │
│    agent_family(prompt, context),        │   Execution                 │
│    agent_goals(prompt, context),         │                             │
│    agent_skills(prompt, context)       ──┘                             │
│  ])                                                                     │
│                                                                         │
│  Each agent returns:                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  {                                                               │  │
│  │    "agent_id": "eb1a_visibility",                               │  │
│  │    "status": "success",                                          │  │
│  │    "relevance_score": 0.95,        // 0-1 self-assessed         │  │
│  │    "insights": [...],               // Key observations          │  │
│  │    "concerns": [...],               // Potential issues          │  │
│  │    "recommendations": [...],        // Action items              │  │
│  │    "suggested_skills": [            // Skills to invoke          │  │
│  │      "eb1a-research",                                            │  │
│  │      "content-round-table"                                       │  │
│  │    ],                                                            │  │
│  │    "execution_time_ms": 1250                                     │  │
│  │  }                                                               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Synthesis Engine

**Purpose**: Aggregate perspectives into weighted, ranked recommendations.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      SYNTHESIS ALGORITHM                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Calculate Effective Weights                                        │
│     ┌─────────────────────────────────────────────────────────────┐   │
│     │  effective_weight = base_weight × relevance_score            │   │
│     │                                                               │   │
│     │  Example:                                                     │   │
│     │  EB1A Agent: 0.15 (base) × 0.95 (relevance) = 0.1425         │   │
│     │  Career Agent: 0.12 × 0.85 = 0.102                           │   │
│     │  Goals Agent: 0.05 × 0.90 = 0.045                            │   │
│     └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  2. Normalize to 100%                                                  │
│     ┌─────────────────────────────────────────────────────────────┐   │
│     │  total = sum(all_effective_weights)                          │   │
│     │  final_weight = effective_weight / total                     │   │
│     │                                                               │   │
│     │  EB1A: 0.1425 / 0.2895 = 0.49 (49%)                         │   │
│     │  Career: 0.102 / 0.2895 = 0.35 (35%)                        │   │
│     │  Goals: 0.045 / 0.2895 = 0.16 (16%)                         │   │
│     └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  3. Aggregate Skill Votes                                              │
│     ┌─────────────────────────────────────────────────────────────┐   │
│     │  skill_scores = {}                                           │   │
│     │  for agent in agents:                                        │   │
│     │    for skill in agent.suggested_skills:                      │   │
│     │      skill_scores[skill] += agent.final_weight               │   │
│     │                                                               │   │
│     │  Ranked Skills:                                              │   │
│     │  1. eb1a-research: 0.89 (EB1A + Career + Goals)             │   │
│     │  2. content-round-table: 0.72 (EB1A + Career)               │   │
│     │  3. deep-research: 0.45 (EB1A)                              │   │
│     └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Round Table Council

**Purpose**: Quality deliberation through 6 specialized council agents.

```
┌────────────────────────────────────────────────────────────────────────┐
│                       ROUND TABLE COUNCIL                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  6 COUNCIL AGENTS (run in deliberation rounds)                         │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │    RESEARCH     │  │    CRITIQUE     │  │   CONSENSUS     │        │
│  │     AGENT       │  │     AGENT       │  │     AGENT       │        │
│  │                 │  │                 │  │                 │        │
│  │ Find trending   │  │ Challenge       │  │ Build agreement │        │
│  │ approaches,     │  │ assumptions,    │  │ from divergent  │        │
│  │ audit-level     │  │ identify gaps   │  │ views           │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │   PROS/CONS     │  │   RED FLAG      │  │ SELF-CORRECTION │        │
│  │     AGENT       │  │     AGENT       │  │     AGENT       │        │
│  │                 │  │                 │  │                 │        │
│  │ Generate        │  │ Prevent         │  │ Rate quality    │        │
│  │ tradeoff        │  │ derailing,      │  │ (Chain of       │        │
│  │ analysis        │  │ flag risks      │  │ Thought)        │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  EXECUTION LOGIC:                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  for round in range(1, 5):                                       │  │
│  │    results = await parallel([                                    │  │
│  │      research_agent(),                                           │  │
│  │      critique_agent(),                                           │  │
│  │      consensus_agent(),                                          │  │
│  │      pros_cons_agent(),                                          │  │
│  │      red_flag_agent(),                                           │  │
│  │      self_correction_agent()                                     │  │
│  │    ])                                                            │  │
│  │    quality_score = self_correction_agent.score                  │  │
│  │    if quality_score >= 0.95:                                    │  │
│  │      break  # Quality threshold met                             │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 4: GOT Artifacts Generation

**Purpose**: Generate audit trail for transparency and debugging.

```
data/audit/upo/{session_id}/
├── query_log.csv         # All agent inputs/outputs with metrics
├── evidence_ledger.csv   # Evidence for each recommendation
├── source_catalog.json   # Source credibility and weights
└── got_state.json        # Graph of Thoughts state
```

**GOT State Structure**:
```json
{
  "nodes": [
    {"id": "eb1a_visibility", "type": "perspective", "weight": 0.49},
    {"id": "career_leadership", "type": "perspective", "weight": 0.35},
    {"id": "eb1a-research", "type": "skill", "score": 0.89}
  ],
  "edges": [
    {"from": "eb1a_visibility", "to": "eb1a-research", "weight": 0.89},
    {"from": "career_leadership", "to": "eb1a-research", "weight": 0.72}
  ],
  "synthesis_score": 0.96,
  "timestamp": "2026-01-09T12:34:56Z"
}
```

### Phase 5: Memory Update (Async)

**Purpose**: Learn from execution to improve future routing.

```python
# Exponential Moving Average (EMA) weight update
def update_agent_weight(agent_id, feedback):
    decay_factor = 0.9
    old_weight = get_current_weight(agent_id)
    new_weight = old_weight * decay_factor + feedback * (1 - decay_factor)
    save_weight(agent_id, new_weight)
    normalize_all_weights()  # Ensure sum = 100%
```

## Agent Selection Examples

### Example 1: EB1A Article Creation

**Prompt**: "Help me create an article for my EB1A application"

```
┌────────────────────────────────────────────────────────────────────────┐
│                    AGENT SELECTION BREAKDOWN                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Keyword Matches:                                                       │
│    "EB1A" ──▶ EB1A & Visibility Agent                                  │
│    "article" ──▶ EB1A & Visibility Agent                               │
│                                                                         │
│  Chain Dependencies:                                                   │
│    EB1A ──▶ Career & Leadership (thought leadership)                   │
│    EB1A ──▶ Technical Excellence (depth and rigor)                     │
│                                                                         │
│  Mandatory Agents:                                                     │
│    Goals & OKRs                                                        │
│    Skills Discovery                                                    │
│                                                                         │
│  FINAL SELECTION (6 agents):                                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Agent              │ Relevance │ Effective Weight              │  │
│  ├─────────────────────┼───────────┼──────────────────────────────│  │
│  │  EB1A & Visibility  │    95%    │      22%                     │  │
│  │  Goals & OKRs       │    95%    │      18%                     │  │
│  │  Career & Leadership│    85%    │      15%                     │  │
│  │  Technical Excellence│   80%    │      12%                     │  │
│  │  Learning & Growth  │    70%    │      10%                     │  │
│  │  Skills Discovery   │   100%    │      23%                     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  RECOMMENDED SKILL CHAIN:                                              │
│    1. deep-research (gather sources)                                   │
│    2. content-round-table (multi-agent creation)                       │
│    3. eb1a-research (EB1A-specific guidance)                          │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Example 2: Vacation Planning

**Prompt**: "Plan a 2-week vacation to Japan with my family"

```
┌────────────────────────────────────────────────────────────────────────┐
│                    AGENT SELECTION BREAKDOWN                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Keyword Matches:                                                       │
│    "vacation" ──▶ Fun & Recreation Agent                               │
│    "Japan" ──▶ Fun & Recreation Agent                                  │
│    "family" ──▶ Family & Relationships Agent                           │
│                                                                         │
│  Chain Dependencies:                                                   │
│    Travel ──▶ Financial (budget planning)                              │
│    Travel ──▶ Health & Energy (travel wellness)                        │
│                                                                         │
│  Mandatory Agents:                                                     │
│    Goals & OKRs                                                        │
│    Skills Discovery                                                    │
│                                                                         │
│  FINAL SELECTION (6 agents):                                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Agent              │ Relevance │ Effective Weight              │  │
│  ├─────────────────────┼───────────┼──────────────────────────────│  │
│  │  Fun & Recreation   │   100%    │      35%                     │  │
│  │  Family & Relations │    90%    │      20%                     │  │
│  │  Health & Energy    │    75%    │      15%                     │  │
│  │  Financial          │    70%    │      12%                     │  │
│  │  Goals & OKRs       │    50%    │       8%                     │  │
│  │  Skills Discovery   │   100%    │      10%                     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  RECOMMENDED SKILL CHAIN:                                              │
│    1. deep-research (destinations, costs, timing)                      │
│    2. calendar-blocker (block travel dates)                            │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

## Quality Gates & Thresholds

UPO enforces strict quality standards at multiple checkpoints:

| Gate | Threshold | Action on Failure |
|------|-----------|-------------------|
| Agents Responded | ≥80% (10/12) | Retry failed agents |
| Synthesis Score | ≥95% | Additional council rounds |
| Skill Match Accuracy | ≥80% | Manual review |
| GOT Artifacts | 4/4 generated | Block completion |
| Balance Coverage | 6/6 categories | Add missing perspectives |
| Latency | <8 seconds | Performance alert |

**Quality Verdicts**:
- `PASS` (≥95%): Full confidence, execute recommended skills
- `CONDITIONAL` (80-95%): Proceed with user confirmation
- `FAIL` (<80%): Require human review before proceeding

## Self-Learning Loop

UPO continuously improves through execution feedback:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SELF-LEARNING LOOP                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐   │
│  │ Execute  │─────▶│ Collect  │─────▶│ Update   │─────▶│ Normalize│   │
│  │   UPO    │      │ Metrics  │      │ Weights  │      │   100%   │   │
│  └──────────┘      └──────────┘      └──────────┘      └──────────┘   │
│       │                                    │                            │
│       │                                    ▼                            │
│       │                          ┌──────────────────┐                  │
│       │                          │  Every N runs:   │                  │
│       │                          │  /self-learn     │                  │
│       │                          │  recalibration   │                  │
│       │                          └──────────────────┘                  │
│       │                                    │                            │
│       ▼                                    ▼                            │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Performance Metrics Tracked:                                    │  │
│  │  - relevance_accuracy: How well agent assessed its relevance    │  │
│  │  - contribution_score: How much agent influenced final output   │  │
│  │  - execution_time: Latency performance                          │  │
│  │  - skill_match_rate: Accuracy of skill recommendations          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Integration with Claude Boost Framework

UPO integrates with the broader framework through:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FRAMEWORK INTEGRATION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DEPENDENCIES (UPO uses):                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ user-persona    │  │ prompt-refiner  │  │ got-core        │         │
│  │ (context)       │  │ (optimization)  │  │ (artifacts)     │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  OUTPUTS TO:                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ L2/L3 Skills    │  │ /self-learn     │  │ Audit Trail     │         │
│  │ (execution)     │  │ (calibration)   │  │ (compliance)    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  DATA FLOW:                                                             │
│  memory/agent-weightage/ ◀──────▶ UPO ◀──────▶ data/dag/skill_dag.json │
│                                    │                                     │
│                                    ▼                                     │
│                          data/audit/upo/{session}/                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Principles

### 1. Code Before Prompts (Axiom #4)
UPO minimizes AI unpredictability by using deterministic Python code for:
- Weightage loading and calculation
- Parallel execution orchestration
- Skill discovery and routing
- Synthesis algorithm
- GOT artifact generation

### 2. Holistic by Default
Every prompt is analyzed through multiple life domains, ensuring recommendations consider work-life balance, not just the immediate task.

### 3. Transparent Decision Making
All routing decisions are logged in GOT artifacts, providing full audit trails for debugging and improvement.

### 4. Continuous Learning
Agent weights are calibrated based on actual performance, ensuring the system improves over time.

## Summary

The Universal Prompt Orchestrator transforms Claude Boost from a simple skill executor into an intelligent, self-improving system that:

- **Analyzes** every prompt through 12 domain perspectives
- **Selects** 4-12 relevant agents based on keywords and dependencies
- **Executes** agents in parallel for maximum efficiency
- **Synthesizes** weighted outputs for balanced recommendations
- **Validates** quality through a 6-agent Round Table Council
- **Learns** from every execution to improve future routing

This architecture ensures that users receive holistic, well-considered responses that account for all aspects of their professional and personal lives.
