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

## The Multi-Agent Architecture

UPO employs multiple specialized domain agents, each bringing a unique perspective to every prompt. This ensures no critical aspect is overlooked. The number and type of agents are fully customizable.

### Example Agent Categories

| Category | Example Agents | Purpose |
|----------|----------------|---------|
| **Professional** | Career, Technical, Leadership | Work-related decisions |
| **Personal** | Family, Health, Relationships | Life balance |
| **Financial** | Budget, Investments, Planning | Money matters |
| **Growth** | Learning, Goals, Skills | Self-improvement |
| **Wellbeing** | Health, Recreation, Stress | Quality of life |

### Configurable Agent System

```
┌────────────────────────────────────────────────────────────────────────┐
│                     DOMAIN AGENTS (Customizable)                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PROFESSIONAL                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Career &        │  │ Technical       │  │ Leadership &    │        │
│  │ Growth          │  │ Excellence      │  │ Influence       │        │
│  │                 │  │                 │  │                 │        │
│  │ - Promotions    │  │ - Code quality  │  │ - Team mgmt     │        │
│  │ - Networking    │  │ - Architecture  │  │ - Strategy      │        │
│  │ - Reputation    │  │ - Performance   │  │ - Mentoring     │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  PERSONAL & WELLBEING                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Family &        │  │ Health &        │  │ Financial       │        │
│  │ Relationships   │  │ Energy          │  │                 │        │
│  │                 │  │                 │  │                 │        │
│  │ - Work-life     │  │ - Physical      │  │ - Budget        │        │
│  │ - Balance       │  │ - Mental        │  │ - Investments   │        │
│  │ - Priorities    │  │ - Sleep         │  │ - Planning      │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  GROWTH & DISCOVERY                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Learning &      │  │ Goals &         │  │ Skills          │        │
│  │ Growth          │  │ Priorities      │  │ Discovery       │        │
│  │                 │  │                 │  │                 │        │
│  │ - Courses       │  │ - OKRs          │  │ - Skill match   │        │
│  │ - Certifications│  │ - Milestones    │  │ - Tool routing  │        │
│  │ - Reading       │  │ - Alignment     │  │ - Automation    │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ Emotional       │  │ Fun &           │  │ Contribution &  │        │
│  │ Intelligence    │  │ Recreation      │  │ Legacy          │        │
│  │                 │  │                 │  │                 │        │
│  │ - Communication │  │ - Hobbies       │  │ - Mentoring     │        │
│  │ - Empathy       │  │ - Travel        │  │ - Community     │        │
│  │ - Relationships │  │ - Entertainment │  │ - Open source   │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

## Execution Phases

UPO processes every prompt through distinct phases, ensuring thorough analysis and quality output.

### Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UPO EXECUTION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────┘

Phase 0             Phase 1           Phase 2            Phase 3
┌──────────┐       ┌──────────┐      ┌──────────┐       ┌──────────┐
│  INIT &  │──────▶│  AGENT   │─────▶│ PARALLEL │──────▶│SYNTHESIS │
│ CONTEXT  │       │ SELECTION│      │EXECUTION │       │  ENGINE  │
└──────────┘       └──────────┘      └──────────┘       └──────────┘
     │                  │                 │                  │
     │ Load config     │ Keywords +      │ 4-12 Agents     │ Weighted
     │ User context    │ Dependencies    │ Concurrent      │ Aggregation
     ▼                  ▼                 ▼                  ▼

Phase 4            Phase 5           Phase 6
┌──────────┐      ┌──────────┐      ┌──────────┐
│  ROUND   │─────▶│   GOT    │─────▶│  MEMORY  │
│  TABLE   │      │ARTIFACTS │      │  UPDATE  │
└──────────┘      └──────────┘      └──────────┘
     │                 │                  │
     │ Council        │ Audit trail     │ Weight
     │ Agents         │ Evidence        │ Calibration
     ▼                 ▼                  ▼
```

### Phase 0: Initialization & Context Loading

**Purpose**: Load system configuration and user context for personalized routing.

```python
# Pseudocode
def initialize():
    # Load agent weightage configuration
    config = load_config("agent-weightage.json")

    # Load user context (with caching)
    context = load_user_context()

    # Load skill dependency graph
    skill_dag = load_dag("skill_dag.json")

    return config, context, skill_dag
```

### Phase 1: Intelligent Agent Selection

**Purpose**: Select 4-12 relevant agents based on prompt analysis.

