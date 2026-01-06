# Example: User Flow Diagram

## Table of Contents
- [Request](#request)
- [Classification](#classification)
- [Generated Mermaid](#generated-mermaid)
- [Rendering](#rendering)
- [Output](#output)



## Request

"Create a user journey diagram showing how a developer uses Claude Boost daily"

## Classification

| Pattern Found | Route |
|---------------|-------|
| "user journey" | MERMAID |
| "diagram" | MERMAID |
| "flow" | MERMAID |

**Decision: MERMAID** (code-based, deterministic)

## Generated Mermaid

### Daily Developer Journey

```mermaid
journey
    title A Developer's Day with Claude Boost
    section Morning Setup
        Open terminal: 5: Developer
        Run journal-orchestrator: 5: Claude
        Review prioritized tasks: 4: Developer
        Check Slack intelligence: 4: Claude
    section Deep Work
        Pick P1 task from plan: 5: Developer
        Use deep-reasoning for design: 5: Claude
        Implement solution: 4: Developer
        Run principal-ic-critique: 4: Claude
    section Collaboration
        Check meeting intelligence: 4: Claude
        Prepare for standups: 4: Developer
        Share progress on Slack: 3: Developer
    section End of Day
        Run weekly-progress check: 4: Claude
        Update tasks in Notion: 4: Developer
        Plan tomorrow: 5: Claude
```

### Detailed Request-Response Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as Developer
    participant CC as Claude Code
    participant SR as Skill Router
    participant L3 as Layer 3
    participant L2 as Layer 2
    participant L1 as Layer 1
    participant API as External APIs

    U->>CC: "Run daily planning"
    CC->>SR: Match skill name
    SR->>SR: Find journal-orchestrator
    SR->>L3: Load & execute skill

    rect rgb(225, 190, 231)
        Note over L3: Layer 3 Orchestration
        L3->>L2: Call slack-intelligence
        L3->>L2: Call aws-infrastructure
        L3->>L2: Call notion-meeting
        L3->>L2: Call github-work
    end

    par Parallel Execution
        rect rgb(187, 222, 251)
            Note over L2,API: slack-intelligence
            L2->>L1: slack-fetch
            L1->>API: Slack API call
            API-->>L1: Messages
            L2->>L1: slack-analyze
            L1-->>L2: Priorities + metrics
        end
    and
        rect rgb(187, 222, 251)
            Note over L2,API: aws-infrastructure
            L2->>L1: aws-fetch
            L1->>API: AWS API call
            API-->>L1: Resources
            L2->>L1: aws-analyze
            L1-->>L2: Health + metrics
        end
    end

    L2-->>L3: quality_metrics

    rect rgb(255, 249, 196)
        Note over L3: Phase 9.5 Quality Gate
        L3->>L3: Validate all metrics
        L3->>L3: Check thresholds
    end

    alt Score >= 90%
        L3->>L1: task-create
        L1->>API: Create Notion tasks
        L3->>L1: page-create
        L1->>API: Create daily plan
        L1-->>L3: Page URL
        L3-->>CC: Success + URL
        CC-->>U: "Daily plan ready!"
    else Score < 90%
        L3->>L3: Identify gaps
        L3->>L2: Retry failed sources
        L2-->>L3: Updated metrics
    end
```

### State Machine: Skill Execution

```mermaid
stateDiagram-v2
    [*] --> Pending: User request

    Pending --> Routing: Skill matched
    Routing --> L3_Executing: Route to L3
    Routing --> L2_Executing: Route to L2
    Routing --> L1_Executing: Route to L1

    state L3_Executing {
        [*] --> Coordinating
        Coordinating --> L2_Calls: Invoke L2 skills
        L2_Calls --> Aggregating: Collect results
        Aggregating --> QualityGate: Run Phase 9.5
        QualityGate --> [*]: Pass
        QualityGate --> Coordinating: Fail (retry)
    }

    state L2_Executing {
        [*] --> L2_Coord
        L2_Coord --> L1_Calls: Invoke L1 skills
        L1_Calls --> Merging: Merge outputs
        Merging --> [*]: Return quality_metrics
    }

    state L1_Executing {
        [*] --> Running
        Running --> [*]: Return result
    }

    L3_Executing --> Completed: Output ready
    L2_Executing --> Completed: Output ready
    L1_Executing --> Completed: Output ready

    Completed --> [*]: Return to user

    note right of QualityGate
        Score must be >= 90%
        Otherwise retry from L2
    end note
```

### User Decision Tree

```mermaid
flowchart TD
    START([Developer needs visualization])

    Q1{What type of\nvisualization?}

    subgraph DIAGRAM["Diagram Type"]
        D1{Showing a\nprocess?}
        D2{Showing\ninteractions?}
        D3{Showing\nstates?}
        D4{Showing\nrelationships?}

        D1 -->|Yes| FLOW[Flowchart]
        D2 -->|Yes| SEQ[Sequence Diagram]
        D3 -->|Yes| STATE[State Diagram]
        D4 -->|Yes| ER[ER/Class Diagram]
    end

    subgraph DATA["Data Type"]
        DA1{Comparing\nvalues?}
        DA2{Showing\ntrends?}
        DA3{Showing\nproportions?}
        DA4{Showing\ncorrelations?}

        DA1 -->|Yes| BAR[Bar Chart]
        DA2 -->|Yes| LINE[Line Chart]
        DA3 -->|Yes| PIE[Pie Chart]
        DA4 -->|Yes| SCATTER[Scatter Plot]
    end

    subgraph CREATIVE["Creative Type"]
        C1[Artistic illustration]
        C2[Photorealistic image]
        C3[Abstract concept]
    end

    Q1 -->|Structure/Flow| DIAGRAM
    Q1 -->|Numbers/Data| DATA
    Q1 -->|Artistic/Creative| CREATIVE

    FLOW --> MM[Use Mermaid]
    SEQ --> MM
    STATE --> MM
    ER --> MM

    BAR --> PY[Use Python]
    LINE --> PY
    PIE --> PY
    SCATTER --> PY

    C1 --> GEM[Use Gemini]
    C2 --> GEM
    C3 --> GEM

    MM --> OUTPUT1[/"Code output\n(deterministic)"/]
    PY --> OUTPUT2[/"Code output\n(deterministic)"/]
    GEM --> OUTPUT3[/"AI output\n(creative)"/]

    style MM fill:#C8E6C9,stroke:#388E3C
    style PY fill:#C8E6C9,stroke:#388E3C
    style GEM fill:#FFE0B2,stroke:#F57C00
```

### Timeline: Project Development

```mermaid
timeline
    title Claude Boost Development Timeline

    section Foundation
        2024-01 : Project inception
                : Core architecture design
        2024-02 : Layer 1 atomic skills
                : MCP server framework

    section Growth
        2024-03 : Layer 2 composite skills
                : Quality metrics system
        2024-04 : Layer 3 orchestrators
                : Phase 9.5 gate

    section Maturity
        2024-05 : 50+ skills deployed
                : Production hardening
        2024-06 : Visualization skill
                : Community expansion
```

## Rendering

### Embed in Documentation

All diagrams above can be embedded directly in:
- GitHub README.md
- Notion pages (code block)
- GitLab wikis
- Obsidian notes

### Export to Images

```bash
# Install mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Export all diagrams
mmdc -i journey.mmd -o journey.png -s 2
mmdc -i sequence.mmd -o sequence.svg
mmdc -i state.mmd -o state.svg
mmdc -i decision.mmd -o decision.png -s 2
```

## Output

```json
{
  "visualization_type": "MERMAID",
  "output": {
    "diagrams": [
      {"type": "journey", "purpose": "User journey map"},
      {"type": "sequenceDiagram", "purpose": "Request-response flow"},
      {"type": "stateDiagram-v2", "purpose": "Execution states"},
      {"type": "flowchart", "purpose": "Decision tree"},
      {"type": "timeline", "purpose": "Project timeline"}
    ],
    "format": "mermaid_code"
  },
  "quality_metrics": {
    "route_confidence": 0.97,
    "tool_used": "mermaid",
    "generation_method": "code",
    "deterministic": true,
    "diagrams_generated": 5
  },
  "reasoning": "Request contains 'user journey' and 'diagram' patterns - routed to Mermaid"
}
```
