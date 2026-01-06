# Data Directory

Runtime data, caches, and operational logs.

## Structure

```
data/
├── audit/        # Execution audit trails
├── cache/        # Skill checksums, session state
├── dag/          # Skill dependency graphs
├── learning/     # Learning aggregator data
└── operational/  # Operational logs and metrics
```

## Subdirectories

### audit/
Execution audit trails for skills and commands. Used for debugging and quality tracking.

### cache/
Runtime caches including:
- Skill checksums (detect changes)
- Session locks
- Post-hook state

### dag/
Directed Acyclic Graph data for skill routing:
- `skill_dag.json` - Skill dependency graph
- `keyword_skill_mapping.json` - Keyword to skill routing

### learning/
Data from learning aggregator skill:
- Source catalogs
- Extracted insights
- Quality ratings

### operational/
Operational metrics and logs:
- Execution times
- Error rates
- Usage patterns

## Data Lifecycle

| Type | Retention | Purpose |
|------|-----------|---------|
| Cache | Session | Fast lookups |
| Audit | 30 days | Debugging |
| DAG | Permanent | Routing |
| Learning | Permanent | Knowledge |

## Gitignore

Most data files are gitignored (user-specific runtime data). Only schema/structure files are committed.
