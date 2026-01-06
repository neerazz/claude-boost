# Graph of Thoughts (GoT) Memory

> **Purpose**: Persistent state for hypothesis-driven research sessions.

## Overview

Stores GoT execution state including:
- Active hypotheses
- Evidence gathered
- Validation status
- Research progress

## Schema

```json
{
  "session_id": "uuid",
  "hypotheses": [
    {
      "id": "H1",
      "statement": "...",
      "confidence": 0.75,
      "evidence": ["E1", "E2"],
      "status": "validated"
    }
  ],
  "evidence": {
    "E1": {"source": "...", "quality": "A"}
  }
}
```

## Integration

Used by `got-core` and `deep-research` skills for multi-session research continuity.
