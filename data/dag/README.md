# DAG (Directed Acyclic Graph) Data

Skill routing and dependency management.

## Files

### skill_dag.json
```json
{
  "nodes": {
    "skill-name": {
      "layer": "L1",
      "dependencies": [],
      "triggers": ["keyword1", "keyword2"]
    }
  },
  "edges": [
    {"from": "skill-a", "to": "skill-b", "type": "depends"}
  ]
}
```

### keyword_skill_mapping.json
```json
{
  "research": ["deep-research", "evidence-gatherer"],
  "analyze": ["gap-analyzer", "clear-thinking-gate"],
  "visualize": ["visualization"]
}
```

## Usage

The Universal Prompt Orchestrator (UPO) uses these files to route prompts to appropriate skills.

## Generation

Run `python3 tools/skill_architect.py dag-sync` to regenerate DAG from skill definitions.
