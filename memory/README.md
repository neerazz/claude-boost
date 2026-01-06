# Memory System

Persistent storage for agent learning and state across sessions.

## Purpose

The memory system enables:
- **Session continuity**: State persists across conversations
- **Learning**: Track patterns, improvements, ratings over time
- **Context**: Build up domain knowledge incrementally

## Directory Structure

```
memory/
├── README.md           # This file
├── self-learn/         # Self-improvement tracking
├── got-core/           # Graph of Thoughts state
└── agent-weightage/    # Agent voting weights
```

## Subdirectories

### self-learn/
Tracks skill ratings, improvement proposals, and learning trends.

### got-core/
Graph of Thoughts execution state and hypothesis tracking.

### agent-weightage/
Multi-agent voting weights and calibration data.

## Usage Pattern

Skills write to memory using standard JSON schema:
```python
# Write to memory
with open(f"memory/self-learn/{date}.json", "w") as f:
    json.dump(session_data, f)

# Read from memory
with open(f"memory/self-learn/{date}.json") as f:
    history = json.load(f)
```

## Retention Policy

- Daily snapshots: Keep 30 days
- Weekly aggregates: Keep 12 weeks
- Monthly summaries: Keep indefinitely