```
┌────────────────────────────────────────────────────────────────────────┐
│                     AGENT SELECTION ALGORITHM                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. MANDATORY AGENTS (Always Included)                                 │
│     ┌─────────────────┐  ┌─────────────────┐                          │
│     │ Goals &         │  │ Skills Discovery│                          │
│     │ Priorities      │  │                 │                          │
│     └─────────────────┘  └─────────────────┘                          │
│                                                                         │
│  2. KEYWORD MATCHING                                                   │
│     Prompt: "Help me optimize my database queries"                     │
│     ┌─────────────┐                                                    │
│     │  Keywords   │──▶ "optimize" ──▶ Technical Agent                 │
│     │  Extracted  │──▶ "database" ──▶ Technical Agent                 │
│     │             │──▶ "queries" ──▶ Technical Agent                  │
│     └─────────────┘                                                    │
│                                                                         │
│  3. CHAIN DEPENDENCIES                                                 │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│     │  Technical  │────▶│   Career    │────▶│  Learning   │          │
│     └─────────────┘     └─────────────┘     └─────────────┘          │
│                                                                         │
│  4. MINIMUM THRESHOLD: 4 agents                                        │
│                                                                         │
│  5. DOUBT = INCLUDE (if >30% relevance possible, add agent)           │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

**Keyword → Agent Mapping Examples**:

| Agent | Trigger Keywords |
|-------|------------------|
| Career & Growth | `career`, `promotion`, `leadership`, `manager`, `job`, `interview` |
| Technical Excellence | `code`, `technical`, `database`, `api`, `performance`, `architecture` |
| Financial | `money`, `invest`, `budget`, `salary`, `savings`, `retirement` |
| Health & Energy | `health`, `exercise`, `sleep`, `stress`, `fitness`, `gym` |
| Learning & Growth | `learn`, `course`, `certification`, `study`, `skill`, `training` |
| Fun & Recreation | `travel`, `vacation`, `trip`, `fun`, `hobby`, `entertainment` |

### Phase 2: Parallel Agent Execution

**Purpose**: Run selected agents concurrently for diverse perspectives.

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PARALLEL AGENT EXECUTION                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Promise.all([                                                         │
│    agent_technical(prompt, context),     ──┐                           │
│    agent_career(prompt, context),          │                           │
│    agent_learning(prompt, context),        ├── Concurrent              │
│    agent_goals(prompt, context),           │   Execution               │
│    agent_skills(prompt, context)         ──┘                           │
│  ])                                                                     │
│                                                                         │
│  Each agent returns:                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  {                                                               │  │
│  │    "agent_id": "technical",                                      │  │
│  │    "status": "success",                                          │  │
│  │    "relevance_score": 0.95,        // 0-1 self-assessed         │  │
│  │    "insights": [...],               // Key observations          │  │
│  │    "concerns": [...],               // Potential issues          │  │
│  │    "recommendations": [...],        // Action items              │  │
│  │    "suggested_skills": [            // Skills to invoke          │  │
│  │      "code-review",                                              │  │
│  │      "performance-analyzer"                                      │  │
│  │    ],                                                            │  │
│  │    "execution_time_ms": 1250                                     │  │
│  │  }                                                               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Synthesis Engine

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
│     │  Technical Agent: 0.20 (base) × 0.95 (relevance) = 0.19      │   │
│     │  Career Agent: 0.15 × 0.80 = 0.12                            │   │
│     │  Goals Agent: 0.10 × 0.90 = 0.09                             │   │
│     └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  2. Normalize to 100%                                                  │
│     ┌─────────────────────────────────────────────────────────────┐   │
│     │  total = sum(all_effective_weights)                          │   │
│     │  final_weight = effective_weight / total                     │   │
│     │                                                               │   │
│     │  Technical: 0.19 / 0.40 = 0.475 (47.5%)                      │   │
│     │  Career: 0.12 / 0.40 = 0.30 (30%)                            │   │
│     │  Goals: 0.09 / 0.40 = 0.225 (22.5%)                          │   │
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
│     │  1. code-review: 0.85 (Technical + Career)                   │   │
│     │  2. performance-analyzer: 0.72 (Technical)                   │   │
│     │  3. deep-research: 0.45 (Learning)                           │   │
│     └─────────────────────────────────────────────────────────────┘   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 4: Round Table Council

**Purpose**: Quality deliberation through specialized council agents.

```
┌────────────────────────────────────────────────────────────────────────┐
│                       ROUND TABLE COUNCIL                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  COUNCIL AGENTS (run in deliberation rounds)                           │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │    RESEARCH     │  │    CRITIQUE     │  │   CONSENSUS     │        │
│  │     AGENT       │  │     AGENT       │  │     AGENT       │        │
│  │                 │  │                 │  │                 │        │
│  │ Find trending   │  │ Challenge       │  │ Build agreement │        │
│  │ approaches      │  │ assumptions     │  │ from divergent  │        │
│  │                 │  │                 │  │ views           │        │
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
│  │  for round in range(1, max_rounds + 1):                          │  │
│  │    results = await parallel([all_council_agents])                │  │
│  │    quality_score = self_correction_agent.score                  │  │
│  │    if quality_score >= quality_threshold:                       │  │
│  │      break  # Quality threshold met                             │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 5: GOT Artifacts Generation

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
    {"id": "technical", "type": "perspective", "weight": 0.475},
    {"id": "career", "type": "perspective", "weight": 0.30},
    {"id": "code-review", "type": "skill", "score": 0.85}
  ],
  "edges": [
    {"from": "technical", "to": "code-review", "weight": 0.85},
    {"from": "career", "to": "code-review", "weight": 0.72}
  ],
  "synthesis_score": 0.96,
  "timestamp": "2026-01-09T12:34:56Z"
}
```

### Phase 6: Memory Update (Async)

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

### Example 1: Technical Task

**Prompt**: "Help me optimize my database queries for better performance"

```
┌────────────────────────────────────────────────────────────────────────┐
│                    AGENT SELECTION BREAKDOWN                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Keyword Matches:                                                       │
│    "optimize" ──▶ Technical Agent                                      │
│    "database" ──▶ Technical Agent                                      │
│    "performance" ──▶ Technical Agent                                   │
│                                                                         │
│  Chain Dependencies:                                                   │
│    Technical ──▶ Career (skill development)                            │
│    Technical ──▶ Learning (knowledge gaps)                             │
│                                                                         │
│  Mandatory Agents:                                                     │
│    Goals & Priorities                                                  │
│    Skills Discovery                                                    │
│                                                                         │
│  FINAL SELECTION (5 agents):                                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Agent              │ Relevance │ Effective Weight              │  │
│  ├─────────────────────┼───────────┼──────────────────────────────│  │
│  │  Technical          │    95%    │      40%                     │  │
│  │  Career             │    70%    │      20%                     │  │
│  │  Learning           │    65%    │      15%                     │  │
│  │  Goals              │    80%    │      15%                     │  │
│  │  Skills Discovery   │   100%    │      10%                     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  RECOMMENDED SKILL CHAIN:                                              │
│    1. code-review (analyze current queries)                            │
│    2. performance-analyzer (identify bottlenecks)                      │
│    3. deep-research (best practices)                                   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Example 2: Life Balance Task

