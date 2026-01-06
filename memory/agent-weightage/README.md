# Agent Weightage Memory

> **Purpose**: Track multi-agent voting weights and calibration.

## Overview

When multiple agents vote on decisions (roundtable pattern), their weights are calibrated based on historical accuracy.

## Schema

```json
{
  "agents": {
    "critic": {"weight": 1.2, "accuracy": 0.85},
    "researcher": {"weight": 1.0, "accuracy": 0.78},
    "implementer": {"weight": 0.9, "accuracy": 0.72}
  },
  "last_calibrated": "2025-01-05"
}
```

## Usage

The `roundtable-council` skill uses these weights for weighted voting decisions.
