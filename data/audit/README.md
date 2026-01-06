# Audit Trail

Execution audit logs for debugging and quality tracking.

## Schema

```json
{
  "timestamp": "2025-01-05T10:30:00Z",
  "skill": "skill-name",
  "input_hash": "abc123",
  "output_hash": "def456",
  "quality_score": 92,
  "duration_ms": 1500,
  "gates_passed": ["clear-thinking", "self-critique"]
}
```

## Retention

- Keep 30 days of audit logs
- Aggregate to weekly summaries after 7 days

## Usage

Used by `self-improvement-loop` to identify patterns and improvement opportunities.