**Prompt**: "Plan a 2-week vacation to Europe with my family"

```
┌────────────────────────────────────────────────────────────────────────┐
│                    AGENT SELECTION BREAKDOWN                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Keyword Matches:                                                       │
│    "vacation" ──▶ Recreation Agent                                     │
│    "Europe" ──▶ Recreation Agent                                       │
│    "family" ──▶ Family & Relationships Agent                           │
│                                                                         │
│  Chain Dependencies:                                                   │
│    Travel ──▶ Financial (budget planning)                              │
│    Travel ──▶ Health (travel wellness)                                 │
│                                                                         │
│  Mandatory Agents:                                                     │
│    Goals & Priorities                                                  │
│    Skills Discovery                                                    │
│                                                                         │
│  FINAL SELECTION (6 agents):                                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Agent              │ Relevance │ Effective Weight              │  │
│  ├─────────────────────┼───────────┼──────────────────────────────│  │
│  │  Recreation         │   100%    │      35%                     │  │
│  │  Family             │    90%    │      25%                     │  │
│  │  Financial          │    75%    │      15%                     │  │
│  │  Health             │    60%    │      10%                     │  │
│  │  Goals              │    50%    │       8%                     │  │
│  │  Skills Discovery   │   100%    │       7%                     │  │
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
| Agents Responded | ≥80% | Retry failed agents |
| Synthesis Score | ≥95% | Additional council rounds |
| Skill Match Accuracy | ≥80% | Manual review |
| GOT Artifacts | All generated | Block completion |
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
│       │                          │  Periodic        │                  │
│       │                          │  Recalibration   │                  │
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
│  │ L2/L3 Skills    │  │ Self-Learning   │  │ Audit Trail     │         │
│  │ (execution)     │  │ (calibration)   │  │ (compliance)    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  DATA FLOW:                                                             │
│  config/agent-weightage/ ◀────▶ UPO ◀────▶ data/dag/skill_dag.json    │
│                                   │                                      │
│                                   ▼                                      │
│                          data/audit/upo/{session}/                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Principles

### 1. Code Before Prompts
UPO minimizes AI unpredictability by using deterministic code for:
- Weightage loading and calculation
- Parallel execution orchestration
- Skill discovery and routing
- Synthesis algorithm
- Artifact generation

### 2. Holistic by Default
Every prompt is analyzed through multiple life domains, ensuring recommendations consider work-life balance, not just the immediate task.

### 3. Transparent Decision Making
All routing decisions are logged in GOT artifacts, providing full audit trails for debugging and improvement.

### 4. Continuous Learning
Agent weights are calibrated based on actual performance, ensuring the system improves over time.

## Summary

The Universal Prompt Orchestrator transforms Claude Boost from a simple skill executor into an intelligent, self-improving system that:

- **Analyzes** every prompt through multiple domain perspectives
- **Selects** 4-12 relevant agents based on keywords and dependencies
- **Executes** agents in parallel for maximum efficiency
- **Synthesizes** weighted outputs for balanced recommendations
- **Validates** quality through a Round Table Council
- **Learns** from every execution to improve future routing

This architecture ensures that users receive holistic, well-considered responses that account for multiple aspects of their professional and personal lives.
