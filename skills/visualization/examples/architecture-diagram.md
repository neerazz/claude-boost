# Example: Architecture Diagram

## Table of Contents
- [Request](#request)
- [Classification](#classification)
- [Generated Mermaid](#generated-mermaid)
- [Rendering Commands](#rendering-commands)
- [Output](#output)



## Request

"Create a diagram showing the complete Claude Boost user flow from request to execution"

## Classification

| Pattern Found | Route |
|---------------|-------|
| "diagram" | MERMAID |
| "flow" | MERMAID |
| "architecture" | MERMAID |

**Decision: MERMAID** (code-based, deterministic)

## Generated Mermaid

### Complete User Flow Diagram

```mermaid
flowchart TB
    subgraph USER["User Request"]
        U1[/"User: 'Run daily planning'"/]
    end

    subgraph ROUTER["Skill Router"]
        R1{Match skill name?}
        R2[Load SKILL.md]
        R3[Parse instructions]
    end

    subgraph L3["Layer 3: Meta Orchestrators"]
        direction TB
        JOR["journal-orchestrator"]
        CRT["dynamic-roundtable"]
        RTO["dynamic-roundtable"]
        PB["personal-branding"]
    end

    subgraph L2["Layer 2: Composite Skills"]
        direction TB
        SI["slack-intelligence"]
        AWS["aws-infrastructure"]
        NMI["notion-meeting"]
        GWI["github-work"]
        HLT["holistic-life-tracker"]
        DR["dynamic-roundtable"]
    end

    subgraph L1["Layer 1: Atomic Skills"]
        direction TB
        subgraph FETCH["Fetchers"]
            SF["slack-fetch"]
            AF["aws-fetch"]
            NF["notion-fetch"]
            GF["github-fetch"]
        end
        subgraph ANALYZE["Analyzers"]
            SA["slack-analyze"]
            AA["aws-analyze"]
        end
        subgraph EXECUTE["Executors"]
            TC["task-create"]
            PC["page-create"]
        end
    end

    subgraph L0["Layer 0: External APIs"]
        SLACK[(Slack API)]
        NOTION[(Notion API)]
        GITHUB[(GitHub API)]
        AWSAPI[(AWS API)]
    end

    subgraph QA["Quality Gate"]
        Q1{Phase 9.5\nValidation}
        Q2["Aggregate\nquality_metrics"]
        Q3{Score >= 90%?}
    end

    subgraph OUTPUT["Final Output"]
        O1["Daily Plan Page"]
        O2["Created Tasks"]
        O3["Audit Trail"]
    end

    U1 --> R1
    R1 -->|Yes| R2
    R2 --> R3
    R3 --> DOP

    DOP -->|Parallel| SI
    DOP -->|Parallel| AWS
    DOP -->|Parallel| NMI
    DOP -->|Parallel| GWI
    DOP -->|Parallel| HLT

    SI --> SF
    SI --> SA
    AWS --> AF
    AWS --> AA
    NMI --> NF
    GWI --> GF

    SF --> SLACK
    NF --> NOTION
    GF --> GITHUB
    AF --> AWSAPI

    SI -->|quality_metrics| Q1
    AWS -->|quality_metrics| Q1
    NMI -->|quality_metrics| Q1
    GWI -->|quality_metrics| Q1

    Q1 --> Q2
    Q2 --> Q3
    Q3 -->|Yes| TC
    Q3 -->|No, retry| DOP

    TC --> PC
    PC --> O1
    PC --> O2
    PC --> O3

    style L3 fill:#E1BEE7,stroke:#7B1FA2
    style L2 fill:#BBDEFB,stroke:#1976D2
    style L1 fill:#C8E6C9,stroke:#388E3C
    style L0 fill:#CFD8DC,stroke:#546E7A
    style QA fill:#FFF9C4,stroke:#FBC02D
    style OUTPUT fill:#DCEDC8,stroke:#689F38
```

### Simplified 3-Layer Architecture

```mermaid
flowchart TD
    subgraph L3["Layer 3: Meta Orchestrators"]
        L3A["Coordinate multiple L2 skills"]
        L3B["Produce final output"]
        L3C["Enforce quality gates"]
    end

    subgraph L2["Layer 2: Composite Skills"]
        L2A["Coordinate 2-3 L1 skills"]
        L2B["Return quality_metrics"]
        L2C["Domain isolation"]
    end

    subgraph L1["Layer 1: Atomic Skills"]
        L1A["Single responsibility"]
        L1B["Fetch / Analyze / Execute"]
        L1C["Pure functions"]
    end

    subgraph L0["Layer 0: External"]
        L0A["MCP Servers"]
        L0B["APIs"]
        L0C["Databases"]
    end

    L3 -->|"calls"| L2
    L2 -->|"calls"| L1
    L1 -->|"calls"| L0

    L3 -.->|"NEVER direct"| L1

    style L3 fill:#E1BEE7,stroke:#7B1FA2
    style L2 fill:#BBDEFB,stroke:#1976D2
    style L1 fill:#C8E6C9,stroke:#388E3C
    style L0 fill:#CFD8DC,stroke:#546E7A
```

### Visualization Routing Flow

```mermaid
flowchart TD
    START[/"Visualization Request"/]

    ANALYZE["Analyze Request"]

    CHECK1{Contains diagram\npatterns?}
    CHECK2{Contains data\npatterns?}
    CHECK3{Contains artistic\npatterns?}

    MERMAID["Route: MERMAID\n(Code-based)"]
    PYTHON["Route: PYTHON\n(Code-based)"]
    GEMINI["Route: GEMINI\n(AI-based)"]

    GEN_MERMAID["Generate Mermaid Code"]
    GEN_PYTHON["Generate Python Script"]
    GEN_PROMPT["Generate Detailed Prompt"]

    RENDER_MM["Render to SVG/PNG"]
    EXEC_PY["Execute matplotlib/plotly"]
    CALL_GEMINI["Call gemini-image-gen"]

    OUTPUT[/"Output File + Metrics"/]

    START --> ANALYZE
    ANALYZE --> CHECK1

    CHECK1 -->|Yes| MERMAID
    CHECK1 -->|No| CHECK2

    CHECK2 -->|Yes| PYTHON
    CHECK2 -->|No| CHECK3

    CHECK3 -->|Yes| GEMINI
    CHECK3 -->|No| MERMAID

    MERMAID --> GEN_MERMAID
    PYTHON --> GEN_PYTHON
    GEMINI --> GEN_PROMPT

    GEN_MERMAID --> RENDER_MM
    GEN_PYTHON --> EXEC_PY
    GEN_PROMPT --> CALL_GEMINI

    RENDER_MM --> OUTPUT
    EXEC_PY --> OUTPUT
    CALL_GEMINI --> OUTPUT

    style MERMAID fill:#C8E6C9,stroke:#388E3C
    style PYTHON fill:#C8E6C9,stroke:#388E3C
    style GEMINI fill:#FFE0B2,stroke:#F57C00
    style OUTPUT fill:#E3F2FD,stroke:#1976D2
```

## Rendering Commands

### Save as SVG (recommended for diagrams)
```bash
# Install mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Convert to SVG
mmdc -i user-flow.mmd -o user-flow.svg

# Convert to PNG with transparent background
mmdc -i user-flow.mmd -o user-flow.png -b transparent -s 2
```

### Embed in Markdown

The Mermaid code above can be directly embedded in:
- GitHub README files
- Notion pages (using code blocks)
- GitLab wikis
- Obsidian notes

## Output

```json
{
  "visualization_type": "MERMAID",
  "output": {
    "format": "mermaid_code",
    "rendered_formats": ["svg", "png"],
    "file_path": "user-flow.svg"
  },
  "quality_metrics": {
    "route_confidence": 0.98,
    "tool_used": "mermaid",
    "generation_method": "code",
    "deterministic": true,
    "complexity": "high",
    "nodes": 45,
    "edges": 38
  },
  "reasoning": "Request contains 'diagram', 'flow', 'architecture' patterns - routed to Mermaid for code-based generation"
}
```
